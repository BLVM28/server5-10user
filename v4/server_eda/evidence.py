"""Cross-check public receipts against the current server-private simulation and STA evidence."""
import argparse
import json
from pathlib import Path
import re
from qualify import ROOT,HOME,digest,load_flow,implementation_sources
from snapshot import validate
from daily import COUNTS,report

PERIOD=6.666667
LABELS=["class_%02d"%i for i in range(12)]+["worst"]

def ppa():
    core=ROOT/"implementation/rebuilt/synth_kwt_nice_core"
    q=validate(core,implementation_sources())
    rows=[[p["period_ns"],p["corner"],*p["setup_hold_ns"],len(p["reported_violations"])] for p in q["points"]]
    return {"mapped_sha256":q["mapped_sha256"],"qualification_sha256":digest(core/"qualification.json"),
            "map_period_ns":q["mapped_period_ns"],"total_cell_area":q["v4_area"],"macro_area":q["macro_area"],
            "v31_area":q["v31_reference_area"],"resized":len(q["resize_changes"]),"points":rows}

def record(flow,label,top,vec):
    run=flow.OUT/"runs"/label/top
    j=json.loads((run/"verified.json").read_text())
    count=COUNTS[top]
    assert j["passed"] and j["counts"]==[[str(count),str(count)]]
    assert j["rtl_sha256"]==flow.source_hashes() and digest(run/"run.log")==j["log_sha256"]
    assert Path(j["vector_dir"]).resolve()==vec.resolve()
    assert j["vectors_sha256"]=={p.name:digest(p) for p in vec.glob("*.hex")}
    assert json.loads((flow.OUT/"compile"/top/"signature.json").read_text())==flow.signature(top)
    return j

def speech(flow):
    output={}
    software=json.loads((ROOT/"results/codec.json").read_text())
    for name in LABELS+["base"]:
        vec=ROOT/"vec" if name=="base" else ROOT/"vec/real_speech"/name
        label="default" if name=="base" else name
        entries=[]
        for top in ("tb_kwt_system","tb_kwt_compact"):
            j=record(flow,label,top,vec);rows=j["nice_cycles"]
            assert len(rows)==14 and [x["layer"] for x in rows[:12]]==list(range(12))
            for m in rows:
                expected=software["matrices"][name][m["layer"]]["physical_writes"] if top=="tb_kwt_compact" else 12672
                assert m["reads"]==11624 and m["writes"]==expected
            entries.extend([sum(x["cycles"] for x in rows[:12]),sum(x["writes"] for x in rows[:12])])
        output[name]=entries
    return output

def matches(rel,value):
    if json.loads((ROOT/rel).read_text())!=value:raise ValueError("Published numbers differ: "+rel)

