from pathlib import Path
import subprocess,json,hashlib
root=Path(__file__).resolve().parents[1];out=root/"build/wrapper";out.mkdir(exist_ok=True)
bin=Path("D:/vivado/Vivado/2023.2/bin")
src=[root/p for p in (root/"rtl.f").read_text().splitlines() if p.strip()]
src += [root/"tb/kwt_sram_sim.sv",root/"integration/e203_subsys_nice_core.v"]
(out/"sources.f").write_text("\n".join('"'+str(p).replace("\\","/")+'"' for p in src)+"\n")
def run(tool,args,name):
    cmd=["cmd","/d","/c",str(bin/(tool+".bat"))]+args
    p=subprocess.run(cmd,cwd=out,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/(name+".log")).write_bytes(p.stdout)
    if p.returncode:raise RuntimeError(p.stdout.decode(errors="replace")[-3500:])
run("xvlog",["-sv","-i",str(root/"integration/upstream"),"-f","sources.f"],"compile")
run("xelab",["work.e203_subsys_nice_core","-s","wrapper_sim","-timescale","1ns/1ps"],"elaborate")
proof={"wrapper_linked":True,"public_defines_sha256":hashlib.sha256((root/"integration/upstream/e203_defines.v").read_bytes()).hexdigest(),"wrapper_sha256":hashlib.sha256(src[-1].read_bytes()).hexdigest(),"elaboration_log_sha256":hashlib.sha256((out/"elaborate.log").read_bytes()).hexdigest()}
(root/"results/conformance.json").write_text(json.dumps(proof,indent=2)+"\n")
print("WRAPPER LINK PASS")
