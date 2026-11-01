"""Verify simulator compatibility changes only negative timing limits to zero."""
from pathlib import Path
import argparse,os,re,json,hashlib
R=Path(os.environ['KWT_VM_ROOT'])
p=argparse.ArgumentParser();p.add_argument('version',choices=['v1','v2']);a=p.parse_args()
def split_checks(s):
 spans=[]
 for m in re.finditer(r'\(TIMINGCHECK\b',s):
  i=m.start();depth=0
  for j in range(i,len(s)):
   if s[j]=='(':depth+=1
   elif s[j]==')':
    depth-=1
    if depth==0:spans.append((i,j+1));break
 checks=[s[a:b] for a,b in spans]
 for a,b in reversed(spans):s=s[:a]+' TIMINGCHECK_REMOVED '+s[b:]
 s=re.sub(r'\(DATE\s+"[^"]*"\)','(DATE IGNORED)',s)
 return re.sub(r'\s+',' ',s),checks
number=re.compile(r'(?<![A-Za-z0-9_])[-+]?\d*\.\d+(?:[eE][-+]?\d+)?')
def norm(s,clamp):
 def numeric(m):
  v=float(m.group());return format(max(0.0,v) if clamp else v,'.10g')
 return re.sub(r'\s+',' ',number.sub(numeric,s))
for corner in ['slow','fast']:
 d=R/'results'/a.version/('sta_eco_'+corner);raw=(d/'mapped_raw.sdf').read_text();sim=(d/'mapped.sdf').read_text()
 outside0,c0=split_checks(raw);outside1,c1=split_checks(sim)
 assert outside0==outside1,'Delay paths/header changed outside timing checks'
 assert len(c0)==len(c1)>0
 assert all(norm(x,True)==norm(y,False) for x,y in zip(c0,c1)),'Unexpected timing check change'
 count=sum(float(m.group())<0 for x in c0 for m in number.finditer(x))
 rec={'passed':True,'timingcheck_groups':len(c0),'negative_numeric_limits_tightened':count,'other_delays_unchanged':True,'raw_sha256':hashlib.sha256(raw.encode()).hexdigest(),'simulation_sha256':hashlib.sha256(sim.encode()).hexdigest()}
 (d/'sdf_compatibility_audit.json').write_text(json.dumps(rec,indent=2)+'\n');print(a.version,corner,json.dumps(rec),flush=True)
