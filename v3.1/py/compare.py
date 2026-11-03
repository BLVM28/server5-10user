"""Audit the local paired experiment and the final page/port stress cases."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
V3=ROOT.parent/"v3"
VEC=ROOT.parent/"v2/vec"
EXPECTED={"tb_kwt_arithmetic":260,"tb_v3_carries":7,"tb_kwt_icb":4,"tb_kwt_system":29,
          "tb_kwt_overlap":5,"tb_kwt_negative":58,"tb_kwt_mul_pipeline":524288}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def trial(tag,top,vec,count,panel_only=False):
    project=ROOT
    if panel_only and (ROOT/"build/prefetch_reference/build"/tag/"results.json").is_file():
        project=ROOT/"build/prefetch_reference"
    run=project/"build"/tag
    rec=json.loads((run/"results.json").read_text())
    hashes={name.replace("\\","/"):value for name,value in rec["source_sha256"].items()}
    assert rec["vector_sha256"]=={p.name:sha(p) for p in vec.glob("*.hex")}
    for p in (ROOT/"rtl").glob("*.sv"):
        actual=V3/"rtl"/p.name if panel_only and p.name=="kwt_mul16_pipe.sv" else p
        assert hashes["rtl/"+p.name]==sha(actual),p.name
    generated=run/(top+".sv")
    original=ROOT/"tb"/(top+".sv")
    if generated.exists():
        # The v2 XSim launcher may substitute only the vectors' default path.
        import os
        rel=os.path.relpath(vec.resolve(),run).replace("\\","/")
        assert generated.read_text(encoding="utf-8")==original.read_text(encoding="utf-8").replace('dir="../../vec"','dir="'+rel+'"')
        key=generated.relative_to(project).as_posix()
        assert hashes[key]==sha(generated)
    else:
        assert hashes["tb/"+original.name]==sha(original)
    tests={t["top"]:t["pass_markers"] for t in rec["tests"]}
    assert tests[top]==[[str(count),str(count)]]
    log=run/(top+".log")
    data=log.read_text(encoding="utf-8",errors="replace")
    matches=re.findall(r"ALL PASS,[^\n]*|PANEL PASS[^\n]*|matrix layer [^\n]*",data)
    assert len([m for m in matches if m.startswith("ALL PASS,")])==1 and "$fatal" not in data
    return {"run":tag,"top":top,"count":count,"defines":rec["defines"],
            "log_sha256":sha(log),"tb_sha256":sha(original),"measurement_lines":matches}


def layers(entry):
    rows=[list(map(int,m.groups())) for text in entry["measurement_lines"]
          for m in [re.fullmatch(r"matrix layer (\d+) PASS core_cycles=(\d+) writes=(\d+)",text)] if m]
    assert len(rows)==14 and [x[0] for x in rows[:12]]==list(range(12))
    assert all(x[2]==12672 for x in rows)
    return [x[1] for x in rows[:12]]


def main():
    frozen=json.loads((V3/"results/functional.json").read_text())
    runs=json.loads((V3/"results/xsim_worst/results.json").read_text())
    assert runs["vector_sha256"]=={p.name:sha(p) for p in (VEC/"real_speech/worst").glob("*.hex")}
    assert sha(V3/"tb/tb_kwt_system.sv")==sha(ROOT/"tb/tb_kwt_system.sv")
    v3=frozen["paired_cycle_comparison"]["per_layer_v3"]
    base=[trial("panel_stress" if top=="tb_kwt_overlap" else "final_base",top,VEC,n) for top,n in EXPECTED.items()]
    for tag in ("panel_stress","panel_swap_large"):
        stress=trial(tag,"tb_kwt_overlap",VEC,5)
        assert any(re.search(r"PANEL PASS 2/2.*full=[1-9]\d* partial=[1-9]\d* port_stalls=[1-9]\d* reads=[1-9]\d*",s)
                   for s in stress["measurement_lines"])
        if tag=="panel_swap_large":base.append(stress)
    a,b=[trial(tag,"tb_kwt_system",VEC/"real_speech/worst",29,tag=="panel_only")
         for tag in ("panel_only","final_worst")]
    counts={"v3":v3,"prefetch_only":layers(a),"v31":layers(b)}
    sums={k:sum(v) for k,v in counts.items()}
    result={"workload":"same worst 12 layers, first pass only, same system TB, 12672 word writes per matrix",
            "per_layer_cycles":counts,"total_cycles":sums,"relative_cycle_change":sums["v31"]/sums["v3"]-1,
            "equal_clock_throughput_gain":sums["v3"]/sums["v31"]-1,
            "rtl_sha256":{p.name:sha(p) for p in sorted((ROOT/"rtl").glob("*.sv"))},
            "v3_baseline_evidence_sha256":sha(V3/"results/functional.json"),
            "xsim":base+[a,b]}
    target=ROOT/"results/functional.json"
    target.write_bytes((json.dumps(result,indent=2)+"\n").encode("utf-8"))
    print("MATCHED PASS",sums)


if __name__=="__main__":
    main()
