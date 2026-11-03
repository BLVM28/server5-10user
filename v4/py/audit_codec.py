"""Round trip every reference output through the Python and C decoders in both orders."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
from codec import encode,decode,signed

ROOT=Path(__file__).resolve().parents[1]
def audit(cc):
    work=ROOT/"build/software"
    work.mkdir(parents=True,exist_ok=True)
    program=work/("codec_probe.exe" if sys.platform=="win32" else "codec_probe")
    subprocess.run([cc,"-std=c11","-Wall","-Wextra","-Werror","-O2",str(ROOT/"integration/codec_probe.c"),"-o",str(program)],check=True)
    sets=[("base",ROOT.parent/"v2/vec")]+[(name,ROOT.parent/"v2/vec/real_speech"/name)
          for name in ["class_%02d"%i for i in range(12)]+["worst"]]
    stats={};captured=[]
    with subprocess.Popen([str(program)],stdin=subprocess.PIPE,stdout=subprocess.PIPE) as native:
        for label,vec in sets:
            rows=[]
            for layer in range(12):
                gold=(vec/("layer%02d_y.hex"%layer)).read_bytes()
                vals=[signed((a>>s)&65535,16) for a in map(lambda b:int(b,16),gold.split()) for s in (0,16)]
                for order in (True,False):
                    encoded,h=encode(vals,order)
                    if decode(encoded,order)!=vals:raise ValueError((label,layer,order))
                    native.stdin.write(struct.pack("<I12896I25344h",int(order),*encoded,*vals))
                if label=="worst":
                    path=ROOT/"build/export"/("physical_layer%02d.hex"%layer)
                    actual=[int(word,16) for word in path.read_text().split()]
                    reference,_=encode(vals,True)
                    if actual!=reference or decode(actual)!=vals:raise ValueError(("DUT physical memory",layer))
                    native.stdin.write(struct.pack("<I12896I25344h",1,*actual,*vals))
                    captured.append(hashlib.sha256(path.read_bytes()).hexdigest())
                rows.append({"layer":layer,"y_sha256":hashlib.sha256(gold).hexdigest(),"modes":h,
                             "physical_writes":224+sum((i+1)*num for i,num in enumerate(h))})
            stats[label]=rows
        native.stdin.close();out=native.stdout.read().decode().strip()
        if native.wait()!=0 or out!="C DECODE PASS 348 frames":raise ValueError(out)
    inherited=json.loads((ROOT.parent/"v2/validation_real_speech_20261102/report.json").read_text())
    data={"scope":"software encode plus two independent decoders, 14 sets x 12 layers x 2 byte orders",
          "software_frames":336,"actual_dut_frames":12,"captured_sha256":captured,"c_result":out,"matrices":stats,
          "prior_float_baseline":{"samples":inherited["samples"],"maximum_layer_nrmse":inherited["max_layer_nrmse"],
          "source_sha256":hashlib.sha256((ROOT.parent/"v2/validation_real_speech_20261102/report.json").read_bytes()).hexdigest()}}
    (ROOT/"results/codec.json").write_bytes((json.dumps(data,indent=2)+"\n").encode())
    print(out,flush=True)
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--cc",default="gcc")
    audit(parser.parse_args().cc)
