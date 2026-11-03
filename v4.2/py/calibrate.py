"""Select quantization steps and entropy parameters from the captured training split only."""
import hashlib,json
from pathlib import Path
import numpy as np
from rice import codes,delta,choose_k,math_layer
ROOT=Path(__file__).resolve().parents[1]
def calibrate():
    train=ROOT/"build/train";rows=json.loads((train/"selection.json").read_text())
    assert len(rows)==33
    snapshots=[np.load(train/("sample_%02d.npz"%i)) for i in range(len(rows))]
    X=np.stack([d["x"] for d in snapshots]);Y=np.stack([d["y"] for d in snapshots])
    profiles=[]
    for i in range(12):
        param=np.load(ROOT.parent/"v2/vec/weights"/("layer%02d.npz"%i))
        w=param["w"].astype(np.int64);b=param["b"].astype(np.int64)
        x=np.clip(np.rint(X[:,i]*2048),-32768,32767).astype(np.int64);ref=Y[:,i].astype(np.float64)
        xcost={s:choose_k(delta(codes(x,s)),s,1)[1].sum()/len(rows) for s in range(4)}
        wcost={s:choose_k(codes(w,s),s,0)[1].sum() for s in range(6)}
        yideal=np.clip(np.rint(ref*2048),-32768,32767).astype(np.int64)
        ycost={s:choose_k(delta(codes(yideal,s)),s,(0,1)) for s in range(4)}
        power=float(np.sum(ref*ref));opts=[]
        for sx in range(4):
            for sw in range(6):
                _,_,_,y,_,_=math_layer(x,w,b,sx,sw,0)
                for sy in range(4):
                    decoded=(codes(y,sy)<<sy)/2048.
                    err=(decoded-ref)**2
                    nrmse=float(np.sqrt(np.sum(err)/power))
                    worst=float(np.sqrt(np.max(np.sum(err,axis=(1,2))/np.sum(ref*ref,axis=(1,2)))))
                    if nrmse<=.00138 and worst<=.00235:
                        rate=xcost[sx]+wcost[sw]+ycost[sy][1].sum()/len(rows)
                        opts.append((float(rate),nrmse,worst,sx,sw,sy))
        rate,err,worst,sx,sw,sy=min(opts)
        _,_,_,_,out,_,=math_layer(x,w,b,sx,sw,sy)
        keys,cost=choose_k(delta(out),sy,(0,1))
        profiles.append({"layer":i,"shifts":[sx,sw,sy],"y_k":[int(v) for v in keys],"train_nrmse":err,"train_worst":worst,
                         "estimated_payload_words":round(rate/32,1)})
        print("TRAIN LAYER",i,sx,sw,sy,round(err*100,4),round(rate/32),flush=True)
    receipt={"source":"33 training WAV, checked using the upstream which_set; no validation or testing samples for calibration",
             "selection_sha256":hashlib.sha256((train/"selection.json").read_bytes()).hexdigest(),
             "aggregate_limit":.00138,"individual_limit":.00235,"profiles":profiles}
    (ROOT/"py/profile42.json").write_bytes((json.dumps(receipt,indent=2)+"\n").encode())
    (ROOT/"results/training_samples.json").write_bytes((train/"selection.json").read_bytes())
if __name__=="__main__":calibrate()
