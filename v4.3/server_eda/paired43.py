"""Compare frozen v4.2 and v4.3 against the exact public E203 SRAM controller.
The backing shared RAM is a synchronous functional array, outside measured DUT
power. No E203 CPU, 512 KiB shared RAM or place/route power is included.
"""
import argparse,hashlib,importlib.util,json,re,shutil,sys
from pathlib import Path
from qualify import ROOT,HOME,TOP,digest,load_flow
UP=("sirv_sram_icb_ctrl.v","sirv_1cyc_sram_ctrl.v","sirv_gnrl_bufs.v","sirv_gnrl_dffs.v","e203_clkgate.v","GENERIC_RVT_SMIC.v")
PERIOD=6.666667
def sources():
    return [ROOT/"integration/upstream"/p for p in UP]
def compile_public(flow):
    top="tb_kwt_public_sram";d=flow.OUT/"compile"/top
    paths=flow.sources(top);sig={str(p):digest(p) for p in paths}
    sig.update({str(ROOT/"integration/upstream"/p):digest(ROOT/"integration/upstream"/p) for p in ("config.v","e203_defines.v")})
    stamp=d/"signature.json"
    if not (d/"simv").exists() or not stamp.exists() or json.loads(stamp.read_text())!=sig:
        flow.run(["vcs","-full64","-sverilog","-debug_access+all","-timescale=1ns/1ps","-top",top,
          "+define+KWT_USE_FOUNDRY_SRAM+ARM_UD_MODEL+FPGA+DISABLE_SV_ASSERTION",
          "+incdir+"+str(ROOT/"integration/upstream"),*paths,"-o","simv"],d,"compile")
        flow.save(stamp,sig);print("COMPILE PASS",top,flush=True)
    return d/"simv"
def run_reference():
    f=load_flow();d=ROOT/"build/paired/v42_rtl";r=ROOT.parent/"v4.2"
    paths=[r/p.strip() for p in (r/"rtl.f").read_text().splitlines() if p.strip()]
    paths += [f.PUB/m/"verilog"/(m+s) for m in ("RAMSP128X16","RAMSP1024X16") for s in (".v","_rtl.v")]
    paths += sources()+[ROOT/"tb/tb_kwt_v42_reference.sv"]
    f.run(["vcs","-full64","-sverilog","-timescale=1ns/1ps","-top","tb_kwt_v42_reference",
      "+define+KWT_USE_FOUNDRY_SRAM+ARM_UD_MODEL+FPGA+DISABLE_SV_ASSERTION",
      "+incdir+"+str(ROOT/"integration/upstream"),*paths,"-o","simv"],d,"compile")
    vec=r/"vec/precision/worst"
    log=f.run([d/"simv","+PRECISION42","+VEC_DIR="+str(vec)],d,"run","ALL PASS, 12/12")
    rows=[{"layer":int(i),"cycles":int(c)} for i,c in re.findall(r"NICE_TIME layer=(\d+) cycles=(\d+)",log)]
    assert [p["layer"] for p in rows]==list(range(12))
    total=sum(p["cycles"] for p in rows)
    rec={"scope":"v4.2 RTL + exact public SRAM controller, 12 cold tasks",
      "cycles":rows,"total_cycles":total,"tasks_s_at_150":1800000000./total,
      "sources":{str(p):digest(p) for p in paths},"log_sha256":digest(d/"run.log")}
    f.save(ROOT/"reports/paired_v42.json",rec);print("PAIRED V42",total,rec["tasks_s_at_150"],flush=True)
    return rec
