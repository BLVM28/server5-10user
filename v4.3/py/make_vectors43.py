"""Produce all wire and arithmetic scoreboards from pinned v2 inputs."""
import hashlib,json
from pathlib import Path
import numpy as np
from block8 import read_words,int16_pairs
from streams43 import frame
ROOT=Path(__file__).resolve().parents[1]
LABELS=["base"]+["class_%02d"%i for i in range(12)]+["worst"]
def pairs(a):
    v=np.asarray(a,dtype=np.int64).ravel()&65535
    return v[::2]|(v[1::2]<<16)
def emit(p,data,bits=32):
    p.write_bytes("".join("%0*x\n"%(bits//4,int(v)&((1<<bits)-1)) for v in np.asarray(data).ravel()).encode())
def main():
    base=ROOT.parent/"v2/vec";pinned=json.loads((ROOT/"py/vector_manifest.json").read_bytes())
    profiles=json.loads((ROOT/"py/profile42.json").read_bytes())["profiles"]
    for label in LABELS:
        src=base if label=="base" else base/"real_speech"/label
        out=ROOT/"vec/streams"/label;out.mkdir(parents=True,exist_ok=True)
        sats=[];reads=[];writes=[];params=[]
        for i,p in enumerate(profiles):
            stem="layer%02d_"%i
            def load(k):
                f=src/(stem+k+".hex");assert hashlib.sha256(f.read_bytes()).hexdigest()==pinned[f.relative_to(base).as_posix()]
                return read_words(f)
            x=int16_pairs(load("x")).reshape(99,64);w=int16_pairs(load("w")).reshape(64,256)
            b=(load("b")^0x80000000)-0x80000000
            px,pw,b,acc,y,wire,decoded,sat,nread,groups=frame(x,w,b,p)
            for k,v,bits in (("x",px,32),("w",pw,32),("b",b,32),("acc",acc,40),("y",pairs(y),32),
                    ("wire",wire,32),("decoded",pairs(decoded),32),("groups",groups,16)):emit(out/(stem+k+".hex"),v,bits)
            # The new transport must preserve every numerical value of v4.2.
            prev=ROOT.parent/"v4.2/vec/precision"/label
            assert np.array_equal(read_words(prev/(stem+"decoded.hex")),pairs(decoded))
            assert np.array_equal(read_words(prev/(stem+"acc.hex")),np.asarray(acc).ravel()&((1<<40)-1))
            sats.append(sat);reads.append(nread);writes.append(sum(groups))
            sx,sw,sy=p["shifts"];params.append(sx|sw<<4|sy<<8)
        for k,v in (("matrix_sat",sats),("reads",reads),("writes",writes),("params",params)):emit(out/(k+".hex"),v)
        print("STREAM VECTORS",label,sum(reads),sum(writes),flush=True)
    files={f.relative_to(ROOT/"vec").as_posix():hashlib.sha256(f.read_bytes()).hexdigest()
           for f in sorted((ROOT/"vec/streams").rglob("*.hex"))}
    assert len(files)==1400
    (ROOT/"py/stream_manifest.json").write_bytes((json.dumps(files,sort_keys=True,indent=2)+"\n").encode())
if __name__=="__main__":main()
