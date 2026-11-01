"""Repair VM dot64 maps, then independently recheck both corners."""
from pathlib import Path
import os,subprocess,json,argparse,re,time,shutil
R=Path(os.environ['KWT_VM_ROOT']);assert str(R)=='/home/eda/kwt_vm_20261101'
p=argparse.ArgumentParser();p.add_argument('version',choices=['v1','v2']);a=p.parse_args()
env=os.environ.copy();env.update(KWT_VERSION=a.version,KWT_ECO='1')
base=R/'results'/a.version
if (base/'eco_dot').exists():
 points=set()
 extra=base/'repair_margin_points.json'
 if extra.exists():points.update(json.loads(extra.read_text()))
 for corner in ['slow','fast']:
  folder=base/('sta_eco_'+corner)
  text=(folder/'constraints.rpt').read_text()
  points.update(re.findall(r'^\s*(\S+)\s+[rf]\s+-?[\d.]+\s+VIOLATED',text,re.M))
  near=folder/'near_hold.rpt'
  if near.exists():points.update(re.findall(r'^Endpoint:\s+(\S+)',near.read_text(),re.M))
 extra.write_text(json.dumps(sorted(points),indent=2)+'\n')
 history=base/'history';history.mkdir(exist_ok=True);stamp=str(int(time.time()*1000000))
 for name in ['eco_dot','sta_eco_slow','sta_eco_fast']:
  if (base/name).exists():shutil.move(str(base/name),str(history/(name+'_'+stamp)))
subprocess.run(['python3',str(R/'flow/repair_gpdk.py'),a.version],env=env,check=True)
subprocess.run(['python3',str(R/'flow/audit_eco.py'),a.version],env=env,check=True)
stages=[]
for corner in ['slow','fast']:
 env['KWT_CORNER']=corner;out=R/'results'/a.version/('sta_eco_'+corner);out.mkdir(exist_ok=False)
 cmd=['tempus','-no_gui','-files',str(R/'flow/sta_dot.tcl')]
 with (out/'tool.log').open('w') as f:r=subprocess.run(cmd,cwd=str(out),env=env,stdout=f,stderr=subprocess.STDOUT,timeout=900)
 s=(out/'tool.log').read_text(errors='replace');ok=r.returncode==0 and 'KWT_TEMPUS_STA_COMPLETE' in s and not re.search(r'\*\*ERROR|^Error\s*:',s,re.M)
 stages.append({'corner':corner,'exit':r.returncode,'execution_completed':ok})
 (out.parent/'eco_run.json').write_text(json.dumps(stages,indent=2)+'\n')
 print(a.version,corner,'ECO_STA_COMPLETE' if ok else 'FAILED',flush=True)
 if not ok:print(s[-5000:]);raise SystemExit(1)
