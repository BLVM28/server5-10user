"""Four independent bounded Rice streams. Numeric output is exactly Precision42."""
import numpy as np
from rice import codes,delta,choose_k,pack,nibbles,math_layer
FORMAT=0x10004
X_WORDS=4096
W_WORDS=Y_WORDS=16384
def frame(x,w,b,profile):
    sx,sw,sy=profile["shifts"]
    xc,wc,acc,y,yc,sat=math_layer(x,w,b,sx,sw,sy)
    xx=np.zeros((4,1024),dtype=np.int64);ww=np.zeros((16,4,256),dtype=np.int64)
    yy=np.full((16,4,256),0x5a5aa5a5,dtype=np.int64);counts=[]
    reads=8+256
    padded=np.concatenate((xc,np.zeros((1,64),dtype=np.int64)))
    for s in range(4):
        vals=padded[s::4];res=delta(vals);k,_=choose_k(res,sx,0)
        payload=pack(vals.T,res.T,k[:,None],sx)
        part=[len(payload)]+nibbles(k)+payload
        assert len(part)<=1024
        xx[s,:len(part)]=part;reads+=len(part)
    wk,_=choose_k(wc,sw,0)
    for g in range(16):
        for s in range(4):
            ix=np.arange(g*16+s,g*16+16,4)
            ks=wk[ix];ky=np.asarray(profile["y_k"])[ix]
            payload=pack(wc[:,ix],wc[:,ix],ks,sw)
            meta=sum(int(ks[j])<<(4*j) for j in range(4))|sum(int(ky[j])<<(16+4*j) for j in range(4))
            part=[len(payload),meta]+payload
            assert len(part)<=256
            ww[g,s,:len(part)]=part;reads+=len(part)
            payload=pack(yc[:,ix],delta(yc[:,ix]),ky,sy)
            part=[sum(int(ky[j])<<(4*j) for j in range(4))]+payload
            assert len(part)<=256
            yy[g,s,:len(part)]=part;counts.append(len(part))
    return xx.ravel(),ww.ravel(),b,acc,y,yy.ravel(),yc<<sy,sat,reads,counts
