"""Generate new transport references, proving all r8 numerical results unchanged.

Run once after copying the original final vectors. Later use verify_frozen.py.
This does not read RTL and never changes a golden result to match a simulation.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from prepare_layer import input_files, reference_files, hex_bytes, load_profiles
from verify_frozen import signed_halfwords, read_words

root = Path(__file__).resolve().parents[1]
v = root / 'verification/vec'
old_manifest = json.loads((v / 'manifest.json').read_text(encoding='utf-8'))
identity = json.loads((root / '依据/final原版SHA256.json').read_text(encoding='utf-8'))
rebuilt = {}
counters = dict(matrix_sat=[], reads=[], writes=[], params=[])
for layer, profile in enumerate(load_profiles()):
    stem = f'layer{layer:02d}_'
    x = signed_halfwords(v / 'raw' / (stem+'x.hex'), (99,64))
    w = signed_halfwords(v / 'raw' / (stem+'w.hex'), (64,256))
    b = (read_words(v / 'raw' / (stem+'b.hex')) ^ 0x80000000)-0x80000000
    files, stats = reference_files(x,w,b,profile)
    for name in ('x','w','b','acc','y','decoded'):
        assert hashlib.sha256(files[name]).hexdigest() == identity['verification/vec/worst/'+stem+name+'.hex'], (layer,name)
    assert files['wire'] == files['decoded'], 'Output must be the original full decoded matrix'
    assert input_files(x,w,b,profile) == {k:files[k] for k in ('x','w','b')}
    rebuilt.update({stem+k+'.hex':value for k,value in files.items()})
    for k,value in stats.items(): counters[k].append(value)
    sx,sw,sy=profile['shifts']; counters['params'].append(sx|(sw<<4)|(sy<<8))
rebuilt.update({k+'.hex':hex_bytes(value) for k,value in counters.items()})
for name,value in rebuilt.items(): (v/'worst'/name).write_bytes(value)
manifest={'raw':old_manifest['raw'], 'worst':{name:hashlib.sha256(value).hexdigest() for name,value in sorted(rebuilt.items())}}
(v/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('RAW_OUTPUT_REFERENCE_PASS layers=12 original_numerical_files=72 writes_per_task=12672')
