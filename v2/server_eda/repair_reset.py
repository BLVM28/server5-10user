"""Post-map reset min-delay repair; outputs a new tag and preserves original maps."""
from pathlib import Path
import json,os,subprocess,argparse,re,shutil
ROOT=Path(__file__).resolve().parents[1]
assert str(ROOT).startswith('/storage2/2026contest/server5/s5_10usr/')
p=argparse.ArgumentParser();p.add_argument('--source',default='v2_150');p.add_argument('--tag',default='v2_reset');p.add_argument('--period',type=float,default=6.666667);a=p.parse_args()
assert re.match(r'^\w+$',a.source) and re.match(r'^\w+$',a.tag) and a.source!=a.tag
libs=json.loads((ROOT.parent/'library_selection.json').read_text());record=[]
for top in ['kwt_dot64','kwt_nice_core']:
 out=ROOT/'build'/a.tag/('synth_'+top);out.mkdir(parents=True,exist_ok=True);(out/'tmp').mkdir(exist_ok=True)
 env=os.environ.copy();env.update({'KWT_ROOT':str(ROOT),'KWT_TOP':top,'KWT_STD_DB':libs['standard']['ss'],
 'KWT_MIN_STD_DB':libs['standard']['ff'],'KWT_SRAM_DBS':'|'.join(libs['sram']['ss']),
 'KWT_MIN_SRAM_DBS':'|'.join(libs['sram']['ff']),'KWT_DDC':str(ROOT/'build'/a.source/('synth_'+top)/'mapped.ddc'),
 'KWT_PERIOD':str(a.period),'KWT_OUTPUT_CAP':'0.002852','SYNOPSYS_LC_ROOT':str(Path(shutil.which('lc_shell')).resolve().parent.parent)})
 for k in ['TMPDIR','TEMP','TMP']:env[k]=str(out/'tmp')
 with (out/'dc.log').open('w') as f:r=subprocess.run(['dc_shell','-f',str(ROOT/'server_eda/reset_repair_run.tcl')],cwd=str(out),env=env,stdout=f,stderr=subprocess.STDOUT,timeout=900)
 s=(out/'dc.log').read_text();ok=r.returncode==0 and 'RESET_REPAIR_COMPLETE '+top in s and not re.search(r'^Error:',s,re.M)
 record.append({'top':top,'completed':ok});print('RESET_REPAIR',top,ok,flush=True)
 if not ok:raise RuntimeError(s[-2500:])
(ROOT/'build'/a.tag/'reset_repair_result.json').write_text(json.dumps({'completed':True,'source_tag':a.source,'period_ns':a.period,'stages':record,'source_synthesis':json.loads((ROOT/'build'/a.source/'synth_result.json').read_text())},indent=2))
