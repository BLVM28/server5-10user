from pathlib import Path
import subprocess,json,time,zipfile
H=Path('/storage2/2026contest/server5/s5_10usr');assert Path.cwd().resolve()==H
for attempt in range(240):
 if 'JOBS FINISHED' in (H/'jobs_20261102.log').read_text():break
 time.sleep(15)
else:raise RuntimeError('Main regression did not finish within one hour')
with zipfile.ZipFile(str(H/'Desktop/kwt_eda_upload_20261101/extended_tests_r2.zip')) as z:
 for n in z.namelist():
  p=(H/n).resolve();assert H in p.parents and n.startswith('v2/');p.write_bytes(z.read(n))
steps=[['negative'],['synth'],['timing','NETLIST=rebuilt'],['gate','NETLIST=rebuilt','VEC='+str(H/'v2/vec/real_speech/worst')]]
report=[]
for i,args in enumerate(steps):
 log=H/'v2/reports'/('post_%02d.log'%i);print('START',args,flush=True);start=time.time()
 with log.open('w') as f:r=subprocess.run(['make']+args,cwd=str(H/'v2'),stdout=f,stderr=subprocess.STDOUT,timeout=7200)
 report.append({'args':args,'exit':r.returncode,'seconds':round(time.time()-start,2),'log':str(log)})
 (H/'shared/post_jobs_20261102.json').write_text(json.dumps(report,indent=2)+'\n')
 print('END',report[-1],flush=True)
 if r.returncode:print(log.read_text()[-1800:],flush=True)
print('POST FINISHED',all(x['exit']==0 for x in report),flush=True)
