from pathlib import Path
import json,sys
soc=Path.cwd()/"soc"
sys.path.insert(0,str(soc/"flow"))
from prepare import FLOW,digest
from path_config import load_paths
from regression import invoke
run=Path(sys.argv[1]).resolve()
work=run/"v44_mapped_direct_engine"
work.mkdir()
s=(soc/"tb/tb_soc_boot.sv").read_text()
a=s.index(chr(96)+"ifdef GATE_LEVEL")
b=s.index("  task automatic itcm_write",a)
s=s[:a]+s[b:]
s=s.replace("  reg [15:0] groups[0:63];","  reg [15:0] groups[0:63];\n  reg [31:0] direct_params[0:11];")
s=s.replace("    batch_load=$test","    $readmemh({vector_dir,\"/params.hex\"},direct_params);\n    batch_load=$test",1)
a=s.index("      store_word(32'ha0000020,layer)")
b=s.index("      checked=0;",a)
s=s[:a]+"""      store_word(32'ha0000200,32'h3154574b);
      store_word(32'ha0000204,32'h10004);
      store_word(32'ha0000208,layer);
      store_word(32'ha000020c,XBASE);
      store_word(32'ha0000210,WBASE);
      store_word(32'ha0000214,BBASE);
      store_word(32'ha0000218,YBASE);
      store_word(32'ha000021c,direct_params[layer]);
      store_word(32'ha0080000,32'ha0000200);
      do begin
        repeat(100)@(negedge clk);
        read_word(32'ha0080004,observed);
      end while(observed[31]===1'b1);
      if(observed!==0)$fatal(1,"Direct engine task failed layer=%0d status=%h",layer,observed);
"""+s[b:]
s=s.replace("SOC_EXECUTION_ALL_PASS","V44_CORE_GATE_DIRECT_PASS")
tb=work/"tb_soc_boot.sv"
tb.write_text(s)
plan=json.loads((soc/"work/design/plan.json").read_text())
for model in plan["models"]:
    if digest(Path(model))!=plan["sha256"][model]: raise RuntimeError("Changed model "+model)
paths=load_paths(FLOW/"paths.tcl")
sim=work/"simv"
command=[paths["VCS"],"-full64","-sverilog","-timescale=1ns/1ps","-top","tb_soc_boot",
         "+define+GATE_LEVEL+functional+ARM_UD_MODEL",
         "+incdir+"+str(Path(paths["OFFICIAL"])/"core"),str(tb),str(run/"netlist/soc_mapped.v")]+plan["models"]+["-o",str(sim)]
invoke(command,work,"compile.log",3600)
invoke([str(sim),"+VEC_DIR="+paths["VECTOR_PATH"],"+FIRMWARE="+str(soc/"firmware/firmware.hex")],work,"run.log",14400)
report=(work/"run.log").read_text(errors="replace")
marker="V44_CORE_GATE_DIRECT_PASS tasks=12 checked_words=58547 boots=2"
if marker not in report or "Fatal:" in report: raise RuntimeError("Direct mapped engine failed: "+str(work/"run.log"))
print(marker,digest(work/"run.log"),flush=True)

