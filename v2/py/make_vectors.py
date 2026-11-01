"""Deterministic RTL vectors. Synthetic X is labelled, never a speech accuracy claim."""
from pathlib import Path
import json
import numpy as np
from numeric_model import linear,quantize

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'vec'
def hexfile(path,values,bits):
    mask=(1<<bits)-1
    path.write_text(''.join(f'{int(x)&mask:0{bits//4}x}\n' for x in np.asarray(values).flat),encoding='ascii')
def pack16(a):
    a=np.asarray(a,dtype=np.int64).ravel()&65535
    return a[0::2] | (a[1::2]<<16)

def main():
    rng=np.random.default_rng(20261101)
    OUT.mkdir(exist_ok=True)
    qvalues=[]
    for q in [-8388608,-32770,-32769,-32768,-32767,-3,-2,-1,0,1,2,3,32766,32767,32768,8388606]:
        for rem in [0,1,32767,32768,32769,65535]:
            a=q*65536+rem
            if -(1<<39)<=a<(1<<39):qvalues.append(a)
    qvalues.extend([-(1<<39),(1<<39)-1])
    qvalues.extend(map(int,rng.integers(-(1<<39),1<<39,size=128,dtype=np.int64)))
    hexfile(OUT/'quant_acc.hex',qvalues,40)
    hexfile(OUT/'quant_y.hex',[quantize(a)[0] for a in qvalues],16)
    hexfile(OUT/'quant_sat.hex',[int(quantize(a)[1]) for a in qvalues],4)
    xs=[];ws=[];bs=[];accs=[];ys=[];sats=[]
    for case in range(32):
        x=rng.integers(-32768,32768,size=64,dtype=np.int64)
        w=rng.integers(-32768,32768,size=64,dtype=np.int64)
        b=int(rng.integers(-(1<<31),1<<31,dtype=np.int64))
        if case==0:x[:]=0;w[:]=0;b=0
        if case==1:x[:]=-32768;w[:]=-32768;b=(1<<31)-1
        if case==2:x[:]=-32768;w[:]=32767;b=-(1<<31)
        if case==3:x[:]=0;w[:]=0;x[63]=12345;w[63]=-26789;b=567
        if case==4:x[:]=0;w[:]=0;b=-32768
        if case==5:x[:]=0;w[:]=0;b=-98304
        a=sum(int(xi)*int(wi) for xi,wi in zip(x,w))+b
        y,s=quantize(a)
        xs.extend(x);ws.extend(w);bs.append(b);accs.append(a);ys.append(y);sats.append(s)
    for name,values,bits in [('dot_x',xs,16),('dot_w',ws,16),('dot_b',bs,32),
      ('dot_acc',accs,40),('dot_y',ys,16),('dot_sat',sats,4)]:hexfile(OUT/(name+'.hex'),values,bits)
    layers=[]
    for layer in range(12):
        data=np.load(OUT/'weights'/f'layer{layer:02d}.npz')
        x=np.clip(np.rint(rng.normal(0,1.1,(99,64))*2048),-32768,32767).astype(np.int16)
        # Include end-of-row/bank/address sentinels and exact zero rows.
        x[0,:]=0;x[98,:]=np.arange(-32,32)*97
        y,acc,sat=linear(x,data['w'],data['b'])
        prefix=OUT/f'layer{layer:02d}'
        for suffix,values,bits in [('x',pack16(x),32),('w',pack16(data['w']),32),
          ('b',data['b'],32),('y',pack16(y),32),('acc',acc,40)]:
            hexfile(Path(str(prefix)+'_'+suffix+'.hex'),values,bits)
        layers.append({'layer':layer,'source':'specified checkpoint, synthetic X',
          'output_saturated':int(sat.sum())})
    report={'seed':20261101,'quant_cases':len(qvalues),'dot_cases':32,'layers':layers,
      'qualification':'NOT Speech Commands activation data; NOT official NRMSE verification'}
    hexfile(OUT/'matrix_sat.hex',[l['output_saturated'] for l in layers],32)
    (OUT/'vectors.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'Generated {len(qvalues)} quantizer cases, 32 dot products, 12 full matrix cases')
if __name__=='__main__': main()
