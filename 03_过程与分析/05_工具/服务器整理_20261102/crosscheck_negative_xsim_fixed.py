"""Independent XSim check. Only the generated TB's default vector path changes."""
from pathlib import Path
import hashlib,json,os,subprocess,time
ROOT=Path(__file__).resolve().parents[3]/'v2'
OUT=ROOT/'build/negative_crosscheck_20261102'
OUT.mkdir(parents=True,exist_ok=True)
tb=ROOT/'tb/tb_kwt_negative.sv'
data=tb.read_text().replace('if(!$value$plusargs("VEC_DIR=%s",dir))$fatal(1,"VEC_DIR required");',
                          'if(!$value$plusargs("VEC_DIR=%s",dir))dir="../../vec";')
(OUT/tb.name).write_text(data)
sources=[ROOT/n.strip() for n in (ROOT/'rtl.f').read_text().splitlines() if n.strip()]
sources += [ROOT/'tb/kwt_sram_sim.sv',OUT/tb.name]
(OUT/'sources.f').write_text('\n'.join('"'+os.path.relpath(p,OUT).replace('\\','/')+'"' for p in sources)+'\n')
report={'qualification':'Only generated TB default vector-directory fallback differs; RTL and checks unchanged',
        'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'original_tb_sha256':hashlib.sha256(tb.read_bytes()).hexdigest(),'steps':[]}
for tool,args in [('xvlog',['-sv','-f','sources.f']),
                  ('xelab',['work.tb_kwt_negative','-s','negative_sim','-debug','typical','-timescale','1ns/1ps']),
                  ('xsim',['negative_sim','-runall'])]:
    start=time.time();cmd=['cmd.exe','/d','/c','D:/vivado/Vivado/2023.2/bin/'+tool+'.bat']+args
    result=subprocess.run(cmd,cwd=OUT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600)
    (OUT/(tool+'.log')).write_bytes(result.stdout)
    report['steps'].append({'command':cmd,'exit':result.returncode,'seconds':round(time.time()-start,2)})
    assert result.returncode==0,result.stdout[-1200:]
    if tool=='xsim':assert b'ALL PASS, 58/58' in result.stdout and b'FATAL' not in result.stdout
report['passed']=True;(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print('XSIM ALL PASS, 58/58')
