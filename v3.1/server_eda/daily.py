"""Version-root Make targets for the full v3.1 accelerator."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from qualify import ROOT, HOME, TOP, digest, load_flow, measure_corner, implementation_sources
from snapshot import validate

sys.path.insert(0,str(ROOT/"py"))
from assets import vectors

COUNTS = {"tb_kwt_arithmetic":260,"tb_v3_carries":7,"tb_kwt_icb":4,"tb_kwt_system":29,
          "tb_kwt_overlap":5,"tb_kwt_negative":58,"tb_kwt_mul_pipeline":524288}


def simulate(flow, top, vec, label, wave=False):
    result = flow.simulate(top,vec,label,wave)
    panel_ok = top!="tb_kwt_overlap" or "PANEL PASS 2/2" in Path(result["log"]).read_text()
    if not panel_ok or result["counts"] != [(str(COUNTS[top]),str(COUNTS[top]))]:
        (flow.OUT/"runs"/label/top/"verified.json").unlink()
        raise ValueError("Unexpected PASS count for "+top)
    return result


def implementation(flow, name):
    core = flow.selected_netlist(name)/"synth_kwt_nice_core"
    q = validate(core,implementation_sources())
    return core/"mapped.v",q


def timing(flow, name, period, require_pass=True):
    stamp = flow.OUT/("timing_"+name+"_"+str(period)+".json")
    if stamp.exists():
        stamp.unlink()
    net,q = implementation(flow,name)
    libs = flow.libs()
    records = []
    for corner in ("ss","ff"):
        d = flow.OUT/"timing"/name/str(period)/(TOP+"_"+corner)
        point = measure_corner(flow,libs,net,d,corner,period)
        point.update({"top":TOP,"passed":point["timing_pass"],"directory":str(d),
                      "slacks_ns":point["setup_hold_ns"],"sdf_sha256":digest(d/"mapped.sdf"),
                      "netlist_sha256":digest(net)})
        records.append(point)
    flow.save(stamp,records)
    print("METRIC area=%.6f macro=%.6f v3_delta=%+.3f%%" %
          (q["v31_area"],q["macro_area"],100*(q["v31_area"]/q["v3_reference_area"]-1)))
    passed=all(p["passed"] for p in records)
    if require_pass and not passed:
        raise ValueError("Timing failed; see "+str(stamp))
    return passed


def report(flow, name, period, vec):
    complete = True
    hashes = flow.source_hashes()
    for top,count in COUNTS.items():
        path = flow.OUT/"runs"/"default"/top/"verified.json"
        ok = False
        if path.exists():
            j = json.loads(path.read_text()); log = Path(j["log"])
            sig = flow.OUT/"compile"/top/"signature.json"
            ok = (j["passed"] and j["counts"]==[[str(count),str(count)]] and j["rtl_sha256"]==hashes and
                  Path(j["vector_dir"]).resolve()==vec.resolve() and log.exists() and digest(log)==j["log_sha256"]
                  and sig.exists() and json.loads(sig.read_text())==flow.signature(top)
                  and j["vectors_sha256"]=={p.name:digest(p) for p in vec.glob("*.hex")})
            if ok and j["matrix_cycles"]:
                cycles = [m["core_cycles"] for m in j["matrix_cycles"]]
                print("METRIC %s min=%d max=%d core cycles"%(top,min(cycles),max(cycles)))
        print("FUNCTION "+("PASS %s %d/%d"%(top,count,count) if ok else "INCOMPLETE/STALE "+top))
        complete = complete and ok
    net,q = implementation(flow,name)
    stamp = flow.OUT/("timing_"+name+"_"+str(period)+".json")
    records = json.loads(stamp.read_text()) if stamp.exists() else []
    corners = {p["corner"] for p in records}
    measured = len(records)==2 and corners=={"ss","ff"}
    for p in records:
        sdf = Path(p["directory"])/"mapped.sdf"
        ok = (p["passed"] and p["netlist_sha256"]==digest(net) and p["period_ns"]==period
              and sdf.exists() and digest(sdf)==p["sdf_sha256"])
        measured = measured and ok
        print("TIMING %s %s %.3f MHz setup=%+.6f ns hold=%+.6f ns" %
              ("PASS" if ok else "STALE/FAIL",p["corner"],1000/period,*p["slacks_ns"]))
    if not measured:
        print("TIMING INCOMPLETE/STALE: run make timing with the selected period and netlist")
    print("AREA %.6f library units; v3 delta %+.3f%%" %
          (q["v31_area"],100*(q["v31_area"]/q["v3_reference_area"]-1)))
    if not (complete and measured):
        raise ValueError("BASIC CHECK INCOMPLETE/FAIL")
    print("BASIC CHECK PASS (7 RTL suites and full accelerator SS/FF STA)")


def clean(flow):
    out = flow.OUT
    if not out.exists():
        print("CLEAN PASS; nothing to clean");return
    if out.is_symlink() or out.resolve()!=ROOT/"build/manual":
        raise ValueError("Unexpected build directory")
    archive = ROOT/"reports"/("before_clean_"+str(int(time.time()*1000000)))
    for file in out.rglob("*"):
        if not file.is_symlink() and file.is_file() and file.suffix in (".log",".json",".rpt",".txt"):
            target = archive/file.relative_to(out)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(str(file),str(target))
    shutil.rmtree(str(out))
    print("CLEAN PASS; saved evidence in "+str(archive))


def main():
    import fcntl
    parser = argparse.ArgumentParser()
    parser.add_argument("target",choices=("env","clean","compile","run","regress","negative","waves","verdi",
                       "timing","sweep","report","synth","probe","gate","package","vectors","paired"))
    parser.add_argument("--period",type=float,default=5.0)
    parser.add_argument("--netlist",choices=("rebuilt",),default="rebuilt")
    parser.add_argument("--vec",type=Path,default=ROOT/"vec")
    parser.add_argument("--jobs",type=int,default=4)
    a=parser.parse_args()
    if ROOT!=HOME/"v3.1" or not math.isfinite(a.period) or a.period<=0 or not 1<=a.jobs<=16:
        raise ValueError("Use the official v3.1 server directory, positive period and JOBS 1..16")
    lock=(ROOT/".manual.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    flow=load_flow()
    a.vec=a.vec.resolve()
    if a.vec!=ROOT/"vec" and ROOT/"vec" not in a.vec.parents:
        raise ValueError("VEC must be a directory under v3.1/vec")
    if a.target=="env":
        for tool in ("python3","make","vcs","dc_shell","pt_shell","verdi"):
            loc=shutil.which(tool);print(tool,loc);assert loc,tool
        libs=flow.libs()
        for path in list(libs["standard"].values())+sum(libs["sram"].values(),[])+[libs["standard_verilog"]]:
            assert Path(path).is_file(),path
        print("ENV PASS")
    elif a.target=="clean":clean(flow)
    elif a.target=="compile":
        for top in COUNTS:flow.compile_one(top)
        print("COMPILE PASS: 7 testbenches")
    elif a.target in ("run","regress","negative","waves"):
        vectors()
        if not (a.vec/"matrix_sat.hex").is_file():raise ValueError("Invalid VEC "+str(a.vec))
        if a.target in ("run","regress") and not all((a.vec/n).is_file() for n in ("dot_x.hex","quant_acc.hex")):
            raise ValueError("The full suite needs the base arithmetic vectors; use make regress for speech suites")
        if a.target=="negative":simulate(flow,"tb_kwt_negative",a.vec,"negative")
        elif a.target=="waves":simulate(flow,"tb_kwt_system",a.vec,"waves",True)
        else:
            for top in COUNTS:simulate(flow,top,a.vec,"default")
            suites=len(COUNTS)
            if a.target=="regress":
                for label in ["class_%02d"%i for i in range(12)]+["worst"]:
                    simulate(flow,"tb_kwt_system",ROOT/"vec/real_speech"/label,label);suites+=1
            print("FUNCTION ALL PASS: %d suites"%suites)
    elif a.target=="paired":
        vectors()
        record=simulate(flow,"tb_kwt_system",ROOT/"vec/real_speech/worst","worst")
        rows=record["matrix_cycles"]
        if len(rows)!=14 or [x["layer"] for x in rows[:12]]!=list(range(12)) or any(x["writes"]!=12672 for x in rows):
            raise ValueError("Unexpected matrix sequence")
        cycles=sum(x["core_cycles"] for x in rows[:12])
        baseline=HOME/"v3/results/functional.json"
        if digest(baseline)!="a49d9c55804b56c14f13a2f15ef05a732665e67120f70abc9302561d4d084e1f":
            raise ValueError("Frozen v3 comparison record changed")
        old=json.loads(baseline.read_text())["paired_cycle_comparison"]["v3_core_cycles"]
        print("PAIRED PASS: 12 tasks, %d cycles; v3 %d; equal-clock throughput %+.2f%%" %
              (cycles,old,100*(old/cycles-1)))
    elif a.target=="verdi":
        d=flow.OUT/"runs/waves/tb_kwt_system";wave=d/"waves.vcd"
        if not wave.is_file() or not wave.stat().st_size:raise ValueError("Run make waves first")
        env=dict(os.environ,**{k:str(d/"tmp") for k in ("TMP","TMPDIR","TEMP")})
        with (d/"verdi.log").open("w") as log:
            subprocess.Popen(["verdi","-sv","+define+KWT_USE_FOUNDRY_SRAM","+define+ARM_UD_MODEL",
                              *map(str,flow.sources("tb_kwt_system")),"-top","tb_kwt_system","-ssf",str(wave)],
                             cwd=str(d),env=env,stdout=log,stderr=subprocess.STDOUT)
        print("Verdi started: "+str(wave))
    elif a.target=="timing":timing(flow,a.netlist,a.period)
    elif a.target=="sweep":
        failed=[]
        for p in (6.666667,5.555556,5.0,4.761905,4.651163,4.545455):
            if not timing(flow,a.netlist,p,require_pass=False):
                failed.append("%.0f MHz"%(1000/p))
        if failed:raise ValueError("Sweep completed; timing violations at "+", ".join(failed))
    elif a.target=="report":report(flow,a.netlist,a.period,a.vec)
    elif a.target=="synth":
        subprocess.run([sys.executable,str(ROOT/"server_eda/qualify.py"),"--periods","5.0"],check=True)
    elif a.target in ("probe","gate"):
        implementation(flow,a.netlist)
        flow.gate(a.period,a.netlist,a.vec,a.jobs,a.target=="probe")
    elif a.target=="package":
        from assets import package
        package()
    else:vectors()


if __name__=="__main__":
    try:main()
    except Exception as e:print("FAIL: "+str(e),file=sys.stderr);sys.exit(1)
