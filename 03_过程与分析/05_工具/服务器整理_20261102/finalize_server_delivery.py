"""Apply only our source delivery inside the authorised home; run the short daily checks."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,zipfile,subprocess,time,shutil
H=Path('/storage2/2026contest/server5/s5_10usr');assert Path.cwd().resolve()==H
U=H/'Desktop/kwt_eda_upload_20261101'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(p):
 assert H in p.resolve().parents and not p.is_symlink(),str(p)
 return p
with zipfile.ZipFile(str(U/'final_delivery_bundle_r1.zip')) as z:
 manifest=json.loads(z.read('shared/source_sync_manifest.json'))
 for n,h in manifest.items():
  if n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
  else:assert sha(safe(H/n))==h,'Existing vector mismatch: '+n
 # Do not change any RTL/TB already used in the protected tests.
 for n in manifest:
  if '/rtl/' in n and n.endswith('.sv'):assert sha(H/n)==manifest[n],n
 for n in z.namelist():
  p=safe(H/n);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
for n,h in manifest.items():assert sha(H/n)==h,n
print('SOURCE SYNC PASS',len(manifest),'files',flush=True)
results={}
def check(v):
 root=H/v;log=root/'reports/final_daily_check.log';started=time.time()
 with log.open('w') as f:r=subprocess.run(['make','check'],cwd=str(root),stdout=f,stderr=subprocess.STDOUT,timeout=900)
 text=log.read_text();assert r.returncode==0 and 'BASIC CHECK PASS' in text,(v,text[-2500:])
 with (root/'reports/final_packages.log').open('w') as f:r=subprocess.run(['make','package'],cwd=str(root),stdout=f,stderr=subprocess.STDOUT,timeout=300)
 assert r.returncode==0,(v,'package')
 j={'passed':True,'seconds':round(time.time()-started,2),'log_sha256':sha(log),'source_files':sum(n.startswith(v+'/') for n in manifest)}
 print('DAILY CHECK PASS',v,j,flush=True)
 return v,j
with ThreadPoolExecutor(max_workers=2) as pool:
 for v,j in pool.map(check,['v1','v2']):results[v]=j
for n,h in manifest.items():assert sha(H/n)==h,n
(H/'shared/final_daily_verification.json').write_text(json.dumps({'source_files':len(manifest),'source_manifest_sha256':sha(H/'shared/source_sync_manifest.json'),'daily':results,'extended_gate':'NOT COMPLETED; optional, not part of daily acceptance'},indent=2)+'\n')
archive=H/'shared/job_logs_20261102';archive.mkdir(exist_ok=True)
for name in ['organize_20261102.log','organize_20261102_r2.log','jobs_20261102.log','post_jobs_20261102.log','parallel_jobs_20261102.log']:
 p=safe(H/name)
 if p.exists():assert not (archive/name).exists();shutil.move(str(p),str(archive/name))
(archive/'README.md').write_text('# Job logs\n\nMigration and experimental batch logs, including failed probes; not a blanket PASS statement. Current conclusions: v2/SERVER_RESULTS.md.\n')
print('FINAL DELIVERY PASS; full-layer SDF remains optional and not claimed.',flush=True)
