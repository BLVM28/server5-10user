"""Collect fresh source-bound server evidence without exporting foundry IP."""
import argparse,json,math,re
from pathlib import Path
from qualify import ROOT,digest,load_flow,implementation_sources
from snapshot import validate
from daily import record
from scalar_vectors import LABELS
def read(p):return json.loads((ROOT/p).read_text())
def collect():
    f=load_flow();core=ROOT/"implementation/rebuilt/synth_kwt_nice_core"
    q=validate(core,implementation_sources())
    ppa={k:v for k,v in q.items() if k!="points"}
    ppa["points"]=[{k:v for k,v in p.items() if k!="coverage"} for p in q["points"]]
    ppa["macros"]={"RAMSP1024X16":8,"RAMSP128X16":64}
    workloads={};suites=0
    for label in LABELS:
        modes={}
        for top in ("tb_kwt_streams","tb_kwt_wait"):
            row=record(f,top,label);rows=row["nice_cycles"][:12];n=sum(v["cycles"] for v in rows)
            modes[top]={"cycles":n,"tasks_s_at_150":1800000000./n,"layers":rows,"log_sha256":row["log_sha256"]}
            suites+=1
        workloads[label]=modes
    extra={}
    for top in ("tb_kwt_zero","tb_kwt_public_sram"):
        row=record(f,top,"worst");extra[top]=row["nice_cycles"][:12];suites+=1
    paired=read("reports/paired_v42.json")
    gates=[];power=[]
    for version,corner in (("v42","ss"),("v43","ss"),("v43","ff")):
        p=ROOT/("build/power/%s_%s_layer00/verified.json"%(version,corner))
        row=json.loads(p.read_text());assert row["passed"]
        if version=="v43":assert row["netlist_sha256"]==q["mapped_sha256"]
        gates.append({k:v for k,v in row.items() if k not in ("raw_power_attributes","power_report","power_units","activity_report")})
        if "vcd_sha256" in row:power.append(row)
    assert suites==30
    result={"ppa":ppa,"workloads":workloads,"extra":extra,"paired_v42":paired,"gate":gates,"power":power,"vcs_suites":suites}
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument("action",choices=("collect","acceptance"));a=p.parse_args()
    report=collect()
    if a.action=="collect":
        (ROOT/"reports/public.json").write_text(json.dumps(report,sort_keys=True)+"\n")
        print("PUBLIC SUMMARY PASS",digest(ROOT/"reports/public.json"));return
    for name in ("ppa","workloads","extra","paired_v42","gate","power"):
        assert report[name]==read("results/"+name+".json"),"Changed "+name
    local=read("results/functional.json");assert local["passed"]
    assert report["extra"]["tb_kwt_public_sram"]==local["matrices"][:12]
    assert report["workloads"]["worst"]["tb_kwt_streams"]["cycles"]==local["total_12_cycles"]
    assert report["ppa"]["v43_area"]<2250000
    ss=next(p for p in report["ppa"]["points"] if p["corner"]=="ss" and abs(p["period_ns"]-6.666667)<1e-7)
    assert ss["timing_pass"] and ss["setup_hold_ns"][0]>=0.5
    acc=read("results/accuracy.json")
    assert acc["samples"]==600 and acc["max_layer_nrmse"]<=.0015 and acc["cases_over_3_percent"]==0
    assert read("results/driver.json")["actual_xsim_frames"]==12
    assert read("results/rv32.json")["object"]=="elf32-littleriscv"
    assert len(report["power"])>=2
    print("ACCEPTANCE PASS: 30 VCS suites, same-source two-corner 150 MHz + SS margin, 600-sample Dense1 accuracy, software, SDF and scoped power")
if __name__=="__main__":main()
