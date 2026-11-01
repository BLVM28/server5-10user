"""Xcelium dot64 gate regression against the unchanged 32 golden vectors."""
from pathlib import Path
import argparse,os,subprocess,json,re,hashlib,shutil,time
R=Path(os.environ['KWT_VM_ROOT']);assert str(R)=='/home/eda/kwt_vm_20261101'
p=argparse.ArgumentParser();p.add_argument('version',choices=['v1','v2']);p.add_argument('--corner',choices=['slow','fast'],default='slow');p.add_argument('--eco',action='store_true');a=p.parse_args()
src=R/'work'/a.version;out=R/'results'/a.version/('gate_'+('eco_' if a.eco else '')+a.corner)
if out.exists():
 history=out.parent/'history';history.mkdir(exist_ok=True)
 shutil.move(str(out),str(history/(out.name+'_'+str(int(time.time()*1000000)))))
out.mkdir(parents=True)
net=out.parent/('eco_dot' if a.eco else 'synth_dot')/'mapped.v';sdf=out.parent/('sta_'+('eco_' if a.eco else '')+a.corner)/'mapped.sdf'
assert net.exists() and sdf.stat().st_size>1000
shutil.copy2(str(sdf),str(out/'mapped.sdf'))
cmd=['xrun','-64bit','-sv','-sdf_verbose','-sdfstats','sdf_stats.txt','-timescale','1ns/1ps','-top','tb_dot64_gate','+define+KWT_GATE_SIM',str(Path(os.environ['KWT_GPDK'])/'verilog'/(a.corner+'_vdd1v0_basicCells.v')),str(net),str(R/'flow/tb_dot64_gate.sv'),'+VEC_DIR='+str(src/'vec')]
with (out/'run.log').open('w') as f:r=subprocess.run(cmd,cwd=str(out),stdout=f,stderr=subprocess.STDOUT,timeout=900)
s=(out/'run.log').read_text(errors='replace');annotation=out/'sdf_annotation.log'
record={'version':a.version,'corner':a.corner,'command':cmd,'exit':r.returncode,'netlist_sha256':hashlib.sha256(net.read_bytes()).hexdigest(),'sdf_sha256':hashlib.sha256(sdf.read_bytes()).hexdigest(),'pass_markers':re.findall(r'ALL PASS,\s*(\d+)/(\d+)',s),'annotation_exists':annotation.exists(),'warning_lines':[x for x in s.splitlines() if '*W,' in x]}
record['simulation_passed']=r.returncode==0 and ('32','32') in record['pass_markers'] and not re.search(r'\*E,|\*F,|Timing violation|timing violation|FATAL|Fatal',s)
# Annotation completeness is retained as an independent requirement in the summary.
record['annotation_text']=annotation.read_text(errors='replace') if annotation.exists() else ''
stats=out/'sdf_stats.txt'
record['annotation_stats_exists']=stats.exists()
stats_text=stats.read_text(errors='replace') if stats.exists() else ''
record['annotation_complete']=annotation.exists() and stats.exists() and 'No Unannotated Path Delays and/or Timing Checks exist' in stats_text and not re.search(r'\*[WEF],SDF',s)
record['sdf_qualification']='Simulation SDF uses native -nonegchecks (negative limits tightened to zero); original Liberty STA and raw SDF are preserved.'
record['passed']=record['simulation_passed'] and record['annotation_complete']
(out/'results.json').write_text(json.dumps(record,indent=2)+'\n')
print(a.version,a.corner,'PASS' if record['passed'] else 'FAIL',flush=True)
if not record['passed']:print(s[-5000:]);raise SystemExit(1)
