"""Rebuild missing Precision42 goldens with scalar integer math on Python 3.6+."""
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
    def cost(k):
        return sum((1+k+(a>>k)) if (a>>k)<4 else (20-s) for a in z)
    return min(range(16),key=cost)
def packed(items,s):
    words=[];buf=used=0
    for v,d,k in items:
        z=zig(d);q=z>>k
        if q<4:
            n=q+1+k;t=(1<<q)-1|((z&((1<<k)-1))<<(q+1))
        else:
            n=20-s;t=15|((v&((1<<(16-s))-1))<<4)
        buf|=t<<used;used+=n
        if used>=32:words.append(buf&0xffffffff);buf>>=32;used-=32
    if used:words.append(buf)
    return words
def head(keys):return sum(k<<(4*i) for i,k in enumerate(keys))
def pairs(a):return [(x&65535)|((y&65535)<<16) for x,y in zip(a[::2],a[1::2])]
def deltas(a):return [a[0]]+[y-x for x,y in zip(a,a[1:])]
def verify(restore=True):
    raw=ROOT.parent/"v2/vec";dest=ROOT/"vec";old=ROOT.parent/"v4.1/vec"
    manifest=json.loads((ROOT/"py/precision_manifest.json").read_text())
    orig=json.loads((ROOT/"py/vector_manifest.json").read_text())
    fast=json.loads((ROOT/"py/fast_manifest.json").read_text())
    profiles=json.loads((ROOT/"py/profile42.json").read_text())["profiles"]
    assert len(manifest)==1400 and len(fast)==1190 and not dest.is_symlink()
    for n,h in fast.items():
        if digest(old/n)!=h:raise ValueError("Changed compatibility vector: "+n)
    for n,h in orig.items():
        if digest(raw/n)!=h:raise ValueError("Changed v2 input: "+n)
    for label in LABELS:
        prefix="precision/"+label+"/"
        src=raw if label=="base" else raw/"real_speech"/label
        folder=dest/prefix
        assert not folder.is_symlink() and dest.resolve() in folder.resolve().parents
        files=[(dest/n,h) for n,h in manifest.items() if n.startswith(prefix)]
        assert len(files)==100
        for p,h in files:
            if p.exists() and digest(p)!=h:raise ValueError("Changed golden: "+str(p))
        if all(p.is_file() for p,h in files):continue
        if not restore:raise ValueError("Missing goldens: "+label)
        folder.mkdir(parents=True,exist_ok=True)
        def publish(name,values,bits=32):
            p=folder/(name+".hex")
            data="".join("%0*x\n"%(bits//4,v&((1<<bits)-1)) for v in values).encode()
            assert hashlib.sha256(data).hexdigest()==manifest[p.relative_to(dest).as_posix()],str(p)
            if not p.exists():
                with tempfile.NamedTemporaryFile(dir=str(folder),delete=False) as f:f.write(data)
                Path(f.name).replace(p)
        reads=[];writes=[];params=[];sats=[]
        for i,profile in enumerate(profiles):
            sx,sw,sy=profile["shifts"];yk=profile["y_k"];stem="layer%02d_"%i
            def load(name):
                return [int(t,16) for t in (src/(stem+name+".hex")).read_bytes().splitlines()]
            def halves(words):return [signed(v,16) for w in words for v in (w&65535,w>>16)]
            X=[quant(v,sx) for v in halves(load("x"))];W=[quant(v,sw) for v in halves(load("w"))]
            B=[signed(v,32) for v in load("b")]
            xs=[X[k::64] for k in range(64)];xd=[deltas(v) for v in xs];xkeys=[key(v,sx) for v in xd]
            xp=packed(((xs[c][m],xd[c][m],xkeys[c]) for pair in range(32) for m in range(99) for c in (2*pair,2*pair+1)),sx)
            xwords=[len(xp)]+[head(xkeys[g:g+8]) for g in range(0,64,8)]+xp
            ws=[W[c::256] for c in range(256)];wk=[key(col,sw) for col in ws]
            wwords=[0]*16384;ywords=[0x5a5aa5a5]*16384
            acc=[];y=[];decoded=[];sat=0
            for row in range(99):
                x=X[row*64:row*64+64]
                for col in range(256):
                    v=(sum(map(operator.mul,x,ws[col]))<<(sx+sw))+B[col];acc.append(v)
                    hi,rem=divmod(v,65536)
                    t=hi+int(rem>32768 or (rem==32768 and hi%2!=0))
                    sat+=int(t<-32768 or t>32767);t=min(32767,max(-32768,t));y.append(t)
                    decoded.append(quant(t,sy))
            ys=[decoded[c::256] for c in range(256)];yd=[deltas(v) for v in ys]
            count=8+len(xwords)+256+32;groups=[]
            for g in range(32):
                cols=range(8*g,8*g+8);a=512*g
                blob=packed(((ws[c][r],ws[c][r],wk[c]) for r in range(64) for c in cols),sw)
                meta=head(yk[8*g:8*g+8])
                fr=[len(blob),head(wk[8*g:8*g+8]),meta]+blob
                wwords[a:a+len(fr)]=fr;count+=2+len(blob)
                fr=[meta]+packed(((ys[c][r],yd[c][r],yk[c]) for r in range(99) for c in cols),sy)
                ywords[a:a+len(fr)]=fr;groups.append(len(fr))
            for n,vals,bits in (("x",xwords+[0]*(4096-len(xwords)),32),("w",wwords,32),("b",B,32),
                ("acc",acc,40),("y",pairs(y),32),("wire",ywords,32),("decoded",pairs([v<<sy for v in decoded]),32),
                ("groups",groups,16)):publish(stem+n,vals,bits)
            reads.append(count);writes.append(sum(groups));sats.append(sat);params.append(sx|sw<<4|sy<<8)
        for n,v in (("reads",reads),("writes",writes),("params",params),("matrix_sat",sats)):publish(n,v)
        print("SCALAR GOLD PASS",label,flush=True)
    print("PRECISION VECTORS PASS 1400; compatibility 1190; original "+str(len(orig)),flush=True)
if __name__=="__main__":verify()
