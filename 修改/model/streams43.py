"""Four input Rice streams; uncompressed fixed-width row-major output."""
import numpy as np
from rice import codes,delta,choose_k,pack,nibbles,math_layer
FORMAT=0x10005
X_WORDS=4096
W_WORDS=Y_WORDS=16384
def pack_x(xc,sx):
    xx=np.zeros((4,1024),dtype=np.int64)
    reads=0
    padded=np.concatenate((xc,np.zeros((1,64),dtype=np.int64)))
    for s in range(4):
        vals=padded[s::4];res=delta(vals);k,_=choose_k(res,sx,0)
        payload=pack(vals.T,res.T,k[:,None],sx)
        part=[len(payload)]+nibbles(k)+payload
        assert len(part)<=1024
        xx[s,:len(part)]=part;reads+=len(part)
    return xx.ravel(),reads

def pack_w(wc,sw,y_keys):
    ww=np.zeros((16,4,256),dtype=np.int64)
    reads=0
    wk,_=choose_k(wc,sw,0)
    for g in range(16):
        for s in range(4):
            ix=np.arange(g*16+s,g*16+16,4)
            ks=wk[ix];ky=y_keys[ix]
            payload=pack(wc[:,ix],wc[:,ix],ks,sw)
            meta=sum(int(ks[j])<<(4*j) for j in range(4))|sum(int(ky[j])<<(16+4*j) for j in range(4))
            part=[len(payload),meta]+payload
            assert len(part)<=256
            ww[g,s,:len(part)]=part;reads+=len(part)
    return ww.ravel(),reads

def input_words(x,w,b,profile):
    """Encode input slots and bias without evaluating the linear layer."""
    sx,sw,_=profile["shifts"]
    xx,_=pack_x(codes(x,sx),sx)
    ww,_=pack_w(codes(w,sw),sw,np.asarray(profile["y_k"]))
    return xx,ww,b

def frame(x,w,b,profile):
    sx,sw,sy=profile["shifts"]
    xc,wc,acc,y,yc,sat=math_layer(x,w,b,sx,sw,sy)
    y_keys=np.asarray(profile["y_k"])
    xx,x_reads=pack_x(xc,sx)
    ww,w_reads=pack_w(wc,sw,y_keys)
    # Complete matrix of 25,344 signed 16/F11 values, low halfword first.
    # Preserve the old decoded values exactly, including numerical sy rounding.
    restored=(yc<<sy).ravel() & 65535
    yy=restored[::2] | (restored[1::2]<<16)
    return xx,ww,b,acc,y,yy,yc<<sy,sat,8+256+x_reads+w_reads,[99*8]*16
