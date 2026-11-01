"""Read/hash/archive first; emit an explicit plan. Deletion uses native PowerShell."""
from pathlib import Path
import hashlib,json,zipfile,os
R=Path(__file__).resolve().parents[3]
A=R/'99_归档/20261101_整理';A.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(R).as_posix()
def files(p):return sorted(x for x in p.rglob('*') if x.is_file())
protected={}
for name in ['01_核心参考','v1/rtl','v1/tb','v1/py','v1/vec','v1/integration','v2/rtl','v2/tb','v2/py','v2/vec','v2/integration']:
 for p in files(R/name):
  if '__pycache__' not in p.parts and p.suffix.lower()!='.md':protected[rel(p)]=sha(p)
for name in ['releases/20261101_v2/v1.zip','releases/20261101_v2/v2.zip','releases/20261101_fix1/v1_fix1.zip','releases/20261101_fix1/v2_fix1.zip']:
 protected[name]=sha(R/name)
(A/'protected_before.json').write_text(json.dumps(protected,ensure_ascii=False,indent=2),encoding='utf8')
groups={};remove=set();map_rows=[]
def group(name,paths,keep=lambda p:False):
 paths=sorted(set(paths));groups[name]=paths
 for p in paths:
  retained=keep(p)
  if not retained:remove.add(p)
  map_rows.append({'original':rel(p),'archive':rel(A/name),'member':rel(p),'retained':retained,'sha256':sha(p),'bytes':p.stat().st_size})
group('01_旧交接与临时输出.zip',list(R.glob('*.docx'))+[p for p in [R/'xvlog.log',R/'xvlog.pb'] if p.exists()]+files(R/'v1/dist'))
hist=['本轮查证_20261101','服务器取证_20261101','服务器验证_20261101','RTL实施取证_20261101','V2优化_20261101','VM验证_20261101']
keep_names={'本轮工作记录.md','实施台账增量.txt','server_snapshot_verification.json','31_eco5_detail.png','34_final_compact.png','36_gate_final.png','38_server_packages_final.png','final_check.log','final_flow_audit.log','release_final_check.log','server_snapshot_verification.json','06_nice_ports.png','07_nice_decode.png','18_sysmem_endpoint.png','19_cpu_binding_clock.png','35_e203_trees.png'}
group('02_历次取证与调试.zip',[p for n in hist for p in files(R/'过程与分析/05_工具'/n)],lambda p:p.name in keep_names)
rp=R/'releases/20261101_v2'
group('03_旧版本候选包.zip',[p for p in rp.glob('*.zip') if p.name not in ['v1.zip','v2.zip']])
for v in ['v1','v2']:
 group('04_'+v+'_构建记录.zip',files(R/v/'build'),lambda p:p.parent==R/v/'build' and p.suffix=='.json')
group('05_VM原始验证产物.zip',files(R/'vm_eda/results'),lambda p:p.suffix=='.json' or (p.suffix=='.rpt' and p.parent.name.startswith('sta_eco_')))
# Snapshot existing project documentation before updating navigation/status.
docs=[]
for base in ['v1','v2','vm_eda','releases','过程与分析/02_交给AI','过程与分析/03_我的工作区']:
 docs += [p for p in (R/base).rglob('*.md') if 'build' not in p.parts and '__pycache__' not in p.parts]
docs+=[R/'AGENT.md']
group('06_整理前文档快照.zip',docs,lambda p:True)
archive_summary=[]
for name,paths in groups.items():
 target=A/name;assert not target.exists(),target
 manifest={rel(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in paths}
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  for p in paths:z.write(p,rel(p))
  z.writestr('ARCHIVE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
 with zipfile.ZipFile(target) as z:
  assert set(z.namelist())==set(manifest)|{'ARCHIVE_MANIFEST.json'}
  for n,m in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==m['sha256'],n
 archive_summary.append({'archive':rel(target),'files':len(paths),'bytes':target.stat().st_size,'sha256':sha(target)})
 print('VERIFIED',name,len(paths),flush=True)
# Cache deletion is separate and explicitly has no backup (regenerable).
cache=R/'过程与分析/05_工具/uv_cache'
cache_entries=[]
for p in files(cache):cache_entries.append({'path':rel(p),'bytes':p.stat().st_size,'reason':'uv package download/unpack cache; installed environment retained'})
pycache=[]
for base in ['v1','v2','vm_eda']:
 for p in (R/base).rglob('__pycache__'):
  if p.is_dir():pycache.append(p)
for d in pycache:
 for p in files(d):cache_entries.append({'path':rel(p),'bytes':p.stat().st_size,'reason':'regenerable Python bytecode'})
plan={'root':str(R),'archived_files_to_remove':[{'path':rel(p),'sha256':sha(p)} for p in sorted(remove)],'cache_trees_to_remove':[rel(cache)]+[rel(p) for p in pycache],'prune_roots':['v1/build','v2/build','v1/dist','vm_eda/results']+['过程与分析/05_工具/'+h for h in hist]}
(A/'cleanup_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
(A/'archive_map.json').write_text(json.dumps(map_rows,ensure_ascii=False,indent=2),encoding='utf8')
(A/'cache_deletions.json').write_text(json.dumps(cache_entries,ensure_ascii=False,indent=2),encoding='utf8')
(A/'archives.json').write_text(json.dumps(archive_summary,ensure_ascii=False,indent=2),encoding='utf8')
print('PLAN',len(remove),'archived loose files;',len(cache_entries),'cache files;',sum(x['bytes'] for x in cache_entries),'logical cache bytes',flush=True)
