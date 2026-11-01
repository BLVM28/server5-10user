"""Replay original sublayers to capture Dense1; check logits against native model.

--smoke uses silence and generated sine, NOT the required speech validation set.
--manifest accepts a JSON list of {path, split, label}; split must be training or
validation, never testing. Selection/count requirements remain the caller's duty.
The source repository and checkpoint are read only. No training is performed.
"""
import argparse,hashlib,json,os,sys,wave
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from numeric_model import encode,linear

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo',type=Path,default=ROOT.parent/'01_核心参考/keyword-transformer-master')
    p.add_argument('--out',type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--smoke',action='store_true')
    group.add_argument('--manifest',type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
    os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.dont_write_bytecode=True
    sys.path.insert(0,str(a.repo))
    import tensorflow as tf
    import tensorflow_addons as tfa
    # Follow the upstream entry point's import order (utils and models have
    # a circular dependency if kws_transformer is imported first).
    from kws_streaming.models import models as model_registry
    from kws_streaming.models import kws_transformer
    # input_data.py disables eager globally at import; restore it BEFORE any
    # model/tensor is constructed in this standalone inference process.
    if not tf.executing_eagerly():tf.compat.v1.enable_eager_execution()
    assert tf.executing_eagerly()
    source=a.repo/'models_data_v2_12_labels/kwt1'
    flags=json.loads((source/'flags.json').read_text())
    flags.update(training=False,batch_size=1,train=0,use_spec_augment=0,
                 use_spec_cutout=0,resample=0.,sp_resample=0.,volume_resample=0.,
                 time_shift_ms=0.,sp_time_shift_ms=0.,prenorm=False,
                 approximate_gelu=False,distill_teacher_json='')
    model=kws_transformer.model(SimpleNamespace(**flags))
    status=model.load_weights(str(source/'best_weights'))
    status.assert_existing_objects_matched();status.expect_partial()
    transformers=[l for l in model.layers if hasattr(l,'enc_layers')]
    assert len(transformers)==1
    transformer=transformers[0];assert len(transformer.enc_layers)==12
    captured={};params=[]
    for i,block in enumerate(transformer.enc_layers):
        dense=block.ffn.layers[0];w,b=dense.get_weights()
        assert w.shape==(64,256) and b.shape==(256,)
        exported=np.load(ROOT/'vec/weights'/('layer%02d.npz'%i))
        assert np.array_equal(w,exported['w_float']) and np.array_equal(b,exported['b_float'])
        wi,ws=encode(w,16,16);bi,bs=encode(b,32,27)
        params.append((wi,bi,ws,bs))
    # TF 2.4 Sequential caches a graph, so replacing Dense.call after model
    # construction does not reliably capture invocations. Replay the exact
    # PostNorm source using the SAME original layer objects, and compare final
    # logits against a separate ordinary model call on every sample.
    feature=[l for l in model.layers if l.__class__.__name__=='SpeechFeatures']
    assert len(feature)==1
    classifier=model.layers[-1]
    def replay(audio):
        net=transformer.patch_proj(feature[0](audio))
        net=tf.concat([tf.broadcast_to(transformer.class_emb,[1,1,64]),net],axis=1)+transformer.pos_emb
        for i,block in enumerate(transformer.enc_layers):
            assert not block.prenorm
            attention,_=block.att(net)
            out1=block.layernorm1(net+block.dropout1(attention,training=False))
            y=block.ffn.layers[0](out1)
            captured[i]=(out1.numpy()[0],y.numpy()[0])
            net=block.layernorm2(out1+block.dropout2(block.ffn(out1),training=False))
        return classifier(net[:,0])
    if a.smoke:
        samples=[{'path':'generated:silence','split':'smoke','label':'silence'},
                 {'path':'generated:sine440','split':'smoke','label':'synthetic_tone'}]
    else:
        samples=json.loads(a.manifest.read_text(encoding='utf-8'))
        assert samples and all(s['split'] in ('training','validation') for s in samples)
    totals=[{'layer':i,'error_sum_sq':0.,'reference_sum_sq':0.,'elements':0,
             'x_saturated':0,'y_saturated':0,'w_saturated':params[i][2],
             'b_saturated':params[i][3],'max_abs_x':0.,'max_abs_y':0.} for i in range(12)]
    records=[];rtl=a.out/'rtl';rtl.mkdir(exist_ok=True)
    def hexfile(name,values,bits):
        (rtl/name).write_text(''.join(('%0*x\n'%(bits//4,int(v)&((1<<bits)-1)))
                                     for v in np.asarray(values).flat),encoding='ascii')
    def pack16(data):
        v=np.asarray(data,dtype=np.int64).ravel()&65535
        return v[0::2]|(v[1::2]<<16)
    first_sat=[]
    for n,sample in enumerate(samples):
        if sample['path']=='generated:silence':audio=np.zeros(16000,np.float32)
        elif sample['path']=='generated:sine440':
            audio=(0.1*np.sin(2*np.pi*440*np.arange(16000)/16000)).astype(np.float32)
        else:
            path=Path(sample['path'])
            if not path.is_absolute():path=a.manifest.parent/path
            with wave.open(str(path),'rb') as f:
                assert f.getnchannels()==1 and f.getsampwidth()==2 and f.getframerate()==16000
                audio=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float32)/32768.
            assert len(audio)<=16000,'Use official one-second clips, no arbitrary cropping'
            audio=np.pad(audio,(0,16000-len(audio)))
            sample=dict(sample,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        captured.clear()
        prediction=model(tf.constant(audio[None,:]),training=False)
        if isinstance(prediction,(list,tuple)):prediction=prediction[0]
        assert np.isfinite(prediction.numpy()).all()
        replayed=replay(tf.constant(audio[None,:]))
        assert np.array_equal(prediction.numpy(),replayed.numpy()), 'Replay differs from original model'
        assert len(captured)==12
        for i in range(12):
            x,reference=captured[i];assert x.shape==(99,64) and reference.shape==(99,256)
            xi,xsat=encode(x,16,11);wi,bi,_,_=params[i]
            yi,acc,sat=linear(xi,wi,bi)
            ref=reference.astype(np.float64);decoded=yi.astype(np.float64)/2048.
            assert np.isfinite(ref).all()
            t=totals[i];t['error_sum_sq']+=float(np.sum((decoded-ref)**2))
            t['reference_sum_sq']+=float(np.sum(ref**2));t['elements']+=ref.size
            t['x_saturated']+=xsat;t['y_saturated']+=int(sat.sum())
            t['max_abs_x']=max(t['max_abs_x'],float(np.max(np.abs(x))))
            t['max_abs_y']=max(t['max_abs_y'],float(np.max(np.abs(ref))))
            if n==0:
                np.savez_compressed(a.out/('layer%02d_first.npz'%i),x=x,reference=reference,y_int=yi,acc=acc)
                for suffix,data,bits in [('x',pack16(xi),32),('w',pack16(wi),32),('b',bi,32),
                                         ('y',pack16(yi),32),('acc',acc,40)]:
                    hexfile('layer%02d_%s.hex'%(i,suffix),data,bits)
                first_sat.append(int(sat.sum()))
        records.append(sample)
        print('captured %d/%d %s'%(n+1,len(samples),sample['path']),flush=True)
    hexfile('matrix_sat.hex',first_sat,32)
    for t in totals:
        t['nrmse']=(t['error_sum_sq']/t['elements'])**.5/max((t['reference_sum_sq']/t['elements'])**.5,1e-8)
    report={'tensorflow':tf.__version__,'tensorflow_addons':tfa.__version__,
            'checkpoint_existing_objects_matched':True,'all_dense1_weights_equal_export':True,
            'capture_method':'same original sublayers, PostNorm replay; logits bit-equal to original model for every sample',
            'augmentation_disabled':True,'samples':records,'layers':totals,
            'max_layer_nrmse':max(t['nrmse'] for t in totals),
            'qualification':'SMOKE ONLY, not official speech precision acceptance' if a.smoke else
              'User-supplied training/validation clips; verify official sample selection/counts independently'}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('max layer aggregate NRMSE %.8f%%'%(report['max_layer_nrmse']*100),flush=True)

if __name__=='__main__':main()
