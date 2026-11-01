"""Recheck the current audited ECO without changing the mapped topology."""
from pathlib import Path
import os,argparse,subprocess,json,re,shutil,time
R=Path(os.environ['KWT_VM_ROOT'])
p=argparse.ArgumentParser();p.add_argument('version',choices=['v1','v2']);a=p.parse_args()
base=R/'results'/a.version;env=os.environ.copy();env.update(KWT_VERSION=a.version,KWT_ECO='1')
subprocess.run(['python3',str(R/'flow/audit_eco.py'),a.version],check=True)
history=base/'history';history.mkdir(exist_ok=True);stamp=str(int(time.time()*1000000));rows=[]
for corner in ['slow','fast']:
 out=base/('sta_eco_'+corner)
 if out.exists():shutil.move(str(out),str(history/(out.name+'_'+stamp)))
 out.mkdir();env['KWT_CORNER']=corner
 with (out/'tool.log').open('w') as f:r=subprocess.run(['tempus','-no_gui','-files',str(R/'flow/sta_dot.tcl')],cwd=str(out),env=env,stdout=f,stderr=subprocess.STDOUT,timeout=900)
 s=(out/'tool.log').read_text(errors='replace');ok=r.returncode==0 and 'KWT_TEMPUS_STA_COMPLETE' in s and not re.search(r'\*\*ERROR|^Error\s*:',s,re.M)
 rows.append({'corner':corner,'exit':r.returncode,'execution_completed':ok})
 print(a.version,corner,'RECHECK',ok,flush=True)
 if not ok:raise SystemExit(s[-4000:])
(base/'eco_run.json').write_text(json.dumps(rows,indent=2)+'\n')
