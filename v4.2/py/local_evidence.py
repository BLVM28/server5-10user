"""Hash-bind the XSim measurements, exact sample identities and frozen software ABI."""
import hashlib,json,math,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,data):p.write_bytes((json.dumps(data,indent=2)+"\n").encode())
def xsim(tag,vec):
    d=ROOT/"build"/tag;result=load(d/"results.json")
    assert result["vector_sha256"]=={p.name:sha(p) for p in vec.glob("*.hex")}
    for n,h in result["source_sha256"].items():
        source=ROOT/n;assert sha(source)==h
        if source.resolve().parent==d.resolve() and source.name.startswith("tb_"):
            current=(ROOT/"tb"/source.name).read_text()
            rel=os.path.relpath(vec,d).replace("\\","/")
            assert source.read_text()==current.replace('dir="../../vec"','dir="'+rel+'"')
    logs={}
    for result in result["tests"]:
        path=d/(result["top"]+".log");data=path.read_text(errors="replace")
        assert all(a==b for a,b in result["pass_markers"]) and "ALL PASS," in data and "Fatal:" not in data
        logs[result["top"]]=sha(path)
    return logs
def measured(tag):
    d=ROOT/"build"/tag
    text=(d/"tb_kwt_precision.log").read_text(errors="replace")
    rows=re.findall(r"NICE_TIME layer=(\d+) cycles=(\d+) reads=(\d+) writes=(\d+) compact=(\d+)",text)
    assert len(rows)==14 and [int(v[0]) for v in rows[:12]]==list(range(12))
    assert "PRECISION GUARD PASS 9/9" in text
    cols=list(zip(*rows[:12]))
    cycles=list(map(int,cols[1]));return {"nice_cycles":cycles,"cycles":sum(cycles),"tasks_per_s_150MHz":1800000000/sum(cycles),
        "reads":list(map(int,cols[2])),"writes":list(map(int,cols[3]))}
def main():
    raw=ROOT.parent/"v2/vec";vec=ROOT/"vec/precision/worst"
    log={tag:xsim(tag,source) for tag,source in (("trial_four",vec),("trial_three",vec),("fix03",ROOT/"vec/precision/class_03"),("swap42",vec),
          ("immediate42",vec),("rice_unit",raw),("dot_unit",raw),("legacy_final",raw))}
    f=measured("trial_four");three=measured("trial_three");assert f==measured("swap42")
    assert f["cycles"]<three["cycles"]
    baseline=sum(load(ROOT.parent/"v4.1/results/functional.json")["fast_nice_cycles"])
    save(ROOT/"results/functional.json",{"v41_same12_cycles":baseline,"four_row":f,"three_row":three,
        "refill_case_class03":measured("fix03"),
        "xsim_logs_sha256":log,"rtl_sha256":{p.name:sha(p) for p in sorted((ROOT/"rtl").glob("*.sv"))}})
    identity=load(ROOT/"results/accuracy_provenance.json")
    prior=load(ROOT.parent/"v4.1/results/accuracy_provenance.json")
    training=load(ROOT/"results/training_samples.json");cases=load(ROOT/"results/accuracy_cases.json")
    assert len(identity)==600 and len(cases)==600 and len(training)==33
    paths=[s["path"] for s in identity if s["class_id"]!=0]
    assert len(set(paths))==550 and set(paths).isdisjoint({s["path"] for s in training})
    # Earlier versions stored the v2 sample manifest as part of their evidence.
    original=ROOT.parent/"v2/validation_real_speech_20261102/manifest.json";older=load(original)
    assert sha(original)==prior["manifest_v2_sha256"] and len(older)==len(identity)
    fields=("id","path","split","label","class_id")
    assert all(all(a[k]==b[k] for k in fields) for a,b in zip(identity,older))
    for sample in older:
        if sample["class_id"]!=0:assert sha(ROOT.parent/"datasets/speech_commands_v0.02/validation"/sample["path"])==sample["sha256"]
    acc=load(ROOT/"results/accuracy.json")
    assert acc["samples"]==600 and acc["checkpoint_tensors"]==162 and acc["native_logits_replays"]==600
    assert all(math.isfinite(v) and v>=0 for s in cases for v in s["layer_nrmse"])
    assert abs(max(max(s["layer_nrmse"]) for s in cases)-acc["max_single_nrmse"])<1e-14
    assert max(v[1] for v in acc["layers"])==acc["max_layer_nrmse"] and acc["max_layer_nrmse"]<=.0015
    assert sum(v>.03 for case in cases for v in case["layer_nrmse"])==0
    assert acc["rice_sha256"]==sha(ROOT/"py/rice.py") and acc["profile_sha256"]==sha(ROOT/"py/profile42.json")
    data=ROOT.parent/"datasets/speech_commands_v0.02"
    validation=set((data/"validation_list.txt").read_text().splitlines());testing=set((data/"testing_list.txt").read_text().splitlines())
    assert set(paths)<=validation and not set(paths)&testing
    assert not {s["path"] for s in training}&(validation|testing)
    save(ROOT/"results/accuracy_audit.json",{"training_wavs":33,"validation_wavs":550,"silence_copies":50,
        "validation_sha256":sha(ROOT/"results/accuracy_provenance.json"),"v41_validation_reference":prior["manifest_v2_sha256"],
        "training_sha256":sha(ROOT/"results/training_samples.json"),"qualifier_sha256":sha(ROOT/"py/qualify_speech.py"),
        "train_capture_sha256":sha(ROOT/"py/capture_training.py"),"cases_sha256":sha(ROOT/"results/accuracy_cases.json")})
    print("LOCAL EVIDENCE PASS",f["cycles"],three["cycles"],acc["max_layer_nrmse"])
if __name__=="__main__":main()
