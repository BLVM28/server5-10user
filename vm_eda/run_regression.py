"""Run the unchanged golden regressions on Xcelium, one version per process."""
from pathlib import Path
import argparse,subprocess,os,json,hashlib,time,shutil
R=Path(os.environ['KWT_VM_ROOT']);assert str(R)=='/home/eda/kwt_vm_20261101'
p=argparse.ArgumentParser();p.add_argument('version',choices=['v1','v2']);a=p.parse_args()
src=R/'work'/a.version;out=R/'results'/a.version/'functional'
history=out.parent/'history';history.mkdir(parents=True,exist_ok=True);stamp=str(int(time.time()*1000000))
if out.exists():shutil.move(str(out),str(history/('functional_'+stamp)))
for tag in ['vm_default','vm_fallback','vm_activation']:
 if (src/'build'/tag).exists():shutil.move(str(src/'build'/tag),str(history/('build_'+tag+'_'+stamp)))
out.mkdir(parents=True,exist_ok=True)
record={'version':a.version,'simulator':'Xcelium','qualification':'behavioral SRAM, no actual E203 CPU or foundry SRAM timing','source_sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in (src/'rtl').glob('*.sv')},'stages':[]}
tops=['tb_kwt_arithmetic','tb_kwt_icb','tb_kwt_system']
if a.version=='v2':tops+=['tb_kwt_overlap','tb_kwt_mul_pipeline']
jobs=[('default',['--tops']+tops),('fallback',['--tops','tb_kwt_system','--define','KWT_TEST_SWAP','--define','KWT_TEST_W1024']),('activation',['--tops','tb_kwt_system','--vectors',str(src/'vec/activation_smoke/rtl')])]
try:
 for name,args in jobs:
  cmd=['python3',str(src/'py/run_linux.py'),'--sim','xrun','--tag','vm_'+name]+args
  with (out/(name+'.log')).open('w') as f:r=subprocess.run(cmd,cwd=str(src),stdout=f,stderr=subprocess.STDOUT,timeout=1800)
  result=src/'build'/('vm_'+name)/'results.json'
  ok=r.returncode==0 and result.exists()
  record['stages'].append({'name':name,'exit':r.returncode,'passed':ok,'details':json.loads(result.read_text()) if ok else None})
  print(a.version,name,'PASS' if ok else 'FAIL',flush=True)
  if not ok:raise RuntimeError((out/(name+'.log')).read_text()[-4500:])
 record['completed']=True
except Exception as e:record['completed']=False;record['error']=str(e);print(str(e),flush=True)
(out/'results.json').write_text(json.dumps(record,indent=2)+'\n')
raise SystemExit(0 if record['completed'] else 1)
