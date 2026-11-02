from pathlib import Path
import hashlib,json,zipfile
R=Path.cwd();D=R/'03_过程与分析/05_工具/服务器整理_20261102'
files=[]
for v in ['v1','v2']:
 root=R/v
 files += [p for p in root.iterdir() if p.is_file()]
 for directory in ['rtl','tb','py','integration','server_eda','vec','06_xcelium','dist']:
  files += [p for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
 for directory in ['implementation','reports','history','releases','packages']:
  files.append(root/directory/'README.md')
 # Publish the evidence/source alongside both trees, but not duplicated captures or build products.
 if v=='v2':
  files += [p for p in (root/'validation_real_speech_20261102').rglob('*') if p.is_file() and 'rtl' not in p.relative_to(root/'validation_real_speech_20261102').parts]
manifest={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
(D/'source_sync_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
with zipfile.ZipFile(D/'final_source_sync.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(set(files)):
  # Fixed vectors were already transferred and validated. Send the new README only.
  if p.suffix=='.hex' and '/vec/' in p.as_posix():continue
  z.write(p,p.relative_to(R).as_posix())
 z.write(D/'source_sync_manifest.json','shared/source_sync_manifest.json')
 root_readme=(D/'server_docs/README.md').read_text().replace('make gate JOBS=4','make report')
 z.writestr('README.md',root_readme)
 z.write(R/'shared/README.md','shared/README.md')
print('SOURCE_FILES',len(manifest),'UPLOAD_BYTES',(D/'final_source_sync.zip').stat().st_size)
