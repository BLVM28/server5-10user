"""Original E203 headers + own wrapper, full 29-scenario regression. Not a CPU test."""
from pathlib import Path
import zipfile,os,subprocess,re,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
assert str(ROOT.resolve()).startswith('/storage2/2026contest/server5/s5_10usr/')
out=ROOT/'build/e203_binding';out.mkdir(parents=True,exist_ok=True);inc=out/'include';inc.mkdir(exist_ok=True);(out/'tmp').mkdir(exist_ok=True)
with zipfile.ZipFile('/storage1/admin_public_dir/SOC_RTL_2025/e203_hbirdv2-master_1013_update_sim.zip') as z:
 for name in ['config.v','e203_defines.v']:
  hits=[n for n in z.namelist() if n.endswith('/rtl/e203/core/'+name)];assert len(hits)==1
  (inc/name).write_bytes(z.read(hits[0]))
s=(ROOT/'tb/tb_kwt_system.sv').read_text()
old='kwt_nice_core #(.MEM_BASE(BASE),.MEM_BYTES(BYTES),.W_BANK_AW(WAW),.PACK_LOW_FIRST(PACK)) dut(.*);';assert old in s
s=s.replace(old,'e203_subsys_nice_core dut(.*);').replace('dut.core.','dut.u_kwt.core.').replace('dut.c_sat','dut.u_kwt.c_sat').replace('dut.c_cycles','dut.u_kwt.c_cycles')
tb=out/'tb_binding.sv';tb.write_text(s)
sources=[ROOT/x.strip() for x in (ROOT/'rtl.f').read_text().splitlines() if x.strip()]+[ROOT/'integration/e203_subsys_nice_core.v']
public=Path('/storage1/admin_public_dir/SRAM_Lib_2025')
sources += [public/m/'verilog'/(m+x) for m in ['RAMSP128X16','RAMSP1024X16'] for x in ['.v','_rtl.v']]+[tb]
env=os.environ.copy()
for key in ['TMPDIR','TMP','TEMP']:env[key]=str(out/'tmp')
cmd=['vcs','-full64','-sverilog','-timescale=1ns/1ps','-top','tb_kwt_system','+define+KWT_USE_FOUNDRY_SRAM','+define+ARM_UD_MODEL','+define+SYNTHESIS','+incdir+'+str(inc),'+define+KWT_MEM_BASE=268435456','+define+KWT_MEM_BYTES=524288',*sources,'-o','simv']
for label,command in [('compile',cmd),('run',[out/'simv','+VEC_DIR='+str(ROOT/'vec')])]:
 with (out/(label+'.log')).open('w') as f:r=subprocess.run([str(x) for x in command],cwd=str(out),env=env,stdout=f,stderr=subprocess.STDOUT,timeout=900)
 text=(out/(label+'.log')).read_text(errors='replace');assert r.returncode==0 and not re.search(r'Error:|Error-|Fatal:|FATAL',text),text[-1500:]
assert 'ALL PASS, 29/29' in text,text[-1500:]
record={'pass':'29/29','qualification':'Original E203 headers and own NICE wrapper; not CPU execution','source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+list(inc.glob('*.v'))}}
(out/'results.json').write_text(json.dumps(record,indent=2)+'\n');print('ALL PASS, 29/29 E203 header/wrapper binding')
