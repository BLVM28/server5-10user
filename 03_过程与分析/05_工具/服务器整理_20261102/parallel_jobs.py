from pathlib import Path
import subprocess,json,time,zipfile,hashlib
H=Path('/storage2/2026contest/server5/s5_10usr');assert Path.cwd().resolve()==H
with zipfile.ZipFile(str(H/'Desktop/kwt_eda_upload_20261101/parallel_flow.zip')) as z:
 for n in z.namelist():
  p=(H/n).resolve();assert H in p.parents and n.startswith(('v1/','v2/'));p.write_bytes(z.read(n))
report=[]
def job(v,args):
 log=H/v/'reports'/('parallel_%02d_%s.log'%(len(report),args[0]));print('START',v,args,flush=True);start=time.time()
 with log.open('w') as f:r=subprocess.run(['make']+args,cwd=str(H/v),stdout=f,stderr=subprocess.STDOUT,timeout=10800)
 report.append({'version':v,'args':args,'exit':r.returncode,'seconds':round(time.time()-start,2),'log':str(log)})
 (H/'shared/parallel_jobs_20261102.json').write_text(json.dumps(report,indent=2)+'\n')
 print('END',report[-1],flush=True)
 if r.returncode:print(log.read_text()[-1800:],flush=True)
 return r.returncode==0
job('v2',['negative'])
rebuilt=job('v2',['synth'])
same=False
if rebuilt:
 job('v2',['timing','NETLIST=rebuilt'])
 # Only remove blank lines, indentation and full-line comments. Preserve every code character.
 def canonical(p):return '\n'.join(s.strip() for s in p.read_text().splitlines() if s.strip() and not s.lstrip().startswith('//'))
 proof={}
 for top in ['kwt_dot64','kwt_nice_core']:
  a=H/'v2/implementation/fix1'/('synth_'+top)/'mapped.v';b=H/'v2/implementation/rebuilt'/('synth_'+top)/'mapped.v'
  proof[top]={'identical_code_lines':canonical(a)==canonical(b),'fix1_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'rebuilt_sha256':hashlib.sha256(b.read_bytes()).hexdigest()}
 same=all(x['identical_code_lines'] for x in proof.values())
 (H/'shared/rebuild_comparison.json').write_text(json.dumps(proof,indent=2)+'\n');print('REBUILD_CODE_IDENTICAL',same,flush=True)
job('v2',['waves'])
for args in [['env'],['compile'],['run'],['sweep']]:job('v1',args)
job('v2',['gate','JOBS=8'])
job('v2',['gate','JOBS=8','VEC='+str(H/'v2/vec/real_speech/worst')])
job('v1',['gate','JOBS=8'])
if rebuilt and not same:job('v2',['gate','JOBS=8','NETLIST=rebuilt','VEC='+str(H/'v2/vec/real_speech/worst')])
print('PARALLEL JOBS FINISHED',all(x['exit']==0 for x in report),flush=True)
