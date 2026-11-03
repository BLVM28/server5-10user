"""Measure the legacy raw NICE window without touching the frozen v3.1 tree."""
import importlib.util
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/"v3.1"
V2=ROOT.parent/"v2"

def main():
    ref=ROOT/"build/v31_reference"
    for folder in ("rtl","tb"):(ref/folder).mkdir(parents=True,exist_ok=True)
    shutil.copyfile(OLD/"rtl.f",ref/"rtl.f")
    for p in (OLD/"rtl").glob("*.sv"):shutil.copyfile(p,ref/"rtl"/p.name)
    shutil.copyfile(OLD/"tb/kwt_sram_sim.sv",ref/"tb/kwt_sram_sim.sv")
    text=(OLD/"tb/tb_kwt_system.sv").read_text(encoding="utf-8")
    for old,new in (
        ("module tb_kwt_system;","module tb_kwt_system;\n  time launched;integer nice_cycles;"),
        ('@(posedge nice_clk);if(!nice_req_ready)$fatal(1,"NICE not ready");',
         '@(posedge nice_clk);launched=$time;if(!nice_req_ready)$fatal(1,"NICE not ready");'),
        ("wait(nice_rsp_valid);@(negedge nice_clk);","wait(nice_rsp_valid);nice_cycles=($time-launched)/10;@(negedge nice_clk);"),
        ("      check_mac=0;tests=tests+1;","      $display(\"NICE_TIME layer=%0d cycles=%0d reads=11624 writes=%0d compact=0\",layer,nice_cycles,write_acks-start_writes);\n      check_mac=0;tests=tests+1;")):
        if text.count(old)!=1:raise ValueError("Review the changed v3.1 testbench")
        text=text.replace(old,new)
    (ref/"tb/tb_kwt_system.sv").write_bytes(text.encode("utf-8"))
    spec=importlib.util.spec_from_file_location("xsim_old",V2/"py/run_xsim.py")
    driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    driver.ROOT=ref
    sys.argv+=["--tag","paired","--vectors",str(V2/"vec/real_speech/worst"),"--tops","tb_kwt_system"]
    driver.main()

if __name__=="__main__":main()
