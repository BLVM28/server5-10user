"""Upload-only FTP; new connection per upload avoids the server idle timeout."""
import ftplib,getpass,json,sys,time
from pathlib import Path
secret=getpass.getpass('FTP Linux password (memory only): ')
print('READY',flush=True)
for line in sys.stdin:
 req=json.loads(line)
 if req['op']=='quit':break
 try:
  remote=req['remote'];assert remote.startswith('kwt_eda_upload_20261101/') and '..' not in remote
  p=Path(req['local']);start=time.time()
  with ftplib.FTP() as ftp:
   ftp.connect('icdesigns0.nicu.cn',18888,timeout=120);ftp.login('s5_10usr',secret)
   with p.open('rb') as f:reply=ftp.storbinary('STOR '+remote,f,blocksize=65536)
   print(json.dumps({'reply':reply,'bytes':p.stat().st_size,'seconds':round(time.time()-start,2),'remote':remote}),flush=True)
 except Exception as e:print(json.dumps({'error':str(e)}),flush=True)
secret=None
