"""Generate frozen transport inputs and all independent numeric / wire scoreboards."""
import hashlib,json
from pathlib import Path
import numpy as np
from block8 import int16_pairs,read_words
from rice import memory,X_WORDS
ROOT=Path(__file__).resolve().parents[1]
LABELS=["base"]+["class_%02d"%i for i in range(12)]+["worst"]
def emit(path,data,bits):
    mask=(1<<bits)-1
    path.write_bytes("".join(("%0*x\n"%(bits//4,int(x)&mask)) for x in np.asarray(data).ravel()).encode())
def pairs(y):
    y=np.asarray(y,dtype=np.int64).ravel()&65535
    return y[::2]|(y[1::2]<<16)
def main():
    raw=ROOT.parent/"v2/vec";pinned=json.loads((ROOT/"py/vector_manifest.json").read_text())
    profiles=json.loads((ROOT/"py/profile42.json").read_text())["profiles"]
    for label in LABELS:
        src=raw if label=="base" else raw/"real_speech"/label
        out=ROOT/"vec/precision"/label;out.mkdir(parents=True,exist_ok=True)
        satcounts=[];reads=[];writes=[];params=[]
        for i,profile in enumerate(profiles):
            stem="layer%02d_"%i
            def load(k):
                path=src/(stem+k+".hex")
                assert hashlib.sha256(path.read_bytes()).hexdigest()==pinned[path.relative_to(raw).as_posix()]
                return read_words(path)
            x=int16_pairs(load("x")).reshape(99,64);w=int16_pairs(load("w")).reshape(64,256);b=(load("b")^0x80000000)-0x80000000
            px,pw,_,acc,y,wire,decoded,sat,nread,groupwords=memory(x,w,b,profile)
            px=px+[0]*(X_WORDS-len(px))
            for k,v,bits in [("x",px,32),("w",pw,32),("b",b,32),("acc",acc,40),("y",pairs(y),32),("wire",wire,32),("decoded",pairs(decoded),32),("groups",groupwords,16)]:
                emit(out/(stem+k+".hex"),v,bits)
            satcounts.append(sat);reads.append(nread);writes.append(sum(groupwords))
            sx,sw,sy=profile["shifts"];params.append(sx|(sw<<4)|(sy<<8))
        for k,d in (("matrix_sat",satcounts),("reads",reads),("writes",writes),("params",params)):emit(out/(k+".hex"),d,32)
        print("PRECISION VECTORS",label,sum(reads),sum(writes),flush=True)
    files={p.relative_to(ROOT/"vec").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/"vec/precision").rglob("*.hex"))}
    assert len(files)==1400
    (ROOT/"py/precision_manifest.json").write_bytes((json.dumps(files,sort_keys=True,indent=2)+"\n").encode())
if __name__=="__main__":main()
