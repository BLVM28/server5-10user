"""Report-driven, topology-preserving delay/buffer ECO for flat Genus netlists.

Only buffers (BUFX2, Y=A, checked in the installed Liberty) are inserted.
Original RTL, clocks, logical functions, SDC and expected vectors stay unchanged.
This is a pre-layout experiment; fresh Tempus STA and SDF gates are mandatory.
"""
from pathlib import Path
import argparse,os,re,json,hashlib
R=Path(os.environ['KWT_VM_ROOT']);assert str(R)=='/home/eda/kwt_vm_20261101'
p=argparse.ArgumentParser();p.add_argument('version',choices=['v1','v2']);a=p.parse_args()
base=R/'results'/a.version;src=base/'synth_dot/mapped.v';s=src.read_text()
library_hashes={}
for corner in ['slow','fast']:
 lib=Path(os.environ['KWT_GPDK'])/'timing'/(corner+'_vdd1v0_basicCells.lib')
 text=lib.read_text();m=re.search(r'cell\s*\(\s*BUFX2\s*\)',text);assert m,'Required buffer is absent'
 next_cell=re.search(r'\bcell\s*\(',text[m.end():]);end=m.end()+next_cell.start() if next_cell else len(text)
 cell=text[m.end():end]
 assert re.search(r'function\s*:\s*"A"',cell),'BUFX2 is not an identity buffer'
 library_hashes[corner]=hashlib.sha256(lib.read_bytes()).hexdigest()
assert s.count('endmodule')==1 and 'kwt_eco_' not in s
pattern=re.compile(r'^\s*(\w+)\s+(\\\S+|\w+)\s*\((.*?)\);',re.M|re.S)
cells={}
for m in pattern.finditer(s):
 if m.group(1)=='module':continue
 name=m.group(2).lstrip('\\')
 pins=dict(re.findall(r'\.(\w+)\s*\(\s*([^()]*?)\s*\)',m.group(3)))
 assert name not in cells and pins,(name,pins)
 cells[name]={'match':m,'type':m.group(1),'identifier':m.group(2),'pins':pins.copy(),'old':pins.copy()}
assert len(cells)>1000
violations=set()
for corner in ['slow','fast']:
 text=(base/('sta_'+corner)/'constraints.rpt').read_text()
 violations.update(re.findall(r'^\s*(\S+)\s+[rf]\s+-[\d.]+\s+VIOLATED',text,re.M))
extra=base/'repair_margin_points.json'
if extra.exists():violations.update(json.loads(extra.read_text()))
newcells=[];wires=[];changes=[]
def chain(signal,count,label):
 for k in range(count):
  net='kwt_eco_'+label+'_'+str(k);assert net not in s and net not in wires
  wires.append(net);newcells.append('  BUFX2 '+net+'_buf(.A ('+signal+' ), .Y ('+net+' ));');signal=net
 return signal
# Bound reset leaf fanout, and add real cell delay for removal checks.
resets=sorted(n for n,c in cells.items() if c['pins'].get('RN')=='rst_n')
assert len(resets)>100
for i in range(0,len(resets),16):
 net=chain('rst_n',4,'reset'+str(i//16))
 for name in resets[i:i+16]:cells[name]['pins']['RN']=net;changes.append([name,'RN','rst_n',net])
# Add delay only at the data/control endpoints reported as failing.
for i,point in enumerate(sorted(p for p in violations if not p.endswith('/RN'))):
 name,pin=point.rsplit('/',1);assert pin in ['D','SI','SE'] and name in cells,point
 old=cells[name]['pins'][pin];assert "'" not in old,point
 net=chain(old,2,'hold'+str(i));cells[name]['pins'][pin]=net;changes.append([name,pin,old,net])
# Isolate the actual SS slew-violating high-fanout net with bounded leaves.
drv=(base/'sta_slow/drv.rpt').read_text()
bad=re.findall(r'^\s*(\S+/\S+)\s+[\d.]+\s+[\d.]+\s+-[\d.]+\s*$',drv,re.M)
nets=set()
for point in bad:
 name,pin=point.rsplit('/',1)
 if pin not in ['Y','Q','QN','CO','S']:
  assert name in cells and pin in cells[name]['pins'],point
  nets.add(cells[name]['pins'][pin])
for j,old in enumerate(sorted(nets)):
 loads=[(n,p) for n,c in sorted(cells.items()) for p,x in c['pins'].items() if x==old and p not in ['Y','Q','QN','CO','S']]
 assert len(loads)>8
 for i in range(0,len(loads),8):
  net=chain(old,1,'slew'+str(j)+'_'+str(i//8))
  for name,pin in loads[i:i+8]:cells[name]['pins'][pin]=net;changes.append([name,pin,old,net])
for c in sorted(cells.values(),key=lambda c:c['match'].start(),reverse=True):
 if c['pins']==c['old']:continue
 text='\n  '+c['type']+' '+c['identifier']+' ('+', '.join('.'+p+' ('+n+' )' for p,n in c['pins'].items())+');'
 s=s[:c['match'].start()]+text+s[c['match'].end():]
# Declare before first use: Xcelium rejects late declarations after implicit nets.
header=re.search(r'\bmodule\s+kwt_dot64\s*\([\s\S]*?\);',s);assert header
s=s[:header.end()]+'\n  wire '+', '.join(wires)+';\n'+s[header.end():]
s=s.replace('endmodule','\n'+'\n'.join(newcells)+'\nendmodule')
out=base/'eco_dot';out.mkdir(exist_ok=False)
(out/'mapped.v').write_text(s)
(out/'changes.json').write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(s.encode()).hexdigest(),'library_sha256':library_hashes,'original_cells':len(cells),'added_buffers':len(newcells),'reset_endpoints':len(resets),'reported_hold_endpoints':len(violations),'changes':changes},indent=2)+'\n')
print(a.version,'ECO buffers',len(newcells),'reset endpoints',len(resets),flush=True)
