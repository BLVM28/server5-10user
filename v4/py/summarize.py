"""Read validated XSim records. Keep inter-task resets, seven hold clocks and repeats out of task time."""
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/"v3.1"
VEC=ROOT.parent/"v2/vec"
COUNTS={"tb_kwt_arithmetic":260,"tb_v3_carries":7,"tb_kwt_icb":4,"tb_kwt_system":29,
        "tb_kwt_compact":29,"tb_kwt_overlap":5,"tb_kwt_negative":58,"tb_kwt_mul_pipeline":524288,"tb_kwt_codec":4096}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def check(run,rtl,vec,counts):
    rec=json.loads((run/"results.json").read_text())
    hashes={k.replace("\\","/"):v for k,v in rec["source_sha256"].items()}
    assert all(hashes["rtl/"+p.name]==sha(p) for p in (rtl/"rtl").glob("*.sv"))
    assert rec["vector_sha256"]=={p.name:sha(p) for p in vec.glob("*.hex")}
    project=run.parents[1]
    for name,h in hashes.items():assert sha(project/name)==h,(name,h)
    results={t["top"]:t["pass_markers"] for t in rec["tests"]}
    assert results=={top:[[str(n),str(n)]] for top,n in counts.items()}
    for top in counts:
        log=(run/(top+".log")).read_text(encoding="utf-8",errors="replace")
        assert not re.search(r"Fatal:|\$fatal|FATAL",log)
        if top=="tb_kwt_overlap":assert "PAGE PASS 2/2" in log
        if top in ("tb_kwt_compact","tb_kwt_export"):assert "COMPACT GUARD PASS 2/2" in log
    return {top:sha(run/(top+".log")) for top in counts}
def measurement(run,top,expected=None):
    log=(run/(top+".log")).read_text(encoding="utf-8",errors="replace")
    rows=[list(map(int,x)) for x in re.findall(r"NICE_TIME layer=(\d+) cycles=(\d+) reads=(\d+) writes=(\d+) compact=(\d+)",log)]
    core=[list(map(int,x)) for x in re.findall(r"matrix layer (\d+) PASS core_cycles=(\d+) writes=(\d+)",log)]
    assert len(rows)==len(core)==14 and [a[0] for a in rows[:12]]==list(range(12))
    for a,m in zip(rows,core):
        assert a[0]==m[0] and a[1]>m[1] and a[2]==11624 and a[3]==m[2]
        assert a[3]==(expected[a[0]] if a[4] else 12672)
    return {"nice":[a[1] for a in rows[:12]],"core":[m[1] for m in core[:12]],
            "writes":[a[3] for a in rows[:12]],"total_nice":sum(a[1] for a in rows[:12]),
            "tasks_s_150":1800000000/sum(a[1] for a in rows[:12])}
def main():
    out=ROOT/"build";old=out/"v31_reference/build/paired";vec=VEC/"real_speech/worst"
    logs={"base":check(out/"base",ROOT,VEC,COUNTS),"paired":check(out/"paired",ROOT,vec,{"tb_kwt_system":29,"tb_kwt_compact":29}),
          "swap_large":check(out/"swap",ROOT,vec,{"tb_kwt_compact":29,"tb_kwt_overlap":5}),
          "v31":check(old,OLD,vec,{"tb_kwt_system":29}),"export":check(out/"export",ROOT,vec,{"tb_kwt_export":29})}
    codec=json.loads((ROOT/"results/codec.json").read_text());expected=[m["physical_writes"] for m in codec["matrices"]["worst"]]
    values={"v31_raw":measurement(old,"tb_kwt_system"),"v4_raw":measurement(out/"paired","tb_kwt_system"),
            "v4_packed":measurement(out/"paired","tb_kwt_compact",expected)}
    assert sum(values["v31_raw"]["core"])==json.loads((OLD/"results/functional.json").read_text())["total_cycles"]["v31"]
    assert measurement(out/"swap","tb_kwt_compact",expected)==values["v4_packed"]
    assert measurement(out/"export","tb_kwt_export",expected)==values["v4_packed"]
    assert codec["actual_dut_frames"]==12 and len(codec["captured_sha256"])==12
    item={"timing_window":"NICE instruction handshake to first result-valid, no inter-task reset/backpressure tail",
          "paired":values,"base_suites":COUNTS,"rtl_sha256":{p.name:sha(p) for p in sorted((ROOT/"rtl").glob("*.sv"))},
          "xsim_log_sha256":logs,"integer_oracle":"v2/vec frozen, SHA verified against each XSim run"}
    (ROOT/"results/functional.json").write_bytes((json.dumps(item,indent=2)+"\n").encode())
    print("PAIRED PASS",[(k,v["total_nice"],round(v["tasks_s_150"],2)) for k,v in values.items()])
if __name__=="__main__":main()
