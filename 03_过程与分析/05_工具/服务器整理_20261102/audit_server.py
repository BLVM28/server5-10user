from pathlib import Path
import json, os, shutil
H=Path('/storage2/2026contest/server5/s5_10usr')
assert Path.cwd().resolve()==H
print('TOOLS', {n:shutil.which(n) for n in ['python3','make','vcs','dc_shell','pt_shell','verdi','riscv-nuclei-elf-gcc','riscv64-unknown-elf-gcc']})
for root in ['kwt_versions_20261101','kwt_fixes_20261101','kwt_eda_tmp_20261101']:
 p=H/root
 print('ROOT',root,sorted(x.name for x in p.iterdir()))
 for n in ['v1','v2','project']:
  q=p/n
  if q.is_dir():
   print('PROJECT',str(q.relative_to(H)),sorted(x.name for x in q.iterdir()))
   b=q/'build'
   if b.is_dir():print('BUILDS',str(b.relative_to(H)),sorted(x.name for x in b.iterdir()))
for f in (H/'kwt_versions_20261101').rglob('library_selection.json'):
 print('LIBCFG',str(f.relative_to(H)),f.read_text())
pub=Path('/storage1/admin_public_dir')
print('PUBLIC_TOP',sorted(x.name for x in pub.iterdir()))
for p in pub.iterdir():
 if p.is_dir() and any(x in p.name.lower() for x in ['soc','rtl','2026']):
  print('PUBLIC_PLATFORM',p.name,sorted(x.name for x in p.iterdir()))
for tag in ['v1_reset','v2_eco5']:
 b=H/'kwt_versions_20261101/v2/build'/tag
 print('FINAL',tag,b.exists(), sorted(x.name for x in b.iterdir()) if b.exists() else [])
for p in (H/'kwt_fixes_20261101').glob('*.py'):
 if any(s in p.name for s in ['eco5','final','package']):print('HELPER',p.name)
