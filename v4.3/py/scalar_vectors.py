"""Independent scalar generation for Python 3.6 servers without NumPy."""
import hashlib,json,operator,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LABELS=["base"]+["class_%02d"%i for i in range(12)]+["worst"]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def signed(v,bits):return v-(1<<bits) if v&(1<<(bits-1)) else v
def quant(v,s):
    unit=1<<s
    return max(-32768//unit,min(32767//unit,(v+unit//2)//unit))
def zig(v):return 2*v if v>=0 else -2*v-1
def key(seq,s):
    z=[zig(x) for x in seq]
    def cost(k):return sum(1+k+(v>>k) if (v>>k)<4 else 20-s for v in z)
    return min(range(16),key=cost)
def packed(items,s):
    words=[];buf=used=0
    for v,d,k in items:
        z=zig(d);q=z>>k
        if q<4:n=q+1+k;t=((1<<q)-1)|((z&((1<<k)-1))<<(q+1))
        else:n=20-s;t=15|((v&((1<<(16-s))-1))<<4)
        buf|=t<<used;used+=n
        if used>=32:words.append(buf&0xffffffff);buf>>=32;used-=32
    if used:words.append(buf)
    return words
def head(keys):return sum(k<<(4*i) for i,k in enumerate(keys))
def pairs(a):return [(x&65535)|((y&65535)<<16) for x,y in zip(a[::2],a[1::2])]
def deltas(a):return [a[0]]+[y-x for x,y in zip(a,a[1:])]
def verify(restore=True):
    raw=ROOT.parent/"v2/vec";dest=ROOT/"vec"
    frozen=json.loads((ROOT/"py/stream_manifest.json").read_text())
    original=json.loads((ROOT/"py/vector_manifest.json").read_text())
    profiles=json.loads((ROOT/"py/profile42.json").read_text())["profiles"]
    assert len(frozen)==1400 and not dest.is_symlink()
    for n,h in original.items():
        if digest(raw/n)!=h:raise ValueError("Changed raw input "+n)
    for label in LABELS:
        prefix="streams/"+label+"/";folder=dest/prefix
        assert not folder.is_symlink() and dest.resolve() in folder.resolve().parents
        members=[(dest/n,h) for n,h in frozen.items() if n.startswith(prefix)];assert len(members)==100
        for p,h in members:
            if p.exists() and digest(p)!=h:raise ValueError("Changed golden "+str(p))
        if all(p.is_file() for p,h in members):continue
        if not restore:raise ValueError("Missing golden "+label)
        folder.mkdir(parents=True,exist_ok=True)
        src=raw if label=="base" else raw/"real_speech"/label
        def publish(name,values,bits=32):
            p=folder/(name+".hex")
            data="".join("%0*x\n"%(bits//4,v&((1<<bits)-1)) for v in values).encode()
            assert hashlib.sha256(data).hexdigest()==frozen[p.relative_to(dest).as_posix()],str(p)
            if not p.exists():
                with tempfile.NamedTemporaryFile(dir=str(folder),delete=False) as f:f.write(data)
                Path(f.name).replace(p)
        reads=[];writes=[];params=[];sats=[]
        for layer,profile in enumerate(profiles):
            sx,sw,sy=profile["shifts"];yk=profile["y_k"];stem="layer%02d_"%layer
            def load(k):return [int(t,16) for t in (src/(stem+k+".hex")).read_bytes().splitlines()]
            def halves(a):return [signed(v,16) for w in a for v in (w&65535,w>>16)]
            X=[quant(v,sx) for v in halves(load("x"))];W=[quant(v,sw) for v in halves(load("w"))];B=[signed(v,32) for v in load("b")]
            xx=[0]*4096;ww=[0]*16384;yy=[0x5a5aa5a5]*16384;count=8+256
            padded=X+[0]*64
            for s in range(4):
                cols=[[padded[(4*r+s)*64+c] for r in range(25)] for c in range(64)]
                residual=[deltas(v) for v in cols];ks=[key(v,sx) for v in residual]
                blob=packed(((cols[c][r],residual[c][r],ks[c]) for c in range(64) for r in range(25)),sx)
                part=[len(blob)]+[head(ks[g:g+8]) for g in range(0,64,8)]+blob
                xx[1024*s:1024*s+len(part)]=part;count+=len(part)
            wc=[W[c::256] for c in range(256)];wk=[key(v,sw) for v in wc]
            acc=[];y=[];yc=[];sat=0
            for r in range(99):
                x=X[r*64:r*64+64]
                for c in range(256):
                    v=(sum(map(operator.mul,x,wc[c]))<<(sx+sw))+B[c];acc.append(v)
                    hi,rem=divmod(v,65536);t=hi+int(rem>32768 or (rem==32768 and hi%2))
                    sat+=int(t<-32768 or t>32767);t=min(32767,max(-32768,t));y.append(t);yc.append(quant(t,sy))
            ys=[yc[c::256] for c in range(256)];yd=[deltas(v) for v in ys];groups=[]
            for g in range(16):
                for s in range(4):
                    cols=list(range(16*g+s,16*g+16,4));at=256*(4*g+s)
                    payload=packed(((wc[c][r],wc[c][r],wk[c]) for r in range(64) for c in cols),sw)
                    part=[len(payload),head([wk[c] for c in cols])|(head([yk[c] for c in cols])<<16)]+payload
                    ww[at:at+len(part)]=part;count+=len(part)
                    part=[head([yk[c] for c in cols])]+packed(((ys[c][r],yd[c][r],yk[c]) for r in range(99) for c in cols),sy)
                    yy[at:at+len(part)]=part;groups.append(len(part))
            for n,v,bits in (("x",xx,32),("w",ww,32),("b",B,32),("acc",acc,40),("y",pairs(y),32),
                     ("wire",yy,32),("decoded",pairs([v<<sy for v in yc]),32),("groups",groups,16)):publish(stem+n,v,bits)
            reads.append(count);writes.append(sum(groups));sats.append(sat);params.append(sx|sw<<4|sy<<8)
        for n,v in (("reads",reads),("writes",writes),("matrix_sat",sats),("params",params)):publish(n,v)
        print("SCALAR STREAM PASS",label,flush=True)
    print("STREAM VECTORS PASS 1400; raw "+str(len(original)),flush=True)
if __name__=="__main__":verify()
