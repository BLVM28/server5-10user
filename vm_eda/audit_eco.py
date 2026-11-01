"""Independently compare each original cell connection after bypassing ECO buffers."""
from pathlib import Path
import os,re,json,argparse,hashlib
R=Path(os.environ['KWT_VM_ROOT'])
p=argparse.ArgumentParser();p.add_argument('version',choices=['v1','v2']);a=p.parse_args()
base=R/'results'/a.version
def parse(path):
 s=path.read_text();result={}
 for m in re.finditer(r'^\s*(\w+)\s+(\\\S+|\w+)\s*\((.*?)\);',s,re.M|re.S):
  if m.group(1)=='module':continue
  result[m.group(2)]=(m.group(1),dict(re.findall(r'\.(\w+)\s*\(\s*([^()]*?)\s*\)',m.group(3))))
 return result
old=parse(base/'synth_dot/mapped.v');new=parse(base/'eco_dot/mapped.v')
assert set(old).issubset(new)
aliases={}
for name in set(new)-set(old):
 cell,pins=new[name];assert name.startswith('kwt_eco_') and cell=='BUFX2' and set(pins)=={'A','Y'}
 assert pins['Y'] not in aliases
 aliases[pins['Y']]=pins['A']
def bypass(net):
 visited=set()
 while net in aliases:
  assert net not in visited;visited.add(net);net=aliases[net]
 return net
pins_checked=0
for name,(ref,pins) in old.items():
 nref,npins=new[name];assert ref==nref and set(pins)==set(npins)
 for pin,net in pins.items():
  assert bypass(npins[pin])==net,(name,pin,net,npins[pin]);pins_checked+=1
record={'passed':True,'original_cells_checked':len(old),'pins_checked':pins_checked,'identity_buffers_checked':len(aliases),'netlist_sha256':hashlib.sha256((base/'eco_dot/mapped.v').read_bytes()).hexdigest(),'scope':'Structural identity after bypassing library BUFX2 (Y=A); not a formal sequential equivalence run.'}
(base/'eco_dot/structural_audit.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
