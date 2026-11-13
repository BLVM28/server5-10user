"""Precision42 fixed-point math and LSB-first bounded Rice transport."""
import numpy as np

FORMAT=0x00010003
X_WORDS=4096
GROUP_WORDS=512
W_WORDS=Y_WORDS=32*GROUP_WORDS

def codes(values,shift):
    """Round to the nearest multiple of 2**shift, ties to +infinity."""
    scale=1<<shift
    a=np.asarray(values,dtype=np.int64)
    return np.clip((a+scale//2)//scale,-32768//scale,32767//scale)

def delta(a):
    return a-np.concatenate((np.zeros_like(a[..., :1,:]),a[..., :-1,:]),axis=-2)

def zigzag(a):
    return np.where(a<0,-2*a-1,2*a)

def choose_k(residual,shift,axis):
    z=zigzag(residual)
    best=np.full(np.sum(z,axis=axis).shape,2**60,dtype=np.int64)
    keys=np.zeros_like(best)
    for k in range(16):
        quotient=z>>k
        cost=np.where(quotient<4,1+k+quotient,20-shift).sum(axis=axis)
        improve=cost<best
        keys=np.where(improve,k,keys);best=np.minimum(best,cost)
    return keys,best

def nibbles(entries):
    a=np.asarray(entries,dtype=np.int64).reshape(-1,8)
    return np.sum(a<<(4*np.arange(8)),axis=1).tolist()

def pack(values,residuals,keys,shift):
    """Pack prefix, remainder or signed absolute escape. Last word is zero padded."""
    values=np.asarray(values,dtype=np.int64)
    keys=np.broadcast_to(keys,values.shape)
    z=zigzag(residuals);u=z>>keys
    widths=np.where(u<4,u+1+keys,20-shift)
    short=((z&((1<<keys)-1))<<(np.minimum(u,3)+1))|((1<<np.minimum(u,3))-1)
    literals=((values&((1<<(16-shift))-1))<<4)|15
    bits=np.where(u<4,short,literals).ravel()
    sizes=widths.ravel()
    starts=np.cumsum(sizes,dtype=np.int64)-sizes
    idx=starts>>5;offset=starts&31
    out=np.zeros(int((starts[-1]+sizes[-1]+31)//32)+1,dtype=np.int64)
    np.bitwise_or.at(out,idx,(bits<<offset)&0xffffffff)
    np.bitwise_or.at(out,idx+1,bits>>(32-offset))
    return out[:-1].tolist()

def math_layer(x,w,b,sx,sw,sy):
    xc,wc=codes(x,sx),codes(w,sw)
    acc=(xc<<sx)@(wc<<sw)+b
    base=acc>>16;low=acc&65535
    before=base+((low>32768)|((low==32768)&((base&1)!=0)))
    y=np.clip(before,-32768,32767)
    return xc,wc,acc,y,codes(y,sy),int(np.count_nonzero(before!=y))

def memory(x,w,b,profile):
    sx,sw,sy=profile["shifts"]
    xc,wc,acc,y,yc,sat=math_layer(x,w,b,sx,sw,sy)
    xk,_=choose_k(delta(xc),sx,0)
    def xorder(a):
        return a.reshape(99,32,2).transpose(1,0,2)
    xp=pack(xorder(xc),xorder(delta(xc)),np.broadcast_to(xk.reshape(32,1,2),(32,99,2)),sx)
    xwords=[len(xp)]+nibbles(xk)+xp
    wk,_=choose_k(wc,sw,0);yk=np.asarray(profile["y_k"])
    wslots=np.zeros(W_WORDS,dtype=np.int64);yslots=np.full(Y_WORDS,0x5a5aa5a5,dtype=np.int64)
    written=[];reads=8+len(xwords)+256+32
    for g in range(32):
        cols=slice(8*g,8*g+8)
        ws=wc[:,cols];wp=pack(ws,ws,wk[cols],sw)
        wpart=[len(wp),nibbles(wk[cols])[0],nibbles(yk[cols])[0]]+wp
        wslots[512*g:512*g+len(wpart)]=wpart
        reads+=2+len(wp)  # Y metadata is read once, separately at write-back.
        yp=pack(yc[:,cols],delta(yc[:,cols]),yk[cols],sy)
        ypart=[nibbles(yk[cols])[0]]+yp
        yslots[512*g:512*g+len(ypart)]=ypart;written.append(len(ypart))
        assert len(wpart)<=512 and len(ypart)<=512
    assert len(xwords)<=4096
    return xwords,wslots,b,acc,y,yslots,yc<<sy,sat,reads,written
