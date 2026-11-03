"""Print a small public timing receipt, independently verifiable in the server project."""
import argparse
import json
from pathlib import Path
import re
from qualify import ROOT, HOME, digest, implementation_sources, load_flow
from snapshot import validate


def make_receipt():
    if ROOT!=HOME/"v3.1":
        raise ValueError("Read PPA evidence in the official server project")
    core=ROOT/"implementation/rebuilt/synth_kwt_nice_core"
    q=validate(core,implementation_sources())
    points=[[p["period_ns"],p["corner"],*p["setup_hold_ns"],len(p["reported_violations"])]
            for p in q["points"]]
    return {"top":"kwt_nice_core","scope":"SMIC40 pre-layout; same implemented netlist, SS/FF",
            "mapped_sha256":q["mapped_sha256"],"qualification_sha256":digest(core/"qualification.json"),
            "map_period_ns":q["mapped_period_ns"],"total_cell_area":q["v31_area"],
            "macro_area":q["macro_area"],"v3_cell_area":q["v3_reference_area"],
            "references_resized":len(q["resize_changes"]),
            "columns":["period_ns","corner","setup_ns","hold_ns","reported_violations"],
            "points":points}


def acceptance():
    from daily import COUNTS, report
    flow=load_flow()
    report(flow,"rebuilt",5.0,ROOT/"vec")
    receipt=make_receipt()
    if json.loads((ROOT/"results/ppa.json").read_text())!=receipt:
        raise ValueError("Public PPA summary changed")
    sets=["class_%02d"%i for i in range(12)]+["worst"]
    cycles=None
    for label in sets+["waves"]:
        vec=ROOT/"vec" if label=="waves" else ROOT/"vec/real_speech"/label
        run=flow.OUT/"runs"/label/"tb_kwt_system"
        record=json.loads((run/"verified.json").read_text())
        rows=record["matrix_cycles"]
        if not (record["passed"] and record["counts"]==[["29","29"]] and len(rows)==14
                and [m["layer"] for m in rows[:12]]==list(range(12))
                and all(m["writes"]==12672 for m in rows)
                and record["rtl_sha256"]==flow.source_hashes()
                and record["vectors_sha256"]=={f.name:digest(f) for f in vec.glob("*.hex")}
                and Path(record["vector_dir"]).resolve()==vec.resolve()
                and digest(run/"run.log")==record["log_sha256"]):
            raise ValueError("Speech suite is incomplete or stale: "+label)
        if label=="worst":
            perf=json.loads((ROOT/"results/functional.json").read_text())
            if [m["core_cycles"] for m in rows[:12]]!=perf["per_layer_cycles"]["v31"]:
                raise ValueError("VCS and XSim paired cycles differ")
            cycles=sum(m["core_cycles"] for m in rows[:12])
        if label=="waves" and not (run/"waves.vcd").stat().st_size:
            raise ValueError("Empty waveform")
    for corner in ("ss","ff"):
        probe=flow.OUT/"gate/rebuilt/5.0"/("vec_"+corner)/"annotation_probe"
        sta=flow.OUT/"timing/rebuilt/5.0"/("kwt_nice_core_"+corner)
        annotation=(probe/"sdf_annotation.log").read_text()
        if ("ANNOTATION_PROBE PASS" not in (probe/"run.log").read_text() or
                digest(probe/"mapped.sdf")!=digest(sta/"mapped.sdf") or any(
                not re.search(r"Total "+key+r":\s*0\b",annotation) for key in ("errors","warnings"))):
            raise ValueError("Invalid SDF probe: "+corner)
    published=ROOT/"releases/verification.json"
    expected={"directory":str(ROOT),"rtl_suites":COUNTS,"activation_sets":sets,
              "worst_first_12_cycles":cycles,"mapped_sha256":receipt["mapped_sha256"],
              "sdf_probes":{"ss":"PASS","ff":"PASS"},"waveform":"PASS","long_gate_run":False}
    if published.is_file() and json.loads(published.read_text())!=expected:
        raise ValueError("Published functional acceptance receipt differs")
    print("EXTENDED ACCEPT PASS: 7 base suites, 13 speech activation suites, waveform and both SDF probes")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=("show","verify","acceptance"))
    args=ap.parse_args()
    if args.action=="acceptance":
        acceptance()
        raise SystemExit(0)
    receipt=make_receipt()
    for key,value in receipt.items():
        if key.endswith("sha256"):
            print(key," ".join(value[i:i+8] for i in range(0,len(value),8)))
        elif key!="points": print(key,value)
    for row in receipt["points"]: print(*row)
    if args.action=="verify":
        local=json.loads((ROOT/"results/ppa.json").read_text())
        if local!=receipt:
            raise ValueError("Public summary differs from the installed qualification")
        print("PUBLIC PPA MATCH",digest(ROOT/"results/ppa.json"))
