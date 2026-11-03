"""Release arithmetic, throughput and causal identity checks against live EDA records."""
import argparse,json,re,sys
from pathlib import Path
from daily import ROOT,RAW,LABELS,COUNTS,record,report,load_flow,digest,implementation,implementation_sources,verify
from snapshot import validate
PERIOD=6.666667
def load(rel):return json.loads((ROOT/rel).read_text())
def match(rel,target):
    if load(rel)!=target:raise ValueError("Published file differs: "+rel)
def ppa():
    core=ROOT/"implementation/rebuilt/synth_kwt_nice_core"
    q=validate(core,implementation_sources())
    return {"mapped_sha256":q["mapped_sha256"],"qualification_sha256":digest(core/"qualification.json"),
      "map_period_ns":q["mapped_period_ns"],"area_um2":q["v41_area"],"macro_um2":q["macro_area"],
      "v4_um2":q["v4_reference_area"],"resize_count":len(q["resize_changes"]),
      "points":[[p["period_ns"],p["corner"],*p["setup_hold_ns"],len(p["reported_violations"])] for p in q["points"]]}
def workloads(flow):
    stats={};local=load("results/functional.json")
    for k in LABELS:
        result=[]
        for t in ("tb_kwt_system","tb_kwt_compact","tb_kwt_block8"):
            j=record(flow,k,t);rows=j["nice_cycles"][:12]
            if t=="tb_kwt_block8":
                assert [m["cycles"] for m in rows]==local["fast_nice_cycles"],k
                assert all(m["reads"]==6075 and m["writes"]==6752 and m["compact"]==2 for m in rows)
            result.extend([sum(x["cycles"] for x in rows),sum(x["writes"] for x in rows)])
        assert 150000000*12>=1500*result[-2],k
        stats[k]=result
    return stats
def acceptance(flow):
    report(flow,PERIOD);verify(False)
    assert all(digest(RAW/n)==h for n,h in load("py/vector_manifest.json").items())
    q=ppa();match("results/ppa.json",q)
    qualified={p[0] for p in q["points"] if p[1]=="ss" and min(p[2:4])>=0 and p[4]==0}
    qualified&={p[0] for p in q["points"] if p[1]=="ff" and min(p[2:4])>=0 and p[4]==0}
    assert any(p<6.25 for p in qualified),"Failed to exceed v4 160 MHz"
    stats=workloads(flow);match("results/workloads.json",stats)
    for top,n in (("tb_kwt_fast_return",1),("tb_kwt_block8_immediate",12)):
        d=ROOT/"build/immediate"/top;rec=json.loads((d/"verified.json").read_text())
        assert rec["count"]==n and rec["rtl"]==flow.source_hashes() and rec["log_sha256"]==digest(d/"run.log")
        assert rec["signature"]==flow.signature(top)
    mode_dir=ROOT/"build/modes/run";mrec=json.loads((mode_dir/"verified.json").read_text())
    assert mrec["rtl"]==flow.source_hashes() and mrec["log_sha256"]==digest(mode_dir/"run.log")
    assert mrec["signature"]==flow.signature("tb_kwt_modes")
    # Cross-simulator dumps may differ in comments/case. Compare the actual 6,752 words.
    d=ROOT/"build/immediate/tb_kwt_block8_immediate"
    for i in range(12):
        words=[int(x.strip(),16) for x in (d/("block8_layer%02d.hex"%i)).read_text().splitlines() if re.fullmatch(r"[0-9a-fA-F]{8}",x.strip())]
        gold=[int(x,16) for x in (ROOT/"vec/fast/worst"/("layer%02d_wire.hex"%i)).read_text().splitlines()]
        assert words==gold and len(words)==6752
    wdir=flow.OUT/"runs/waves/tb_kwt_system"
    wave=json.loads((wdir/"verified.json").read_text())
    assert (wdir/"waves.vcd").stat().st_size>0 and wave["passed"] and wave["rtl_sha256"]==flow.source_hashes()
    assert wave["log_sha256"]==digest(wdir/"run.log") and Path(wave["vector_dir"]).resolve()==RAW.resolve()
    gate=load("build/gate_sample/sample.json");assert {p["corner"] for p in gate}=={"ss","ff"} and len(gate)==2
    archive={p["corner"]:p for p in load("results/gate.json")}
    for p in gate:
        c=p["corner"];assert p["layer"]==0 and p["transactions"]==12827 and p["writes"]==6752 and p["netlist_sha256"]==q["mapped_sha256"]
        assert all(p[k]==archive[c][k] for k in ("netlist_sha256","layer","writes","transactions"))
        root=ROOT/"build/gate_sample";out=root/"gate/rebuilt"/str(PERIOD)/("worst_"+c)
        assert digest(root/"timing/rebuilt"/str(PERIOD)/("kwt_nice_core_"+c)/"mapped.sdf")==p["sdf_sha256"]
        assert digest(out/"block8_layer00/run.log")==p["log_sha256"]
        ann=(out/"annotation_probe/sdf_annotation.log").read_text()
        assert all(re.search(r"Total "+k+r":\s*0\b",ann) for k in ("errors","warnings"))
    a=load("results/accuracy.json");cases=load("results/accuracy_cases.json")
    all_cases=[x for c in cases for x in c["layer_nrmse"]]
    assert a["block8_sha256"]==digest(ROOT/"py/block8.py") and len(all_cases)==7200 and max(all_cases)==a["max_single_nrmse"]<.03
    assert a["max_layer_nrmse"]<.03 and a["cases_over_3_percent"]==0
    provenance=load("results/accuracy_provenance.json")
    assert provenance["case_report_sha256"]==digest(ROOT/"results/accuracy_cases.json")
    assert provenance["qualifier_sha256"]==digest(ROOT/"py/qualify_speech.py")
    assert load("results/driver.json")["c_header_sha256"]==digest(ROOT/"integration/kwt_v41_block8.h")
    assert load("results/rv32.json")["source_sha256"]==digest(ROOT/"integration/block8_driver_probe.c")
    match("releases/verification.json",{"rtl_suites":len(COUNTS)+39,"map_sha256":q["mapped_sha256"],
      "gate_corners":["ss","ff"],"gate_layer":0,"gate_tb_sha256":digest(ROOT/"server_eda/tb_core_all_gate.sv"),
      "fast_cycles":stats["worst"][4],"accuracy_cases":7200,"class_tasks":144})
    print("EXTENDED ACCEPT PASS 50 VCS suites, 1500+ tasks/s, higher clock, two complete SDF matrices, 7200 float cases")
def main():
    cli=argparse.ArgumentParser();cli.add_argument("action",choices=("ppa","stats","acceptance","gate"));a=cli.parse_args()
    f=load_flow()
    if a.action=="acceptance":acceptance(f)
    elif a.action=="stats":
        for n,v in workloads(f).items():print(n,*v)
    elif a.action=="gate":
        for p in load("build/gate_sample/sample.json"):
            for k in ("netlist_sha256","sdf_sha256","log_sha256"):print(p["corner"],k," ".join(p[k][i:i+8] for i in range(0,64,8)))
    else:
        p=ppa()
        for k,v in p.items():
            if k.endswith("sha256"):print(k," ".join(v[i:i+8] for i in range(0,64,8)))
            elif k!="points":print(k,v)
        for row in p["points"]:print(*row)
if __name__=="__main__":main()
