"""Derive Block8 transport and scoreboards from the pinned raw X/W/b files without modifying the reference."""
import hashlib,json
from pathlib import Path
import numpy as np
from block8 import int16_pairs,read_words,memory

ROOT=Path(__file__).resolve().parents[1]
NAMES=["base"]+["class_%02d"%i for i in range(12)]+["worst"]
def emit(p,data,bits):
    mask=(1<<bits)-1
    p.write_bytes("".join(("%0*x\n"%(bits//4,int(x)&mask)) for x in np.asarray(data).ravel()).encode("ascii"))
def pairs(y):
    a=np.asarray(y,dtype=np.int64).ravel()&65535
    return a[::2]|a[1::2]<<16
def generate():
    base=ROOT.parent/"v2/vec"
    pinned=json.loads((ROOT/"py/vector_manifest.json").read_text())
    for name in NAMES:
        src=base if name=="base" else base/"real_speech"/name
        out=ROOT/"vec/fast"/name;out.mkdir(parents=True,exist_ok=True)
        sats=[]
        for i in range(12):
            stem="layer%02d_"%i
            def load(k):
                p=src/(stem+k+".hex")
                assert hashlib.sha256(p.read_bytes()).hexdigest()==pinned[p.relative_to(base).as_posix()]
                return read_words(p)
            x=int16_pairs(load("x")).reshape(99,64);w=int16_pairs(load("w")).reshape(64,256)
            b=(load("b")^0x80000000)-0x80000000
            px,pw,pb,a,y,py,decoded,sat=memory(x,w,b)
            for k,values,bits in [("x",px,32),("w",pw,32),("b",pb,32),("acc",a,40),("y",pairs(y),32),
                                   ("wire",py,32),("decoded",pairs(decoded),32)]:
                emit(out/(stem+k+".hex"),values,bits)
            sats.append(sat)
        emit(out/"matrix_sat.hex",sats,32)
        print("VECTORS",name,flush=True)
    files={p.relative_to(ROOT/"vec").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/"vec/fast").rglob("*.hex"))}
    print("FAST VECTOR PASS",len(files),hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest())
    return files
if __name__=="__main__":generate()
