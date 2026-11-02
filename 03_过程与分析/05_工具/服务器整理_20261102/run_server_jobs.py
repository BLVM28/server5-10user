from pathlib import Path
import subprocess,json,time,zipfile
H=Path('/storage2/2026contest/server5/s5_10usr');assert Path.cwd().resolve()==H
assert 'INSTALL PASS:' in (H/'organize_20261102_r2.log').read_text(),'Installation incomplete'
with zipfile.ZipFile(str(H/'Desktop/kwt_eda_upload_20261101/flow_update_r2.zip')) as z:
 for n in z.namelist():
  p=(H/n).resolve();assert H in p.parents and n.startswith(('v1/','v2/'))
  p.write_bytes(z.read(n))
jobs=[('v2',['env']),('v2',['clean']),('v2',['compile']),('v2',['run']),('v2',['regress']),
      ('v2',['sweep']),('v2',['gate']),('v2',['gate','VEC='+str(H/'v2/vec/real_speech/worst')]),
      ('v2',['waves']),('v1',['env']),('v1',['compile']),('v1',['run']),('v1',['sweep']),('v1',['gate'])]
report=[]
for i,(v,args) in enumerate(jobs):
 log=H/v/'reports'/('%02d_'%i+'_'.join(x.split('=')[0] for x in args)+'.log')
 log.parent.mkdir(exist_ok=True);start=time.time()
 print('START',i,v,args,flush=True)
 with log.open('w') as f:r=subprocess.run(['make']+args,cwd=str(H/v),stdout=f,stderr=subprocess.STDOUT,timeout=7200)
 item={'version':v,'args':args,'exit':r.returncode,'seconds':round(time.time()-start,2),'log':str(log)};report.append(item)
 (H/'shared/jobs_20261102.json').write_text(json.dumps(report,indent=2)+'\n')
 print('END',item,flush=True)
 if r.returncode:print(log.read_text()[-1200:],flush=True)
print('JOBS FINISHED',all(x['exit']==0 for x in report),flush=True)
