"""Identical fixed-latency BFM for both versions. Cycles, not invented silicon speed."""
from pathlib import Path
import argparse,subprocess,os,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
HOME=Path('/storage2/2026contest/server5/s5_10usr')
assert str(ROOT.resolve()).startswith(str(HOME)+'/')
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);a=p.parse_args()
template=(ROOT/'tb/tb_kwt_system.sv').read_text()
assert template.count('&&(rng[2:0]!=0)')==1 and template.count('wait_count<=rng[5:3]')==1
tb=template.replace('&&(rng[2:0]!=0)','').replace('wait_count<=rng[5:3]','wait_count<=2')
tb=tb.replace('module tb_kwt_system;', '''module tb_kwt_system;
  integer bench_cycle=0,bench_start=0,nice_latency=0;
  reg bench_seen=0;
''')
tb=tb.replace('  kwt_nice_core #','''
  always @(posedge nice_clk) begin
    bench_cycle<=bench_cycle+1;
    if(!nice_rst_n)bench_seen<=0;
    else begin
      if(nice_req_valid&&nice_req_ready)begin bench_start<=bench_cycle;bench_seen<=0;end
      if(nice_rsp_valid&&!bench_seen)begin nice_latency<=bench_cycle-bench_start;bench_seen<=1;end
    end
  end
  kwt_nice_core #''')
tb=tb.replace('core_cycles=%0d writes=%0d",layer,dut.c_cycles,write_acks-start_writes',
              'core_cycles=%0d writes=%0d nice_cycles=%0d",layer,dut.c_cycles,write_acks-start_writes,nice_latency')
record={'clock_period_ns':10,'memory_wait_count':2,'request_backpressure':False,'nice_cycle_definition':'accepted request edge to first sampled response-valid edge, excludes deliberate result backpressure','tb_sha256':hashlib.sha256(tb.encode()).hexdigest(),'versions':{}}
public=Path('/storage1/admin_public_dir/SRAM_Lib_2025')
macro=[public/m/'verilog'/(m+s) for m in ['RAMSP128X16','RAMSP1024X16'] for s in ['.v','_rtl.v']]
for version,rtlroot in [('v1',a.baseline.resolve()),('v2',ROOT)]:
 assert str(rtlroot).startswith(str(HOME)+'/')
 out=ROOT/'build'/('benchmark_'+version);out.mkdir(parents=True,exist_ok=True);(out/'tmp').mkdir(exist_ok=True)
 (out/'tb_kwt_system.sv').write_text(tb)
 env=os.environ.copy()
 for k in ['TMP','TEMP','TMPDIR']:env[k]=str(out/'tmp')
 sources=[rtlroot/s.strip() for s in (rtlroot/'rtl.f').read_text().splitlines() if s.strip()]
 commands=[['vcs','-full64','-sverilog','-timescale=1ns/1ps','-top','tb_kwt_system','+define+KWT_USE_FOUNDRY_SRAM','+define+ARM_UD_MODEL',*sources,*macro,out/'tb_kwt_system.sv','-o','simv'],[out/'simv','+VEC_DIR='+str(ROOT/'vec')]]
 for name,cmd in zip(['compile','run'],commands):
  with (out/(name+'.log')).open('w') as f:r=subprocess.run([str(x) for x in cmd],cwd=str(out),env=env,stdout=f,stderr=subprocess.STDOUT,timeout=900)
  text=(out/(name+'.log')).read_text(errors='replace')
  assert r.returncode==0 and not re.search(r'Error:|Error-|Fatal:|FATAL',text),text[-1500:]
 assert 'ALL PASS, 29/29' in text,text[-1500:]
 rows=[{'layer':int(l),'cycles':int(c),'writes':int(w),'nice_cycles':int(n)} for l,c,w,n in re.findall(r'matrix layer (\d+) PASS core_cycles=(\d+) writes=(\d+) nice_cycles=(\d+)',text)]
 assert len(rows)==14 and all(d['writes']==12672 for d in rows)
 record['versions'][version]={'rows':rows,'rtl_sha256':{s.name:hashlib.sha256(s.read_bytes()).hexdigest() for s in sources}}
 print(version,'ALL PASS, 29/29','cycles',[d['cycles'] for d in rows],flush=True)
record['first_12_layer_cycles']={v:sum(d['cycles'] for d in obj['rows'][:12]) for v,obj in record['versions'].items()}
record['first_12_layer_nice_cycles']={v:sum(d['nice_cycles'] for d in obj['rows'][:12]) for v,obj in record['versions'].items()}
(ROOT/'build/benchmark_comparison.json').write_text(json.dumps(record,indent=2)+'\n')
print('BENCHMARK_COMPLETE',record['first_12_layer_cycles'],flush=True)
