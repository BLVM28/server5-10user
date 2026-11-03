"""Extract public summary metrics while keeping library, netlist and raw reports in the private work area."""
import argparse,json,math
from pathlib import Path
from daily import ROOT,COUNTS,LABELS,record,report,load_flow,digest,implementation_sources,verify
from snapshot import validate
PERIOD=6.666667
MODES=("tb_kwt_system","tb_kwt_compact","tb_kwt_block8","tb_kwt_precision")
def load(rel):return json.loads((ROOT/rel).read_text())
def ppa():
    core=ROOT/"implementation/rebuilt/synth_kwt_nice_core";q=validate(core,implementation_sources())
    return {"mapped_sha256":q["mapped_sha256"],"qualification_sha256":digest(core/"qualification.json"),
            "formal":load("implementation/rebuilt/synth_kwt_nice_core/formal_receipt.json") if (core/"formal_receipt.json").is_file() else None,
            "map_period_ns":q["mapped_period_ns"],"area_um2":q["v42_area"],"macro_um2":q["macro_area"],
            "v41_area_um2":q["v41_reference_area"],"resize_changes":q["resize_changes"],"macros":{"SP1024x16":8,"SP128x16":32},
            "points":[[p["period_ns"],p["corner"],*p["setup_hold_ns"],len(p["reported_violations"])] for p in q["points"]]}
def statistics(flow):
    groups={}
    for label in LABELS:
        modes={}
        for t in MODES:
            run=record(flow,label,t);rows=run["nice_cycles"][:12]
            assert len(rows)==12 and [r["layer"] for r in rows]==list(range(12))
            item={"cycles":sum(r["cycles"] for r in rows),"reads":sum(r["reads"] for r in rows),
                  "writes":sum(r["writes"] for r in rows)}
            if t=="tb_kwt_precision":item["layers"]=[r["cycles"] for r in rows]
            modes[t]=item
        groups[label]=modes
    return groups
def extra(flow):
    items={}
    for t,n in (("tb_kwt_stream_dot",64),("tb_kwt_rice_codec",1542),("tb_kwt_fast_return",1),("tb_kwt_block8_immediate",12),("tb_kwt_precision_immediate",12),("tb_kwt_modes",8)):
        d=ROOT/("build/modes/run" if t=="tb_kwt_modes" else "build/immediate/"+t)
        proof=json.loads((d/"verified.json").read_text())
        assert proof["rtl"]==flow.source_hashes() and proof["signature"]==flow.signature(t)
        assert digest(d/"run.log")==proof["log_sha256"]
        assert "ALL PASS, %d/%d"%(n,n) in (d/"run.log").read_text()
        items[t]=[n,proof["log_sha256"]]
    return items
def collect(flow):
    report(flow,PERIOD);verify(False)
    pp=ppa();stats=statistics(flow);ex=extra(flow)
    gate=load("build/gate_sample/sample.json")
    assert len(gate)==2 and {r["corner"] for r in gate}=={"ss","ff"}
    for r in gate:
        corner=r["corner"];sdir=ROOT/"build/gate_sample"
        src=sdir/"timing/rebuilt"/str(PERIOD)/("kwt_nice_core_"+corner)/"mapped.sdf"
        run=sdir/"gate/rebuilt"/str(PERIOD)/("worst_"+corner)/"precision_layer00/run.log"
        assert r["netlist_sha256"]==pp["mapped_sha256"] and r["sdf_sha256"]==digest(src) and r["log_sha256"]==digest(run)
        assert r["writes"]==4471 and r["transactions"]==10274
    return {"ppa":pp,"workloads":stats,"gate":gate,"extra":ex,"vcs_suites":len(COUNTS)+52}
def main(action):
    f=load_flow()
    if action=="collect":
        data=collect(f);dest=ROOT/"reports/public.json"
        dest.write_text(json.dumps(data,sort_keys=True)+"\n");print("PUBLIC SUMMARY PASS",digest(dest));return
    live=collect(f)
    for name in ("ppa","workloads","gate","extra"):
        assert live[name]==load("results/"+name+".json"),"Changed server evidence: "+name
    groups=live["workloads"];local=load("results/functional.json")
    assert groups["worst"]["tb_kwt_precision"]["layers"]==local["four_row"]["nice_cycles"]
    assert groups["class_03"]["tb_kwt_precision"]["layers"]==local["refill_case_class03"]["nice_cycles"]
    n=sum(groups["class_%02d"%i]["tb_kwt_precision"]["cycles"] for i in range(12))
    acc=load("results/accuracy.json");cases=load("results/accuracy_cases.json")
    assert len(cases)==600 and sum(len(v["layer_nrmse"]) for v in cases)==7200
    assert all(math.isfinite(v) and v>=0 for c in cases for v in c["layer_nrmse"])
    assert acc["max_layer_nrmse"]<=.0015 and acc["cases_over_3_percent"]==0
    assert digest(ROOT/"py/profile42.json")==acc["profile_sha256"] and digest(ROOT/"py/rice.py")==acc["rice_sha256"]
    assert load("results/driver.json")["software_frames"]==336 and load("results/driver.json")["actual_xsim_frames"]==12
    assert len(load("results/training_samples.json"))==33
    rel=load("releases/verification.json")
    assert rel["mapped_sha256"]==live["ppa"]["mapped_sha256"] and rel["vcs_suites"]==live["vcs_suites"]
    print("ACCEPT PASS %d VCS suites, 7200 float cases, two SDF matrices; class=%.2f tasks/s, worst=%.2f tasks/s at 150 MHz"%
        (live["vcs_suites"],21600000000./n,1800000000./groups["worst"]["tb_kwt_precision"]["cycles"]),flush=True)
if __name__=="__main__":
    cli=argparse.ArgumentParser();cli.add_argument("action",choices=("acceptance","collect"));main(cli.parse_args().action)
