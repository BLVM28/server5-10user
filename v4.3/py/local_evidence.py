"""Publish only checked local evidence; never infer a server pass."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):
    (ROOT/"results").mkdir(exist_ok=True)
    (ROOT/"results"/name).write_bytes((json.dumps(value,indent=2,ensure_ascii=False)+"\n").encode("utf-8"))
def main():
    path=ROOT/"build/public_full";rec=json.loads((path/"results.json").read_text())
    assert rec["tests"]==[{"top":"tb_kwt_public_sram","pass_markers":[["29","29"]]}]
    for name,h in rec["source_sha256"].items():assert sha(ROOT/name)==h
    text=(path/"tb_kwt_public_sram.log").read_text()
    assert "STREAM GUARD PASS 25/25" in text and "ALL PASS, 29/29" in text
    rows=[dict(layer=int(i),cycles=int(c),reads=int(r),writes=int(w),mode=int(m)) for i,c,r,w,m in
      re.findall(r"NICE_TIME layer=(\d+) cycles=(\d+) reads=(\d+) writes=(\d+) mode=(\d+)",text)]
    assert len(rows)==14 and [r["layer"] for r in rows[:12]]==list(range(12)) and all(r["mode"]==3 for r in rows)
    total=sum(r["cycles"] for r in rows[:12])
    write("functional.json",dict(tool="XSim 2023.2",endpoint="unaltered public E203 sirv_sram_icb_ctrl, functional one-cycle RAM",
      passed=True,matrices=rows,scenarios=29,stream_guards=25,total_12_cycles=total,tasks_s_at_150=1800000000./total,
      log_sha256=sha(path/"tb_kwt_public_sram.log"),sources=rec["source_sha256"]))
    speech=ROOT/"build/speech";a=json.loads((speech/"accuracy.json").read_text())
    old=json.loads((ROOT.parent/"v4.2/results/accuracy.json").read_text())
    assert a["samples"]==600 and a["cases_over_3_percent"]==0 and a["max_layer_nrmse"]==old["max_layer_nrmse"]
    assert a["rice_sha256"]==sha(ROOT/"py/rice.py") and a["profile_sha256"]==sha(ROOT/"py/profile42.json")
    for src,dst in (("accuracy.json","accuracy.json"),("manifest.json","accuracy_provenance.json"),("cases.json","accuracy_cases.json")):
        (ROOT/"results"/dst).write_bytes((speech/src).read_bytes())
    proof={"precision_scope":"fresh 600-sample original float Dense1 vs frozen numeric v4.2; NOT quantized end-to-end word recognition accuracy",
      "validation_real_distinct_wavs":550,"silence_copies":50,"layer_comparisons":7200,
      "profile_unchanged_from_v42":sha(ROOT/"py/profile42.json")==sha(ROOT.parent/"v4.2/py/profile42.json"),
      "math_unchanged_from_v42":sha(ROOT/"py/rice.py")==sha(ROOT.parent/"v4.2/py/rice.py"),
      "fresh_log_sha256":sha(ROOT/"build/accuracy_run.log"),"script_sha256":sha(ROOT/"py/qualify_speech.py"),
      "stream_generator_sha256":sha(ROOT/"py/streams43.py"),
      "actual_pin_level_transport_and_C_proofs":["functional.json","driver.json","rv32.json"]}
    assert proof["profile_unchanged_from_v42"] and proof["math_unchanged_from_v42"]
    write("accuracy_audit.json",proof);print("LOCAL EVIDENCE PASS",total,1800000000./total)
if __name__=="__main__":main()
