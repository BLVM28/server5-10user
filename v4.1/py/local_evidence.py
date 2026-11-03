"""Verify the XSim records and float workload identities before publishing a receipt."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(rel,obj):(ROOT/rel).write_bytes((json.dumps(obj,indent=2)+"\n").encode())
def xsim(tag,source_vec):
    d=ROOT/"build"/tag
    rec=json.loads((d/"results.json").read_text())
    assert rec["vector_sha256"]=={p.name:sha(p) for p in source_vec.glob("*.hex")}
    for name,h in rec["source_sha256"].items():
        assert sha(ROOT/name)==h,(tag,name)
    logs={}
    for t in rec["tests"]:
        name=t["top"];log=d/(name+".log")
        assert all(a==b for a,b in t["pass_markers"])
        assert "ALL PASS," in log.read_text(errors="replace")
        logs[name]=sha(log)
    return logs
def main():
    raw=ROOT.parent/"v2/vec";fast=ROOT/"vec/fast/worst"
    logs={n:xsim(n,v) for n,v in [("legacy",raw),("trial",fast),("alt",fast),("bfpunit",raw),("immediate",fast)]}
    def counts(tag):
        data=(ROOT/"build"/tag/"tb_kwt_block8.log").read_text(errors="replace")
        rows=[list(map(int,a)) for a in re.findall(r"NICE_TIME layer=(\d+) cycles=(\d+) reads=(\d+) writes=(\d+) compact=(\d+)",data)]
        assert len(rows)==14 and [a[0] for a in rows[:12]]==list(range(12))
        assert all(a[2:]==[6075,6752,2] for a in rows) and "BLOCK8 GUARD PASS 4/4" in data
        return [a[1] for a in rows[:12]]
    times=counts("trial");assert times==counts("alt")
    old=json.loads((ROOT.parent/"v4/results/functional.json").read_text())["paired"]
    v={"baseline_v4_raw":old["v4_raw"]["total_nice"],"baseline_v4_compact":old["v4_packed"]["total_nice"],
       "fast_nice_cycles":times,"total_fast_cycles":sum(times),"fast_tasks_per_s_150":1800000000.0/sum(times),
       "clocks_left_for_1500":1200000-sum(times),"reads_per_task":6075,"writes_per_task":6752,
       "xsim_logs_sha256":logs,"rtl_sha256":{p.name:sha(p) for p in sorted((ROOT/"rtl").glob("*.sv"))}}
    write("results/functional.json",v)
    run=ROOT/"build/speech";a=json.loads((run/"accuracy.json").read_text())
    v2=ROOT.parent/"v2/validation_real_speech_20261102"
    source=json.loads((v2/"manifest.json").read_text())
    current=json.loads((run/"manifest.json").read_text())
    fields=("id","path","split","label","class_id")
    assert len(current)==len(source)==600 and all(all(old[k]==new[k] for k in fields) for old,new in zip(source,current))
    cases=json.loads((run/"cases.json").read_text())
    ys=[v for c in cases for v in c["layer_nrmse"]]
    assert len(ys)==7200 and max(ys)==a["max_single_nrmse"] and max(ys)<.03
    assert a["block8_sha256"]==sha(ROOT/"py/block8.py") and a==json.loads((ROOT/"results/accuracy.json").read_text())
    for s in source:
        if not s["path"].startswith("generated:"):
            assert sha(ROOT.parent/"datasets/speech_commands_v0.02/validation"/s["path"])==s["sha256"]
    write("results/accuracy_cases.json",cases)
    write("results/accuracy_provenance.json",{"samples":600,"comparisons":len(ys),"real_wavs_checked":550,
      "manifest_v2_sha256":sha(v2/"manifest.json"),"prior_v4_numeric_report_sha256":sha(v2/"report.json"),
      "case_report_sha256":sha(ROOT/"results/accuracy_cases.json"),"qualifier_sha256":sha(ROOT/"py/qualify_speech.py")})
    print("XSIM / FLOAT PROVENANCE PASS",sum(times),len(ys))
if __name__=="__main__":main()
