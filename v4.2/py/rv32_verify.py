"""Cross-compile the driver and inspect the actual RV32 custom instruction fields."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(prefix):
    flags="-march=rv32imac -mabi=ilp32 -ffreestanding -std=c11 -O2 -Wall -Wextra -Werror".split()
    source=ROOT/"integration/precision_rv32_probe.c";out=ROOT/"build/software";out.mkdir(parents=True,exist_ok=True)
    obj=out/"precision_rv32.o"
    subprocess.run([prefix+"gcc",*flags,"-c",str(source),"-o",str(obj)],check=True)
    asm=subprocess.check_output([prefix+"objdump","-dr",str(obj)]).decode()
    (out/"precision_rv32.lst").write_text(asm)
    matches=[int(v,16) for v in re.findall(r"^\s*[0-9a-f]+:\s+([0-9a-f]{8})\s",asm,re.M)
             if (int(v,16)&0xfff0707f)==0x8000607b]
    assert "elf32-littleriscv" in asm and len(matches)==1
    j={"compiler":subprocess.check_output([prefix+"gcc","-dumpfullversion"]).decode().strip(),
       "flags":" ".join(flags),"object":"elf32-littleriscv","custom_word":"%08x"%matches[0],
       "source_sha256":sha(source),"object_sha256":sha(obj),"driver_sha256":sha(ROOT/"integration/kwt_v42_precision.h")}
    (ROOT/"results/rv32.json").write_bytes((json.dumps(j,indent=2)+"\n").encode());print("RV32 PASS",j["custom_word"])
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("prefix",nargs="?",default="riscv-none-elf-");run(ap.parse_args().prefix)
