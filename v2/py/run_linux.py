"""Portable VCS / Xcelium regression. Xcelium command is supplied, not locally tested."""
import argparse,hashlib,json,os,re,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--sim',choices=['vcs','xrun'],default='vcs')
    p.add_argument('--tops',nargs='+',default=['tb_kwt_arithmetic','tb_kwt_icb','tb_kwt_system'])
    p.add_argument('--tag',default='linux')
    p.add_argument('--define',action='append',default=[])
    p.add_argument('--vectors',type=Path,default=ROOT/'vec')
    p.add_argument('--foundry',type=Path,help='SRAM_Lib_2025 root, read only')
    a=p.parse_args();out=ROOT/'build'/a.tag;out.mkdir(parents=True,exist_ok=True)
    (out/'tmp').mkdir(exist_ok=True)
    env=os.environ.copy()
    for k in ['TMP','TEMP','TMPDIR']:env[k]=str(out/'tmp')
    src=[ROOT/s for s in (ROOT/'rtl.f').read_text().splitlines() if s.strip()]
    defines=list(a.define)
    if a.foundry:
        defines+=['KWT_USE_FOUNDRY_SRAM','ARM_UD_MODEL']
        src += [a.foundry/m/'verilog'/(m+s) for m in ['RAMSP128X16','RAMSP1024X16'] for s in ['.v','_rtl.v']]
    else:src += [ROOT/'tb/kwt_sram_sim.sv']
    results={'simulator':a.sim,'defines':defines,'tests':[],
             'qualification':'functional simulation, not SoC or STA',
             'source_sha256':{str(s):hashlib.sha256(s.read_bytes()).hexdigest() for s in src}}
    def run(cmd,name):
        start=time.monotonic()
        r=subprocess.run(cmd,cwd=str(out),env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600)
        (out/(name+'.log')).write_bytes(r.stdout)
        text=r.stdout.decode(errors='replace')
        if r.returncode:raise RuntimeError(name+' exit '+str(r.returncode)+'\n'+text[-5000:])
        return text,time.monotonic()-start
    for top in a.tops:
        tb=ROOT/'tb'/(top+'.sv')
        results['source_sha256'][str(tb)]=hashlib.sha256(tb.read_bytes()).hexdigest()
        files=[str(s) for s in src]+[str(tb)]
        defs=['+define+'+d for d in defines]
        if a.sim=='vcs':
            run(['vcs','-full64','-sverilog','-timescale=1ns/1ps','-top',top,*defs,*files,'-o',top+'_sim'],top+'_compile')
            text,seconds=run([str(out/(top+'_sim')),'+VEC_DIR='+str(a.vectors.resolve())],top)
        else:
            text,seconds=run(['xrun','-64bit','-sv','-timescale','1ns/1ps','-top',top,
                              *defs,*files,'+VEC_DIR='+str(a.vectors.resolve())],top)
        markers=re.findall(r'ALL PASS,\s*(\d+)/(\d+)[^\r\n]*',text)
        if not markers or any(x!=y for x,y in markers) or re.search(r'Fatal|FATAL|\*E,|\*F,',text):
            raise RuntimeError('Missing/failed PASS check: '+top+'\n'+text[-5000:])
        print(top,markers,flush=True)
        results['tests'].append({'top':top,'pass_markers':markers,'wall_seconds':seconds})
    (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
