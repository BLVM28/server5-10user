from pathlib import Path
import subprocess,time,json
H=Path('/storage2/2026contest/server5/s5_10usr');assert Path.cwd().resolve()==H
assert all('ANNOTATION PROBE PASS '+c in (H/'v2/reports/retain_verified_probe.log').read_text() for c in ['ss','ff'])
results=[]
for v,vec in [('v2',H/'v2/vec'),('v2',H/'v2/vec/real_speech/worst'),('v1',H/'v1/vec')]:
 log=H/v/'reports'/('final_gate_'+vec.name+'.log');start=time.time();print('START',v,vec.name,flush=True)
 with log.open('w') as f:
  p=subprocess.run(['make','gate','JOBS=12','VEC='+str(vec)],cwd=str(H/v),stdout=f,stderr=subprocess.STDOUT,timeout=7200)
 results.append({'version':v,'vectors':str(vec),'exit':p.returncode,'seconds':round(time.time()-start,2),'log':str(log)})
 (H/'shared/final_gate_jobs.json').write_text(json.dumps(results,indent=2)+'\n')
 print('END',results[-1],flush=True)
 if p.returncode:print(log.read_text()[-2000:],flush=True);break
print('FINAL GATES FINISHED',len(results)==3 and all(x['exit']==0 for x in results),flush=True)