def gate_power(version,corner,layer,power):
    assert version in ("v42","v43") and corner in ("ss","ff")
    f=load_flow();r=ROOT if version=="v43" else ROOT.parent/"v4.2"
    net=r/"implementation/rebuilt/synth_kwt_nice_core/mapped.v"
    assert net.exists(),"Run make synth first"
    q=json.loads((net.parent/"qualification.json").read_text());assert q["mapped_sha256"]==digest(net)
    libs=f.libs();d=ROOT/("build/power/%s_%s_layer%02d"%(version,corner,layer))
    env={"KWT_ROOT":str(ROOT),"KWT_TOP":TOP,"KWT_CORNER":corner,"KWT_PERIOD":str(PERIOD),
      "KWT_OUTPUT_CAP":"0.002852","KWT_STD_DB":libs["standard"][corner],
      "KWT_SRAM_DBS":"|".join(libs["sram"][corner]),"KWT_NETLIST":str(net)}
    f.run(["pt_shell","-f",ROOT/"server_eda/manual_sta.tcl"],d,"sta","STA_COMPLETED "+TOP,env)
    assert not re.search("VIOLATED",(d/"violations.rpt").read_text())
    top="tb_kwt_public_sram" if version=="v43" else "tb_kwt_v42_reference"
    benches=[ROOT/"tb/tb_kwt_streams.sv",ROOT/"tb/tb_kwt_public_sram.sv"] if version=="v43" else [ROOT/"tb/tb_kwt_v42_reference.sv"]
    if version=="v43":
        # The mapped top has fixed elaborated parameters, no parameter ports.
        generated=d/"tb_kwt_streams_mapped.sv"
        generated.write_text(benches[0].read_text().replace(
          'kwt_nice_core #(.MEM_BASE(BASE),.MEM_BYTES(BYTES),.PACK_LOW_FIRST(PACK)) dut(.*);',
          'kwt_nice_core dut(.*);'))
        benches[0]=generated
    macros=[f.PUB/m/"verilog"/(m+s) for m in ("RAMSP128X16","RAMSP1024X16") for s in (".v","_rtl.v")]
    defs=["+define+KWT_GATE+FPGA+DISABLE_SV_ASSERTION+KWT_PERIOD_NS="+str(PERIOD)]
    if corner=="ff":defs.append("+define+KWT_SDF_MIN")
    f.run(["vcs","-full64","-sverilog","+neg_tchk","-sdfretain","-timescale=1ns/1ps","-top",top,
      *defs,"+incdir+"+str(ROOT/"integration/upstream"),libs["standard_verilog"],
      *macros,*sources(),net,*benches,"-o","simv"],d,"compile")
    ann=(d/"sdf_annotation.log").read_text()
    for key in ("errors","warnings"):
        match=re.search(r"Total "+key+r":\s*(\d+)",ann);assert match and int(match.group(1))==0,ann[-1500:]
    vec=r/("vec/streams/worst" if version=="v43" else "vec/precision/worst")
    args=[d/"simv","+sdfverbose","+LAYER="+str(layer),"+VEC_DIR="+str(vec)]
    if version=="v42":args.append("+PRECISION42")
    if power:args.append("+POWER")
    log=f.run(args,d,"run","ALL PASS, 1/1",timeout=3600)
    assert re.search(r"Doing SDF annotation[^\r\n]*Done",log)
    rec={"version":version,"corner":corner,"layer":layer,"netlist_sha256":digest(net),
      "sdf_sha256":digest(d/"mapped.sdf"),"annotation_sha256":digest(d/"sdf_annotation.log"),
      "run_log_sha256":digest(d/"run.log"),"passed":True,"power_scope":"accelerator incl. local SRAM, excluding CPU/shared512KiB/interconnect/physical"}
    match=re.search(r"NICE_TIME layer=\d+ cycles=(\d+)",log);assert match
    rec["cycles"]=int(match.group(1));rec["duration_ns"]=int(match.group(1))*PERIOD
    if power:
        vcd=d/"task.vcd";assert vcd.stat().st_size>100000
        env.update({"KWT_VCD":str(vcd),"KWT_STRIP_PATH":top+("/test/dut" if version=="v43" else "/dut")})
        f.run(["pt_shell","-f",ROOT/"server_eda/power.tcl"],d/"px","pt","POWER_COMPLETED "+TOP,env)
        rec["vcd_sha256"]=digest(vcd)
        rec["raw_power_attributes"]=(d/"px/power_attributes.txt").read_text()
        rec["power_report"]=(d/"px/power.rpt").read_text()
        rec["power_units"]=(d/"px/units.rpt").read_text()
        rec["activity_report"]=(d/"px/switching.rpt").read_text()
    f.save(d/"verified.json",rec);print("GATE/POWER PASS",version,corner,layer,flush=True)
    return rec
def main():
    p=argparse.ArgumentParser();p.add_argument("action",choices=("reference","power","gate"))
    p.add_argument("--version",choices=("v42","v43"),default="v43");p.add_argument("--corner",choices=("ss","ff"),default="ss")
    p.add_argument("--layer",type=int,default=0);a=p.parse_args();assert 0<=a.layer<12
    if a.action=="reference":run_reference()
    else:gate_power(a.version,a.corner,a.layer,a.action=="power")
if __name__=="__main__":main()
