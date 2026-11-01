"""Package generated deliverables and selected actual verification logs, no tools."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
files=[]
for directory in ['rtl','tb','py','integration','06_xcelium','vec']:
    files += [p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files += [p for p in ROOT.iterdir() if p.is_file() and p.suffix in ('.md','.f','.sh','.txt')]
for tag in ['final_regression','fallback_swap','activation_rtl','driver','structure_ascii']:
    folder=ROOT/'build'/tag
    files += [p for p in folder.glob('*') if p.is_file() and p.suffix in ('.log','.json','.txt','.f','.sv')]
files += [ROOT/'build/activation_smoke.log',ROOT/'build/server_evidence.json']
files=sorted(set(files));assert all(p.exists() for p in files)
manifest={'format':'kwt-rtl-delivery-v1','sha256':{
    str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
out=ROOT/'dist';out.mkdir(exist_ok=True)
path=out/'kwt_rtl_v1.zip'
with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:z.write(p,str(p.relative_to(ROOT)).replace('\\','/'))
    z.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(path) as z:
    assert z.testzip() is None
    for name,h in manifest['sha256'].items():assert hashlib.sha256(z.read(name)).hexdigest()==h
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
sha=hashlib.sha256(path.read_bytes()).hexdigest()
(out/'kwt_rtl_v1.zip.sha256').write_text(sha+'  kwt_rtl_v1.zip\n',encoding='ascii')
print('ALL PASS, %d/%d packaged file hashes'%(len(files),len(files)))
print(path.name,path.stat().st_size,'bytes',sha)
