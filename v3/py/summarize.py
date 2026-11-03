"""Verify the local logs and compare twelve matched v2/v3 Dense1 tasks."""
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT.parent / "v2"
BASE_COUNTS = {"tb_kwt_arithmetic":260, "tb_v3_carries":7, "tb_kwt_system":29,
               "tb_kwt_overlap":5, "tb_kwt_negative":58, "tb_kwt_icb":4,
               "tb_kwt_mul_pipeline":524288}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_suite(tag, counts, vectors):
    run = ROOT / "build" / ("final_" + tag)
    data = json.loads((run/"results.json").read_text(encoding="utf-8"))
    expected_markers = {top:[[str(n),str(n)]] for top,n in counts.items()}
    assert {t["top"]:t["pass_markers"] for t in data["tests"]} == expected_markers
    assert {p.name:sha(p) for p in vectors.glob("*.hex")} == data["vector_sha256"]
    assert all(sha(ROOT/name)==h for name,h in data["source_sha256"].items())
    dest = ROOT / "results" / ("xsim_" + tag)
    dest.mkdir(exist_ok=True)
    shutil.copyfile(run/"results.json",dest/"results.json")
    for top in counts:
        shutil.copyfile(run/(top+".log"),dest/(top+".log"))
    text = (dest/"tb_kwt_system.log").read_text(encoding="utf-8",errors="replace")
    matrix = [list(map(int,row)) for row in re.findall(
        r"matrix layer (\d+) PASS core_cycles=(\d+) writes=(\d+)",text)]
    assert len(matrix)==14 and [i for i,_,_ in matrix[:12]]==list(range(12))
    assert all(writes==12672 for _,_,writes in matrix)
    return {"tests":counts,"matrix_rows":matrix,"log_sha256":{p.name:sha(p) for p in dest.glob("*.log")}}


def main():
    suites = {"base":read_suite("base",BASE_COUNTS,V2/"vec"),
              "worst":read_suite("worst",{"tb_kwt_system":29},V2/"vec/real_speech/worst")}
    previous = V2/"validation_real_speech_20261102"
    old = json.loads((previous/"rtl_results.json").read_text(encoding="utf-8"))
    old_run = json.loads((previous/"logs/worst_results.json").read_text(encoding="utf-8"))
    assert old_run["vector_sha256"] == {p.name:sha(p) for p in (V2/"vec/real_speech/worst").glob("*.hex")}
    assert (ROOT/"tb/tb_kwt_system.sv").read_bytes() == (V2/"tb/tb_kwt_system.sv").read_bytes()
    old_rows = [list(map(int,row)) for row in next(
        t for t in old["suites"] if t["suite"]=="worst")["matrix_results"]]
    new_rows = suites["worst"]["matrix_rows"]
    assert [(i,w) for i,_,w in old_rows] == [(i,w) for i,_,w in new_rows]
    a = sum(c for _,c,_ in old_rows[:12])
    b = sum(c for _,c,_ in new_rows[:12])
    result = {"suites":suites,"paired_cycle_comparison":{
        "workload":"identical worst vectors and TB, 12 distinct layers; exclude two recovery repetitions",
        "v2_core_cycles":a,"v3_core_cycles":b,"change_percent":100*(b/a-1),
        "per_layer_v2":[c for _,c,_ in old_rows[:12]],"per_layer_v3":[c for _,c,_ in new_rows[:12]]},
        "rtl_sha256":{p.name:sha(p) for p in sorted((ROOT/"rtl").glob("*.sv"))}}
    (ROOT/"results/functional.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("FUNCTION AUDIT PASS; matched 12 tasks: v2=%d, v3=%d cycles"%(a,b))


if __name__=="__main__":
    main()
