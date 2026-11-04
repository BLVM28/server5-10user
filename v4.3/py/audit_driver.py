"""Compare RV32-format C input frames and every decoded result with an independent model and actual XSim RAM."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
import numpy as np
from block8 import int16_pairs,read_words
from scalar_vectors import LABELS
from profile_header import data as header_data
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(cc):
    out=ROOT/"build/software";out.mkdir(parents=True,exist_ok=True)
    exe=out/"streams_probe.exe";header=ROOT/"integration/kwt_v42_profile.h"
    assert header.read_bytes()==header_data()
    subprocess.run([cc,"-std=c11","-O2","-Wall","-Wextra","-Werror",str(ROOT/"integration/streams_probe.c"),"-o",str(exe)],check=True)
    captures={};n=0
    with subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE) as proc:
        for label in LABELS:
            src=ROOT.parent/"v2/vec"
            if label!="base":src=src/"real_speech"/label
            vec=ROOT/"vec/streams"/label
            for i in range(12):
                stem="layer%02d_"%i
                signed=[int16_pairs(read_words(src/(stem+k+".hex"))).astype("<i2").tobytes() for k in ("x","w")]
                blocks=[read_words(vec/(stem+k+".hex")) for k in ("x","w","wire")]
                expected=int16_pairs(read_words(vec/(stem+"decoded.hex"))).astype("<i2").tobytes()
                def send(order,physical):
                    frame=struct.pack("<II",i,order)+b"".join(signed)
                    proc.stdin.write(frame+b"".join(p.astype("<u4").tobytes() for p in physical)+expected)
                send(1,blocks);send(0,[((p<<16)|(p>>16))&0xffffffff for p in blocks]);n+=2
                if label=="worst":
                    path=ROOT/"build/public_full"/("streams_layer%02d.hex"%i)
                    mem=np.array([int(x,16) for x in path.read_text().splitlines() if re.fullmatch("[0-9A-Fa-f]{8}",x.strip())])
                    assert len(mem)==16384 and np.array_equal(mem,blocks[2])
                    send(1,[blocks[0],blocks[1],mem]);captures[str(i)]=sha(path);n+=1
        proc.stdin.close();message=proc.stdout.read().decode().strip()
        assert proc.wait()==0 and n==348 and message=="C STREAMS PASS 348 frames",message
    j={"host":message,"software_frames":336,"actual_xsim_frames":12,"ram_capture_sha256":captures,
       "header_sha256":sha(ROOT/"integration/kwt_v43_streams.h"),"profile_sha256":sha(header)}
    (ROOT/"results/driver.json").write_bytes((json.dumps(j,indent=2)+"\n").encode())
    print(message,flush=True)
if __name__=="__main__":
    cli=argparse.ArgumentParser();cli.add_argument("--cc",default="gcc");main(cli.parse_args().cc)
