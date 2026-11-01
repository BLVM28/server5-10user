"""Cross-check functional, structural, STA and fully annotated gate evidence."""
from pathlib import Path
import argparse,json,os,hashlib
from check_timing import inspect
R=Path(os.environ['KWT_VM_ROOT'])
p=argparse.ArgumentParser();p.add_argument('version',choices=['v1','v2']);a=p.parse_args()
b=R/'results'/a.version;src=R/'work'/a.version
f=json.loads((b/'functional/results.json').read_text())
rtl={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in (src/'rtl').glob('*.sv')}
assert rtl==f['source_sha256'],'RTL changed after functional regression'
assert f['completed'] and all(x['passed'] for x in f['stages'])
audit=json.loads((b/'eco_dot/structural_audit.json').read_text())
netsha=hashlib.sha256((b/'eco_dot/mapped.v').read_bytes()).hexdigest()
assert audit['passed'] and audit['netlist_sha256']==netsha
timing=inspect(b);assert timing['reported_constraints_met'],'STA or DRV failure'
gates=[]
for corner in ['slow','fast']:
 g=json.loads((b/('gate_eco_'+corner)/'results.json').read_text())
 c=json.loads((b/('sta_eco_'+corner)/'sdf_compatibility_audit.json').read_text())
 assert c['passed'] and c['other_delays_unchanged'] and c['simulation_sha256']==g['sdf_sha256']
 assert g['netlist_sha256']==netsha and g['sdf_sha256']==hashlib.sha256((b/('sta_eco_'+corner)/'mapped.sdf').read_bytes()).hexdigest()
 assert g['passed'] and g['annotation_complete'] and g['pass_markers']==[['32','32']]
 gates.append({k:g[k] for k in ['corner','passed','pass_markers','netlist_sha256','sdf_sha256','annotation_complete']})
summary={'version':a.version,'functional_passed':True,'functional_stages':[{ 'name':s['name'],'tests':s['details']['tests']} for s in f['stages']],'rtl_sha256':rtl,'structural_audit':audit,'timing':timing,'gate':gates,'completed':True,'qualification':'Behavioral-SRAM full accelerator RTL + GPDK045 dot64 pre-layout STA/SDF. Simulation SDF tightens negative timing limits to zero; raw SDF and original Liberty STA preserved. No CPU/full-model/post-route signoff.'}
(b/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(a.version,'ALL REQUIRED VM CHECKS PASS (limited scope stated in summary)',flush=True)
