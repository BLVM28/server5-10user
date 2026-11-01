from pathlib import Path
import hashlib,json,zipfile,os,re,urllib.parse
R=Path(__file__).resolve().parents[3];A=R/'99_归档/20261101_整理'
sha=lambda b:hashlib.sha256(b).hexdigest()
protected=json.loads((A/'protected_before.json').read_text(encoding='utf8'))
for n,h in protected.items():assert sha((R/n).read_bytes())==h,n
archives=json.loads((A/'archives.json').read_text(encoding='utf8'))
for item in archives:
 p=R/item['archive'];assert sha(p.read_bytes())==item['sha256'],p
 with zipfile.ZipFile(p) as z:
  manifest=json.loads(z.read('ARCHIVE_MANIFEST.json'))
  for n,m in manifest.items():assert sha(z.read(n))==m['sha256'],n
plan=json.loads((A/'cleanup_plan.json').read_text(encoding='utf8'))
for item in plan['archived_files_to_remove']:assert not (R/item['path']).exists(),item['path']
for n in plan['cache_trees_to_remove']:assert not (R/n).exists(),n
exempt=['01_核心参考','过程与分析/05_工具/tf24_env','过程与分析/05_工具/python_runtimes','过程与分析/05_工具/checkpoint_deps','过程与分析/05_工具/vnc_client_deps']
dirs=[];docs=[];missing=[];bad=[];checked=0
for b,ds,fs in os.walk(R):
 p=Path(b);n=p.relative_to(R).as_posix()
 if n=='01_核心参考':ds[:]=[];continue
 if n in exempt:ds[:]=[]
 dirs.append(n)
 if 'README.md' not in fs:missing.append(n)
 for f in fs:
  if f.endswith('.md'):docs.append(p/f)
for p in docs:
 s=p.read_text(encoding='utf-8-sig')
 for target in re.findall(r'\]\(([^)]+)\)',s):
  target=target.strip().strip('<>')
  if re.match(r'^(https?://|mailto:|#)',target):continue
  target=urllib.parse.unquote(target.split('#',1)[0])
  if not target:continue
  q=(p.parent/target).resolve();checked+=1
  if not q.exists():bad.append({'document':p.relative_to(R).as_posix(),'target':target})
result={'protected_file_hashes_unchanged':len(protected),'verified_archives':len(archives),'archived_files_removed':len(plan['archived_files_to_remove']),'own_directories_with_readme':len(dirs)-len(missing),'readme_missing':missing,'local_markdown_links_checked':checked,'broken_links':bad,'exempt_trees':exempt,'qualification':'Documentation/organization audit, not a new RTL or EDA simulation.'}
(A/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
assert not missing and not bad
