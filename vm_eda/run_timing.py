"""Cadence-native synthesis and independent per-corner STA, no foundry SRAM."""
from pathlib import Path
import os,subprocess,json,argparse,time,re,shutil
R=Path(os.environ['KWT_VM_ROOT']);assert str(R)=='/home/eda/kwt_vm_20261101'
p=argparse.ArgumentParser();p.add_argument('version',choices=['v1','v2']);a=p.parse_args()
env=os.environ.copy();env['KWT_VERSION']=a.version
base=R/'results'/a.version
history=base/'history';history.mkdir(parents=True,exist_ok=True)
stamp=str(int(time.time()*1000000))
for name in ['eco_dot','sta_eco_slow','sta_eco_fast','gate_eco_slow','gate_eco_fast','repair_margin_points.json','eco_run.json','timing_summary.json','summary.json']:
 if (base/name).exists():shutil.move(str(base/name),str(history/(name+'_'+stamp)))
stages=[]
jobs=[('synth_dot','genus','synth_dot.tcl',None)]+[('sta_'+c,'tempus','sta_dot.tcl',c) for c in ['slow','fast']]
for name,tool,script,corner in jobs:
 out=R/'results'/a.version/name
 if out.exists():
  history=R/'results'/a.version/'history';history.mkdir(parents=True,exist_ok=True)
  shutil.move(str(out),str(history/(name+'_'+str(int(time.time()*1000000)))))
 out.mkdir(parents=True,exist_ok=True)
 if corner:env['KWT_CORNER']=corner
 command=[tool,'-no_gui','-files',str(R/'flow'/script)]
 start=time.monotonic()
 with (out/'tool.log').open('w') as f:
  r=subprocess.run(command,cwd=str(out),env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
 s=(out/'tool.log').read_text(errors='replace');marker='KWT_GENUS_SYNTH_COMPLETE' if tool=='genus' else 'KWT_TEMPUS_STA_COMPLETE'
 ok=r.returncode==0 and marker in s and not re.search(r'(?:^Error\s*:|\*\*ERROR|\*E,)',s,re.M)
 stages.append({'name':name,'command':command,'exit':r.returncode,'execution_completed':ok,'seconds':time.monotonic()-start})
 (R/'results'/a.version/'timing_run.json').write_text(json.dumps(stages,indent=2)+'\n')
 print(a.version,name,'COMPLETE' if ok else 'FAILED',flush=True)
 if not ok:print(s[-8000:],flush=True);raise SystemExit(1)
print('Execution complete. Constraint closure must be evaluated from the reports.',flush=True)
