"""Compile the host C packers/decoder and replay golden plus actual recorded ICB memory."""
import argparse,hashlib,json,re,subprocess,struct
from pathlib import Path
import numpy as np
from block8 import read_words,int16_pairs
from scalar_vectors import LABELS
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(cc):
    d=ROOT/"build/software";d.mkdir(parents=True,exist_ok=True)
    exe=d/"block8_probe.exe"
    subprocess.run([cc,"-std=c11","-Wall","-Wextra","-Werror","-O2",str(ROOT/"integration/block8_probe.c"),"-o",str(exe)],check=True)
    dump=ROOT/"build/immediate";captures={};count=0
    with subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE) as c:
        for label in LABELS:
            raw=ROOT.parent/"v2/vec"
            if label!="base":raw=raw/"real_speech"/label
            fast=ROOT/"vec/fast"/label
            for l in range(12):
                stem="layer%02d_"%l
                data=[int16_pairs(read_words(raw/(stem+k+".hex"))) for k in ("x","w")]
                blocks=[read_words(fast/(stem+k+".hex")) for k in ("x","w","wire")]
                expect=int16_pairs(read_words(fast/(stem+"decoded.hex")))
                def send(order,words):
                    frame=struct.pack("<I",order)+b"".join(a.astype("<i2").tobytes() for a in data)
                    frame+=b"".join(a.astype("<u4").tobytes() for a in words)+expect.astype("<i2").tobytes()
                    c.stdin.write(frame)
                send(1,blocks);send(0,[((p>>16)|(p<<16))&0xffffffff for p in blocks]);count+=2
                if label=="worst":
                    path=dump/("block8_layer%02d.hex"%l)
                    mem=np.array([int(x,16) for x in path.read_text().splitlines() if re.fullmatch("[0-9a-fA-F]{8}",x.strip())],dtype=np.int64)
                    assert len(mem)==6752 and np.array_equal(mem,blocks[2])
                    send(1,[blocks[0],blocks[1],mem]);captures[str(l)]=sha(path);count+=1
        c.stdin.close();out=c.stdout.read().decode().strip()
        assert c.wait()==0 and out=="C BLOCK8 PASS 348 frames" and count==348,out
    r={"host":out,"software_frames":336,"actual_dut_frames":12,"capture_sha256":captures,
       "c_header_sha256":sha(ROOT/"integration/kwt_v41_block8.h")}
    (ROOT/"results/driver.json").write_bytes((json.dumps(r,indent=2)+"\n").encode())
    print(out)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--cc",default="gcc");main(p.parse_args().cc)