def checks(flow):
    report(flow,"rebuilt",PERIOD,ROOT/"vec")
    info=ppa()
    matches("results/ppa.json",info)
    stats=speech(flow)
    matches("results/speech.json",stats)
    numeric=json.loads((ROOT/"results/numeric.json").read_text())
    assert numeric["model_sha256"]==digest(ROOT/"py/numeric_model.py")==digest(ROOT.parent/"v2/py/numeric_model.py")
    assert numeric["vector_manifest_sha256"]==digest(ROOT/"py/vector_manifest.json")
    assert numeric["tasks_by_set"]=={name:12 for name in LABELS+["base"]}
    assert numeric["tasks"]==numeric["saturation_counters"]==168 and numeric["acc40_elements"]==numeric["int16_elements"]==4257792
    local=json.loads((ROOT/"results/functional.json").read_text())
    for name,top in (("v4_raw","tb_kwt_system"),("v4_packed","tb_kwt_compact")):
        j=record(flow,"worst",top,ROOT/"vec/real_speech/worst")
        assert local["paired"][name]["nice"]==[x["cycles"] for x in j["nice_cycles"][:12]]
    record(flow,"waves","tb_kwt_system",ROOT/"vec")
    assert (flow.OUT/"runs/waves/tb_kwt_system/waves.vcd").stat().st_size
    fast=ROOT/"build/fast_return/run"
    immediate=json.loads((fast/"verified.json").read_text())
    assert immediate["passed"] and immediate["rtl"]==flow.source_hashes()
    assert immediate["signature"]==flow.signature("tb_kwt_fast_return") and digest(fast/"run.log")==immediate["log_sha256"]
    gate=json.loads((ROOT/"build/gate_sample/sample.json").read_text())
    released={p["corner"]:p for p in json.loads((ROOT/"results/gate.json").read_text())}
    assert set(released)=={"ss","ff"}
    assert {p["corner"] for p in gate}=={"ss","ff"} and len(gate)==2
    for point in gate:
        c=point["corner"]; assert point["layer"]==0 and point["writes"]==local["paired"]["v4_packed"]["writes"][0]
        assert point["transactions"]==11624+point["writes"]
        assert point["netlist_sha256"]==info["mapped_sha256"]
        # Fresh SDFs and simulator logs include run dates. Compare their live
        # hashes below and match the deterministic result to the release.
        assert all(point[k]==released[c][k] for k in ("corner","layer","transactions","writes","netlist_sha256"))
        d=ROOT/"build/gate_sample"
        assert digest(d/"timing/rebuilt"/str(PERIOD)/("kwt_nice_core_"+c)/"mapped.sdf")==point["sdf_sha256"]
        assert digest(d/"gate/rebuilt"/str(PERIOD)/("worst_"+c)/"packed_layer00/run.log")==point["log_sha256"]
        ann=(d/"gate/rebuilt"/str(PERIOD)/("worst_"+c)/"annotation_probe/sdf_annotation.log").read_text()
        assert all(re.search(r"Total "+k+r":\s*0\b",ann) for k in ("errors","warnings"))
    expected={"rtl_suites":COUNTS,"extended_suites":35,"same_edge_matrix":True,"activation_sets":LABELS,"paired_packed_nice":stats["worst"][2],
              "packed_gate_layers":{"ss":[0],"ff":[0]},"gate_tb_sha256":digest(ROOT/"server_eda/tb_core_all_gate.sv"),
              "mapped_sha256":info["mapped_sha256"]}
    matches("releases/verification.json",expected)
    assert 12*150000000>1000*stats["worst"][2], "1000 tasks/s not reached"
    class_cycles=[stats[name][2] for name in LABELS if name!="worst"]
    assert all(12*150000000>1000*cycles for cycles in class_cycles), "Under 1000 tasks/s on a class representative"
    classes=[1800000000.0/cycles for cycles in class_cycles]
    aggregate=150000000.0*12*len(class_cycles)/sum(class_cycles)
    print("150 MHz NICE tasks/s: paired packed %.2f, raw %.2f; 144 class tasks %.2f, range %.2f .. %.2f; synthetic base %.2f" %
          (1800000000.0/stats["worst"][2],1800000000.0/stats["worst"][0],aggregate,min(classes),max(classes),1800000000.0/stats["base"][2]))
    print("EXTENDED ACCEPT PASS: 35 suites, packed SDF layer 0 SS/FF, 150 MHz throughput verified")

def main():
    if ROOT!=HOME/"v4":raise ValueError("Read the actual server project")
    ap=argparse.ArgumentParser();ap.add_argument("action",choices=("ppa","speech","acceptance"))
    args=ap.parse_args();flow=load_flow()
    if args.action=="acceptance":checks(flow)
    elif args.action=="speech":
        for name,n in speech(flow).items():print(name,*n)
    else:
        info=ppa()
        for k,v in info.items():
            if k.endswith("sha256"):print(k," ".join(v[i:i+8] for i in range(0,64,8)))
            elif k!="points":print(k,v)
        for row in info["points"]:print(*row)
if __name__=="__main__":main()
