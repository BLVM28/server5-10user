"""Move only explicitly inventoried personal projects. Never touches public data."""
from pathlib import Path
import hashlib,json,os,shutil,zipfile,time
H=Path('/storage2/2026contest/server5/s5_10usr')
assert Path.cwd().resolve()==H
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def safe(p):
 assert H in p.resolve().parents and not p.is_symlink(),str(p)
 return p
def dump(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,indent=2)+'\n')
upload=H/'Desktop/kwt_eda_upload_20261101'
assert not (H/'v1').exists() and not (H/'v2').exists(),'Already installed; refusing overwrite'
z=zipfile.ZipFile(upload/'organized_sources_20261102.zip')
manifest=json.loads(z.read('delivery_manifest.json'))
for n,h in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
legacy={'v1':H/'kwt_eda_tmp_20261101/project','v2':H/'kwt_versions_20261101/v2'}
for version in ['v1','v2']:
 for n,h in manifest.items():
  if n.startswith(version+'/rtl/') and n.endswith('.sv'):
   old=legacy[version]/n.split('/',1)[1]
   assert old.exists() and sha(old)==h,'Legacy RTL differs: '+str(old)
for info in z.infolist():
 if info.is_dir() or info.filename=='delivery_manifest.json':continue
 p=safe(H/info.filename);p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists();p.write_bytes(z.read(info))
shared=H/'shared';shared.mkdir(exist_ok=True)
shutil.copytree(str(H/'kwt_eda_tmp_20261101/libraries'),str(shared/'libraries'))
config=json.loads((H/'kwt_versions_20261101/library_selection.json').read_text())
text=json.dumps(config,indent=2).replace(str(H/'kwt_eda_tmp_20261101/libraries'),str(shared/'libraries'))
(shared/'library_selection.json').write_text(text+'\n')
for version,tag in [('v1','v1_reset'),('v2','v2_eco5')]:
 old=H/'kwt_versions_20261101/v2/build'/tag;dest=H/version/'implementation/fix1'
 dest.mkdir(parents=True)
 for top in ['kwt_dot64','kwt_nice_core']:shutil.copytree(str(old/('synth_'+top)),str(dest/('synth_'+top)))
 dump(dest/'manifest.json',{'source_tag':tag,'qualification':'SMIC40 pre-layout, explicit test memory window, no real E203 CPU',
  'rtl_sha256':{str(p.relative_to(H/version)):sha(p) for p in sorted((H/version/'rtl').glob('*.sv'))},
  'mapped_sha256':{str(p.relative_to(dest)):sha(p) for p in dest.rglob('*') if p.is_file()},
  'source_path':str(old),'created':time.ctime()})
# Partition every historical version-specific build before archiving the old mixed tree.
moves=[]
def move(src,dest):
 safe(src);safe(dest);assert src.exists() and not dest.exists()
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(src),str(dest))
 moves.append({'from':str(src.relative_to(H)),'to':str(dest.relative_to(H))})
for p in list((H/'kwt_versions_20261101/v2/build').iterdir()):
 if p.name.startswith('v1_') or p.name.startswith('benchmark_v1'):
  move(p,H/'v1/history/mixed_tree_v1_builds'/p.name)
move(H/'kwt_eda_tmp_20261101',H/'v1/history/kwt_eda_tmp_20261101')
for p in list((H/'kwt_fixes_20261101/final').iterdir()):
 if p.name.startswith(('v1','v2')):move(p,H/p.name[:2]/'releases'/p.name)
for p in list((H/'kwt_versions_20261101').iterdir()):
 if p.name.startswith(('v1.zip','v1_package','baseline_')):move(p,H/'v1/history/version_release'/p.name)
move(H/'kwt_versions_20261101',H/'v2/history/kwt_versions_20261101')
move(H/'kwt_fixes_20261101',H/'v2/history/kwt_fixes_20261101')
for name in ['kwt_foundry_full_20261101','kwt_rtl_probe_20261101','kwt_rtl_probe_20261101_r2']:
 if (H/name).exists():move(H/name,H/'v1/history'/name)
dump(shared/'migration_20261102.json',{'moves':moves,'source_package_sha256':sha(upload/'organized_sources_20261102.zip'),'source_files':len(manifest)})
# Historical inputs/logs are compressed, then checked entry by entry before deleting loose copies.
for version in ['v1','v2']:
 folder=H/version/'history';archive=H/version/'history_20261102.zip';index={}
 with zipfile.ZipFile(str(archive),'w',zipfile.ZIP_DEFLATED,allowZip64=True) as out:
  for p in sorted(folder.rglob('*')):
   if p.is_symlink():
    name=str(p.relative_to(folder));data=os.readlink(str(p)).encode('utf-8')
    info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=0o120777<<16
    index[name]=hashlib.sha256(data).hexdigest();out.writestr(info,data)
   elif p.is_file():
    name=str(p.relative_to(folder));index[name]=sha(p);out.write(str(p),name)
  out.writestr('_sha256_manifest.json',json.dumps(index,indent=2))
 with zipfile.ZipFile(str(archive)) as check:
  for n,h in index.items():assert hashlib.sha256(check.read(n)).hexdigest()==h,n
 safe(folder);shutil.rmtree(str(folder));folder.mkdir()
 move(archive,folder/archive.name)
 dump(folder/'verification.json',{'files':len(index),'sha256':sha(folder/archive.name),'verified_all_members':True})
 print('HISTORY VERIFIED',version,len(index),flush=True)
# Component packs are separate from the live sources. No stale logs in RTL/TB packages.
for version in ['v1','v2']:
 root=H/version;packages=root/'packages';packages.mkdir()
 for name,folders in [('rtl',['rtl']),('tb',['tb']),('flow',['server_eda','py','integration']),('vectors',['vec'])]:
  with zipfile.ZipFile(str(packages/(name+'.zip')),'w',zipfile.ZIP_DEFLATED) as out:
   for folder in folders:
    for p in sorted((root/folder).rglob('*')):
     if p.is_file():out.write(str(p),str(p.relative_to(root)))
   if name=='flow':out.write(str(root/'Makefile'),'Makefile');out.write(str(root/'rtl.f'),'rtl.f')
 dump(packages/'sha256.json',{p.name:sha(p) for p in packages.glob('*.zip')})
 for folder in ['rtl','tb','server_eda','vec','py','integration','implementation','history','packages','reports','build']:
  d=root/folder;d.mkdir(exist_ok=True)
  if not (d/'README.md').exists():(d/'README.md').write_text('# '+folder+'\nSee ../SERVER_GUIDE.md for operation and scope.\n')
print('INSTALL PASS: v1 v2 shared; all legacy moves in shared/migration_20261102.json',flush=True)
