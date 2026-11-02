"""Official upload-only FTP. No RETR command; credentials stay in memory."""
import ftplib,getpass,json,sys,time
from pathlib import Path
password=getpass.getpass('FTP Linux password (not saved): ')
ftp=ftplib.FTP();ftp.connect('icdesigns0.nicu.cn',18888,timeout=30)
print('FTP welcome',ftp.getwelcome(),flush=True)
ftp.login('s5_10usr',password);password=None
print(json.dumps({'pwd':ftp.pwd(),'entries':ftp.nlst()}),flush=True)
for line in sys.stdin:
    req=json.loads(line)
    if req['op']=='quit':break
    if req['op']=='mkdir':
        name=req['name'];assert name.isascii() and '/' not in name and '..' not in name
        print(ftp.mkd(name),flush=True)
    elif req['op']=='upload':
        remote=req['remote'];assert remote.startswith('kwt_eda_upload_20261101/') and '..' not in remote
        p=Path(req['local']);total=[0];started=time.monotonic()
        def progress(block):
            total[0]+=len(block)
        with p.open('rb') as f:reply=ftp.storbinary('STOR '+remote,f,blocksize=65536,callback=progress)
        print(json.dumps({'reply':reply,'bytes':total[0],'seconds':round(time.monotonic()-started,2),'remote':remote}),flush=True)
    else:raise ValueError('Unsupported operation')
ftp.quit()
