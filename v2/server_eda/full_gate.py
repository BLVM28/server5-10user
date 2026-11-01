"""One external-interface full matrix with real standard/SRAM timing models and SDF."""
from pathlib import Path
import argparse,subprocess,os,re,json,shutil,hashlib
R=Path(__file__).resolve().parents[1]
assert str(R).startswith('/storage2/2026contest/server5/s5_10usr/')
p=argparse.ArgumentParser();p.add_argument('--tag',default='v2_reset');a=p.parse_args();assert re.match(r'^\w+$',a.tag)
out=R/'build'/a.tag/'full_gate';out.mkdir(parents=True,exist_ok=True);(out/'tmp').mkdir(exist_ok=True)
net=out.parent/'synth_kwt_nice_core';shutil.copy2(str(net/'mapped.sdf'),str(out/'mapped.sdf'))
libs=json.loads((R.parent/'library_selection.json').read_text())
pub=Path('/storage1/admin_public_dir/SRAM_Lib_2025')
mac=[pub/m/'verilog'/(m+s) for m in ['RAMSP128X16','RAMSP1024X16'] for s in ['.v','_rtl.v']]
env=os.environ.copy()
for k in ['TMP','TEMP','TMPDIR']:env[k]=str(out/'tmp')
record={'netlist_sha256':hashlib.sha256((net/'mapped.v').read_bytes()).hexdigest(),'sdf_sha256':hashlib.sha256((net/'mapped.sdf').read_bytes()).hexdigest(),'scope':'one layer-0 matrix external interfaces, SS maximum SDF, real SRAM default timing models','stages':[]}
try:
 for name,cmd in [('compile',['vcs','-full64','-sverilog','+neg_tchk','-timescale=1ns/1ps','-top','tb_core_gate',libs['standard_verilog'],*mac,net/'mapped.v',R/'server_eda/tb_core_gate.sv','-o','simv']),('run',[out/'simv','+sdfverbose','+VEC_DIR='+str(R/'vec')])]:
  with (out/(name+'.log')).open('w') as f:x=subprocess.run([str(v) for v in cmd],cwd=str(out),env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
  t=(out/(name+'.log')).read_text(errors='replace');ok=x.returncode==0 and not re.search(r'Error:|Error-|Fatal:|FATAL|Timing violation',t)
  record['stages'].append({'name':name,'exit':x.returncode,'passed':ok});print('CORE_GATE',name,ok,flush=True)
  assert ok,t[-2500:]
 assert 'ALL PASS, 1/1' in t
 t=(out/'sdf_annotation.log').read_text();assert 'SDF annotation completed:' in t
 for field in ['errors','warnings']:
  m=re.search(r'Total '+field+r':\s*(\d+)',t);assert m and int(m.group(1))==0,'SDF '+field
 record['completed']=True
except Exception as e:record['completed']=False;record['error']=str(e);print(str(e)[-2500:],flush=True)
(out.parent/'full_gate_result.json').write_text(json.dumps(record,indent=2))
raise SystemExit(0 if record['completed'] else 1)
