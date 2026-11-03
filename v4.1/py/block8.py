"""Block8 v4.1. Each exponent is computed only from the block being encoded."""
import numpy as np

def encode_block(values):
    """Signed int16 last axis -> uint4 exponent and int8 mantissas (nearest, ties toward +infinity)."""
    a=np.asarray(values,dtype=np.int64)
    if np.any((a < -32768) | (a > 32767)):
        raise ValueError("Encoded source outside int16")
    top=np.max(np.where(a < 0, ~a, a),axis=-1)
    e=np.zeros(top.shape,dtype=np.int64)
    for bit in range(7,15):
        e+=top >= (1<<bit)
    step=(1<<e)[...,None]
    q=np.clip((a+step//2)//step,-128,127)
    return e,q

def unpack(e,q):
    return np.asarray(q,dtype=np.int64)<<np.asarray(e,dtype=np.int64)[...,None]

def transform(x,w,b):
    xe,xq=encode_block(x)
    we,wq=encode_block(w.T)
    xx=unpack(xe,xq); ww=unpack(we,wq).T
    acc=xx @ ww + b
    floor=acc>>16
    low=acc&65535
    y0=floor+((low>32768)|((low==32768)&((floor&1)!=0)))
    y=np.clip(y0,-32768,32767)
    ye,yq=encode_block(y.reshape(99,32,8))
    return xe,xq,we,wq,acc,y,ye,yq,unpack(ye,yq).reshape(99,256),int(np.count_nonzero(y0!=y))

def packed_bytes(q):
    a=np.asarray(q,dtype=np.int64).reshape(-1,4)&255
    return a[:,0]|a[:,1]<<8|a[:,2]<<16|a[:,3]<<24

def memory(x,w,b):
    xe,xq,we,wq,acc,y,ye,yq,decoded,sat=transform(x,w,b)
    px=np.column_stack((xe,packed_bytes(xq).reshape(99,16))).ravel()
    ww=wq.T.reshape(64,32,8).transpose(1,0,2)
    exps=np.sum(we.reshape(32,8)<<(4*np.arange(8)),axis=1)
    pw=np.column_stack((exps,packed_bytes(ww).reshape(32,128))).ravel()
    tags=np.pad(ye.T,((0,0),(0,5))).reshape(32,13,8)
    pt=np.sum(tags<<(4*np.arange(8)),axis=2).ravel()
    py=np.concatenate((packed_bytes(yq),pt))
    assert (len(px),len(pw),len(py))==(1683,4128,6752)
    return px,pw,b,acc,y,py,decoded,sat

def read_words(path):
    return np.array([int(x,16) for x in path.read_bytes().splitlines()],dtype=np.int64)
def int16_pairs(words):
    a=np.column_stack((words&65535,words>>16)).ravel()
    return (a^32768)-32768
