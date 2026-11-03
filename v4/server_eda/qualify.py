"""Map the complete v4 accelerator at the specified optimization period, then qualify the same netlist in SS and FF.

Run inside a separate copy under the authorised server home. Reuses the v2
tool launcher and library configuration, but never uses a v2 mapped netlist.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = Path("/storage2/2026contest/server5/s5_10usr")
TOP = "kwt_nice_core"
BASE_AREA = 155089.240090
AREA_RATIO = 2.5  # explicit v4 engineering ceiling in the same library units


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_flow():
    assert ROOT == HOME / "v4"
    sys.dont_write_bytecode = True
    launcher = HOME / "v2/server_eda/easy.py"
    assert digest(launcher) == "1201ab478d82d6e69ed809993e275c7339839e2965acf8c068be5a0fac0aa846", "Review updated v2 tool launcher"
    spec = importlib.util.spec_from_file_location("kwt_tools", str(launcher))
    flow = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(flow)
    base_sources = flow.sources
    def sources(top):
        paths = base_sources(top)
        if top=="tb_kwt_compact":
            paths.append(ROOT/"tb/tb_kwt_system.sv")
        return paths
    flow.sources = sources
    flow.ROOT = ROOT
    flow.OUT = ROOT/"build/manual"
    return flow


def source_manifest():
    map_scripts = ["constraints.tcl","manual_sta.tcl","manual_synth.tcl","reset_repair.tcl","reset_repair_run.tcl","mapping_period.txt"]
    files = [ROOT/"rtl.f"] + sorted((ROOT/"rtl").glob("*.sv")) + [ROOT/"server_eda"/n for n in map_scripts]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in files}


def implementation_sources():
    paths = ("resize_plan.txt","resize.tcl","check_resize.py")
    return dict(source_manifest(), **{"server_eda/"+p:digest(ROOT/"server_eda"/p) for p in paths})


def measure_corner(flow, libs, net, directory, corner, period):
    env = {"KWT_ROOT":str(ROOT),"KWT_TOP":TOP,"KWT_CORNER":corner,"KWT_PERIOD":str(period),
           "KWT_OUTPUT_CAP":"0.002852","KWT_STD_DB":libs["standard"][corner],
           "KWT_SRAM_DBS":"|".join(libs["sram"][corner]),"KWT_NETLIST":str(net)}
    flow.run(["pt_shell","-f",ROOT/"server_eda/manual_sta.tcl"],directory,"pt","STA_COMPLETED "+TOP,env)
    macro_counts = dict(line.split() for line in (directory/"topology.txt").read_text().splitlines())
    assert macro_counts == {"RAMSP128X16":"35","RAMSP1024X16":"6"}
    paths = (directory/"metrics.txt").read_text().splitlines()
    slacks = [float(re.search(r"slack=([^ ]+)",line).group(1)) for line in paths]
    assert len(slacks)==2 and all(math.isfinite(n) for n in slacks)
    violations = [line.strip() for line in (directory/"violations.rpt").read_text().splitlines() if "VIOLATED" in line]
    ok = min(slacks)>=0 and not violations
    print("TIMING %s %s %.3f MHz setup=%+.6f ns hold=%+.6f ns violations=%d" %
          ("PASS" if ok else "FAIL",corner,1000.0/period,slacks[0],slacks[1],len(violations)),flush=True)
    return {"period_ns":period,"corner":corner,"setup_hold_ns":slacks,"paths":paths,
            "reported_violations":violations,"timing_pass":ok,"coverage":(directory/"coverage.rpt").read_text()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--periods", nargs="+", type=float, default=[5.0, 5.555556, 6.666667])
    parser.add_argument("--before-resize", action="store_true", help="inspect the original mapped implementation")
    args = parser.parse_args()
    assert all(math.isfinite(p) and p > 0 for p in args.periods)
    map_period = float((ROOT/"server_eda/mapping_period.txt").read_text().strip())
    assert math.isfinite(map_period) and map_period>0
    flow = load_flow()
    libs = flow.libs()
    sources = source_manifest()
    identity = hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()[:16]
    work = ROOT / "build/ppa" / identity
    mapped = work / "repaired"
    net = mapped / "mapped.v"
    stamp = mapped / "source_and_netlist.json"
    env = {"KWT_ROOT":str(ROOT),"KWT_RTL_ROOT":str(ROOT),"KWT_TOP":TOP,
           "KWT_PERIOD":str(map_period),"KWT_OUTPUT_CAP":"0.002852","KWT_HOLD_FIX":"1",
           "KWT_STD_DB":libs["standard"]["ss"],"KWT_MIN_STD_DB":libs["standard"]["ff"],
           "KWT_SRAM_DBS":"|".join(libs["sram"]["ss"]),
           "KWT_MIN_SRAM_DBS":"|".join(libs["sram"]["ff"])}
    if stamp.exists():
        recorded = json.loads(stamp.read_text())
        assert sources == recorded["sources"] and digest(net) == recorded["mapped_sha256"]
    else:
        print("MAP_START full core, SS target %.6f ns"%map_period, flush=True)
        raw = work / "raw"
        flow.run(["dc_shell","-f",ROOT/"server_eda/manual_synth.tcl"],raw,"dc","SYNTHESIS_COMPLETED "+TOP,env)
        env["KWT_DDC"] = str(raw/"mapped.ddc")
        flow.run(["dc_shell","-f",ROOT/"server_eda/reset_repair_run.tcl"],mapped,"dc","RESET_REPAIR_COMPLETE "+TOP,env)
        flow.save(stamp,{"sources":sources,"mapped_sha256":digest(net)})
        print("MAP_COMPLETE", flush=True)

    changes = []
    plan = ROOT/"server_eda/resize_plan.txt"
    have_plan = any(row.strip() and not row.lstrip().startswith("#") for row in plan.read_text().splitlines())
    if have_plan and not args.before_resize:
        from check_resize import audit
        script = ROOT/"server_eda/resize.tcl"
        eco_id = hashlib.sha256((digest(net)+digest(script)+digest(plan)).encode()).hexdigest()[:16]
        dest = work/("resize_" + eco_id)
        repair_env = dict(env,KWT_DDC=str(mapped/"mapped.ddc"),KWT_ECO_PLAN=str(plan))
        flow.run(["dc_shell","-f",script],dest,"dc","ECO_COMPLETE "+TOP,repair_env)
        changes = audit(net,dest/"mapped.v",plan)
        flow.save(dest/"resize_audit.json",{"original_sha256":digest(net),"final_sha256":digest(dest/"mapped.v"),
                                         "changes":changes,"remaining_statements_identical":True})
        mapped = work = dest
        net = dest/"mapped.v"
        print("STRUCTURAL AUDIT PASS, changed references="+str(len(changes)),flush=True)

    else:
        work = mapped
        flow.save(work/"resize_audit.json",{"original_sha256":digest(net),"final_sha256":digest(net),
                                           "changes":[],"remaining_statements_identical":True})
    area_text = (mapped/"area.rpt").read_text()
    area = float(re.search(r"Total cell area:\s*([\d.]+)",area_text).group(1))
    macro = float(re.search(r"Macro/Black Box area:\s*([\d.]+)",area_text).group(1))
    assert 0 < macro < area, "Unexpected macro or cell area"
    result = {"sources":implementation_sources(),"mapped_sha256":digest(net),"mapped_period_ns":map_period,"resize_changes":changes,
              "v31_reference_area":BASE_AREA,"v4_area":area,"macro_area":macro,
              "area_change_percent":100*(area/BASE_AREA-1),"proposed_area_limit":BASE_AREA*AREA_RATIO,
              "area_budget_met":area <= BASE_AREA*AREA_RATIO,"points":[]}
    print("AREA total=%.6f macro=%.6f delta=%+.3f%%"%(area,macro,result["area_change_percent"]),flush=True)
    for period in args.periods:
        for corner in ("ss","ff"):
            d = work / ("sta_%.6f_%s"%(period,corner))
            point = measure_corner(flow,libs,net,d,corner,period)
            result["points"].append(point)
            print("  "+point["paths"][0],flush=True)
        flow.save(work/"qualification.json",result)
    at_150=[p for p in result["points"] if abs(p["period_ns"]-6.666667)<1e-7]
    qualified=len(at_150)==2 and all(p["timing_pass"] for p in at_150) and result["area_budget_met"]
    print("150 MHz full-core pre-layout + proposed area gate: "+("PASS" if qualified else "NOT QUALIFIED"),flush=True)
    if qualified and not args.before_resize:
        from snapshot import install
        install(ROOT,work,"rebuilt",implementation_sources())
    return 0 if qualified else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("FLOW ERROR: "+str(error),file=sys.stderr)
        sys.exit(2)
