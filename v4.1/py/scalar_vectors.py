"""No NumPy required. Rebuild missing Block8 data with an independent scalar dot/round implementation."""
import hashlib,json,operator
from pathlib import Path
import tempfile
ROOT=Path(__file__).resolve().parents[1]
LABELS=["base"]+["class_%02d"%i for i in range(12)]+["worst"]

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def signed(v,width):
    sign=1<<(width-1)
    return (v^sign)-sign
def block(values):
    highest=max(v if v>=0 else ~v for v in values)
    shift=max(0,highest.bit_length()-7)
    unit=1<<shift
    return shift,[min(127,max(-128,(v+unit//2)//unit)) for v in values]
def pairs(data):
    return [(data[j]&65535)|((data[j+1]&65535)<<16) for j in range(0,len(data),2)]
def octets(data):
    return [sum((data[j+k]&255)<<(8*k) for k in range(4)) for j in range(0,len(data),4)]
def verify(restore=True):
    src=ROOT.parent/"v2/vec";dest=ROOT/"vec"
    gold=json.loads((ROOT/"py/vector_manifest.json").read_text())
    frozen=json.loads((ROOT/"py/fast_manifest.json").read_text())
    assert len(frozen)==1190 and not dest.is_symlink()
    def publish(key,data,bits):
        rel="fast/"+label+"/"+key+".hex";target=dest/rel
        assert dest.resolve() in target.resolve().parents and not target.is_symlink()
        raw="".join(("%0*x\n"%(bits//4,x&((1<<bits)-1))) for x in data).encode("ascii")
        assert hashlib.sha256(raw).hexdigest()==frozen[rel],rel
        if target.exists():
            if digest(target)!=frozen[rel]:raise ValueError("Changed golden file: "+rel)
        else:
            with tempfile.NamedTemporaryFile(dir=str(target.parent),delete=False) as f:f.write(raw)
            Path(f.name).replace(target)
    for label in LABELS:
        folder=dest/"fast"/label
        assert dest.resolve() in folder.resolve().parents and not folder.is_symlink()
        files=[(dest/n,h) for n,h in frozen.items() if n.startswith("fast/"+label+"/")]
        assert len(files)==85
        for p,h in files:
            if p.exists() and digest(p)!=h:raise ValueError("Changed frozen vector: "+str(p))
        if all(p.is_file() for p,h in files):continue
        if not restore:raise ValueError("Missing Block8 vectors: "+label)
        folder.mkdir(parents=True,exist_ok=True)
        input_dir=src if label=="base" else src/"real_speech"/label
        satlist=[]
        for layer in range(12):
            stem="layer%02d_"%layer
            def load(k):
                p=input_dir/(stem+k+".hex");assert digest(p)==gold[p.relative_to(src).as_posix()]
                return [int(x,16) for x in p.read_bytes().splitlines()]
            def halves(words):return [signed(v,16) for w in words for v in (w&65535,w>>16)]
            X=halves(load("x"));W=halves(load("w"));B=[signed(v,32) for v in load("b")]
            px=[];xs=[]
            for row in range(99):
                e,q=block(X[row*64:row*64+64]);px.extend([e]+octets(q));xs.append([v<<e for v in q])
            ws=[];pw=[]
            for g in range(32):
                ex=[];qs=[]
                for c in range(8):
                    e,q=block(W[g*8+c::256]);ex.append(e);qs.append(q);ws.append([v<<e for v in q])
                pw.append(sum(e<<(4*k) for k,e in enumerate(ex)))
                pw.extend(octets([qs[l][k] for k in range(64) for l in range(8)]))
            acc=[];raw_y=[];decoded=[];payload=[];tags=[0]*416;sat=0
            for row,x in enumerate(xs):
                for g in range(32):
                    eight=[]
                    for lane in range(8):
                        col=8*g+lane
                        v=sum(map(operator.mul,x,ws[col]))+B[col];acc.append(v)
                        hi,rem=divmod(v,65536)
                        y=hi+int(rem>32768 or (rem==32768 and hi%2==1))
                        sat+=int(y < -32768 or y>32767)
                        y=min(32767,max(-32768,y));eight.append(y)
                    e,q=block(eight);raw_y.extend(eight);decoded.extend(v<<e for v in q);payload.extend(octets(q))
                    tags[13*g+row//8]|=e<<(4*(row%8))
            for k,vals,bits in [("x",px,32),("w",pw,32),("b",B,32),("acc",acc,40),
                                ("y",pairs(raw_y),32),("wire",payload+tags,32),("decoded",pairs(decoded),32)]:
                publish(stem+k,vals,bits)
            satlist.append(sat)
        publish("matrix_sat",satlist,32)
        print("SCALAR GOLD PASS",label,flush=True)
    print("FAST VECTORS PASS 1190",flush=True)
if __name__=="__main__":verify()
