"""Export exact named FFN1 tensors from the specified best_weights checkpoint.

Prefer TensorFlow's checkpoint API. --reader-deps enables an optional small MIT
reader for environments without TensorFlow (compatibility shims are local only).
"""
import argparse, collections, hashlib, inspect, json, os, sys
from pathlib import Path
import numpy as np
from numeric_model import encode, FORMAT_ID

EXPECTED = {
    '.index': '5a60a0fa78a1855572084a42669768e2998d37e7d93c833962960fdb0db70fbc',
    '.data-00000-of-00001': 'ae993f6ed995938c1ab584b0857b35ca18f31f88001c7e17c7d7c3868bd33ad3',
}

def load_reader(prefix, reader_deps=None):
    if reader_deps:
        sys.path.insert(0,str(Path(reader_deps).resolve()))
        if not hasattr(np,'string_'): np.string_=np.bytes_
        if not hasattr(np,'unicode_'): np.unicode_=np.str_
        if not hasattr(inspect,'ArgSpec'):
            inspect.ArgSpec=collections.namedtuple('ArgSpec','args varargs keywords defaults')
        if not hasattr(os,'pread'):
            import msvcrt
            def pread(fd,n,offset):
                msvcrt.setmode(fd,os.O_BINARY)
                os.lseek(fd,offset,os.SEEK_SET)
                return os.read(fd,n)
            os.pread=pread  # Single-threaded adapter only.
        from tensorflow_checkpoint_reader.py_checkpoint_reader import NewCheckpointReader
        return NewCheckpointReader(str(prefix).encode('utf-8'))
    import tensorflow as tf
    return tf.train.load_checkpoint(str(prefix))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reader-deps',type=Path)
    args=p.parse_args()
    hashes={}
    for suffix,expected in EXPECTED.items():
        h=hashlib.sha256(Path(str(args.checkpoint)+suffix).read_bytes()).hexdigest()
        if h!=expected: raise ValueError('Unexpected checkpoint identity: '+suffix)
        hashes[suffix]=h
    reader=load_reader(args.checkpoint,args.reader_deps)
    shape_map=reader.get_variable_to_shape_map()
    args.output.mkdir(parents=True,exist_ok=True)
    report={'format_id':FORMAT_ID,'source_sha256':hashes,'layers':[]}
    for layer in range(12):
        stem=f'layer_with_weights-0/enc_layers/{layer}/ffn/layer_with_weights-0/'
        wn,bn=[stem+s+'/.ATTRIBUTES/VARIABLE_VALUE' for s in ('kernel','bias')]
        if tuple(shape_map[wn])!=(64,256) or tuple(shape_map[bn])!=(256,):
            raise ValueError('Invalid layer shape')
        wf,bf=np.array(reader.get_tensor(wn)),np.array(reader.get_tensor(bn))
        w,sw=encode(wf,16,16); b,sb=encode(bf,32,27)
        np.savez(args.output/f'layer{layer:02d}.npz',w=w.astype(np.int16),
                 b=b.astype(np.int32),w_float=wf,b_float=bf)
        report['layers'].append({'layer':layer,'kernel_key':wn,'bias_key':bn,
          'weight_saturated':sw,'bias_saturated':sb,
          'max_abs_w':float(np.max(np.abs(wf))),'max_abs_b':float(np.max(np.abs(bf)))})
    (args.output/'format.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('ALL PASS, 12/12 checkpoint FFN1 exports; not an activation-accuracy test')

if __name__=='__main__': main()
