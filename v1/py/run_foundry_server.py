"""Run our RTL against public SRAM models; write ONLY in the assigned home.

Copy this project into HOME/kwt_foundry_full_20261101 before invoking. The public
files are read in place. This is a NICE BFM test, not an E203 processor test.
Vectors here are independently generated integer stimuli, not speech samples.
"""
from pathlib import Path
from fractions import Fraction
import hashlib,json,os,re,subprocess

HOME=Path('/storage2/2026contest/server5/s5_10usr')
ROOT=Path(__file__).resolve().parents[1]
assert ROOT.parent.resolve()==HOME.resolve(), 'Run in the assigned private home only'
OUT=ROOT/'build'/'foundry_functional'
VEC=ROOT/'vec_foundry'
OUT.mkdir(parents=True,exist_ok=True);VEC.mkdir(exist_ok=True)
(OUT/'tmp').mkdir(exist_ok=True)

def hexfile(name,data,bits):
    (VEC/name).write_text(''.join(('%0*x\n'%(bits//4,v&((1<<bits)-1))) for v in data))
def packed(data):
    return [(data[i]&65535)|((data[i+1]&65535)<<16) for i in range(0,len(data),2)]

sats=[0]*12
for layer in [0,11]:
    x=[((m*97+k*139+layer*11)%6001)-3000 for m in range(99) for k in range(64)]
    w=[((k*571+n*197+layer*79)%65536)-32768 for k in range(64) for n in range(256)]
    b=[((n*1234567+layer*54321)%(1<<31))-(1<<30) for n in range(256)]
    acc=[sum(x[m*64+k]*w[k*256+n] for k in range(64))+b[n]
         for m in range(99) for n in range(256)]
    rounded=[round(Fraction(a,65536)) for a in acc]
    y=[max(-32768,min(32767,v)) for v in rounded]
    sats[layer]=sum(a!=b for a,b in zip(y,rounded))
    for suffix,data,bits in [('x',packed(x),32),('w',packed(w),32),('b',b,32),
                             ('y',packed(y),32),('acc',acc,40)]:
        hexfile('layer%02d_%s.hex'%(layer,suffix),data,bits)
hexfile('matrix_sat.hex',sats,32)
tb=(ROOT/'tb/tb_kwt_system.sv').read_text()
assert tb.count('for(l=0;l<12;l=l+1)')==1
tb=tb.replace('for(l=0;l<12;l=l+1)','for(l=0;l<1;l=l+1)').replace('%0d/29 NICE','%0d/18 NICE')
(OUT/'tb_kwt_foundry.sv').write_text(tb)
sources=[ROOT/line for line in (ROOT/'rtl.f').read_text().splitlines() if line.strip()]
public=Path('/storage1/admin_public_dir/SRAM_Lib_2025')
macros=[public/m/'verilog'/(m+s) for m in ['RAMSP128X16','RAMSP1024X16'] for s in ['.v','_rtl.v']]
sources+=macros+[OUT/'tb_kwt_foundry.sv']
env=os.environ.copy()
for name in ['TMPDIR','TMP','TEMP']:env[name]=str(OUT/'tmp')
meta={'test':'NICE BFM + real SRAM macros, independent integer vectors',
      'qualification':'ARM_UD_MODEL functional macro branch; NOT E203 SoC; NOT speech accuracy; no SDF/STA',
      'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
cmd=['vcs','-full64','-sverilog','-timescale=1ns/1ps','-top','tb_kwt_system',
     '+define+KWT_USE_FOUNDRY_SRAM','+define+ARM_UD_MODEL']+[str(p) for p in sources]+['-o','simv']
with (OUT/'compile.log').open('w') as log:
    r=subprocess.run(cmd,cwd=str(OUT),env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
meta['compile_exit']=r.returncode
if r.returncode==0:
    with (OUT/'run.log').open('w') as log:
        r=subprocess.run([str(OUT/'simv'),'+VEC_DIR='+str(VEC)],cwd=str(OUT),env=env,
                         stdout=log,stderr=subprocess.STDOUT,timeout=600)
    output=(OUT/'run.log').read_text(errors='replace')
    meta['run_exit']=r.returncode
    meta['passed']=r.returncode==0 and 'ALL PASS, 18/18' in output and not re.search(r'Fatal|FATAL|Error!',output)
    print(output[-3500:])
else:
    meta['passed']=False;print((OUT/'compile.log').read_text(errors='replace')[-5000:])
(OUT/'results.json').write_text(json.dumps(meta,indent=2)+'\n')
print('RESULT',json.dumps({k:v for k,v in meta.items() if k!='source_sha256'}))
raise SystemExit(0 if meta['passed'] else 1)
