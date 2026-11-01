"""Server-only regression/synthesis/STA driver. Never writes public libraries."""
from pathlib import Path
import argparse,hashlib,json,math,os,re,subprocess,time,sys,shutil
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'server_eda';OUT=ROOT/'build/server_eda'
HOME=Path('/storage2/2026contest/server5/s5_10usr')
assert str(ROOT.resolve()).startswith(str(HOME)+'/'), 'Server run must stay under the assigned home'
PUBLIC=Path('/storage1/admin_public_dir/SRAM_Lib_2025')
MACROS=[PUBLIC/m/'verilog'/(m+s) for m in ['RAMSP128X16','RAMSP1024X16'] for s in ['.v','_rtl.v']]

def main():
    p=argparse.ArgumentParser();p.add_argument('target',choices=['functional','activation','sram150','dot150','synth','sta','gate','summary'])
    p.add_argument('--libraries',type=Path,default=ROOT.parent/'library_selection.json')
    a=p.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    record={'target':a.target,'stages':[],'source_sha256':{str(s.relative_to(ROOT)):hashlib.sha256(s.read_bytes()).hexdigest() for s in (ROOT/'rtl').glob('*.sv')}}
    def run(cmd,out,label,extra=None,marker=None):
        out.mkdir(parents=True,exist_ok=True);(out/'tmp').mkdir(exist_ok=True)
        env=os.environ.copy()
        for key in ['TMPDIR','TEMP','TMP']:env[key]=str(out/'tmp')
        if shutil.which('lc_shell'):env['SYNOPSYS_LC_ROOT']=str(Path(shutil.which('lc_shell')).resolve().parent.parent)
        if extra:env.update(extra)
        start=time.monotonic()
        oldlog=out/(label+'.log')
        if oldlog.exists():
            history=out/'prior_logs';history.mkdir(exist_ok=True)
            shutil.copy2(str(oldlog),str(history/(label+'.'+str(int(time.time()*1000000))+'.log')))
        with (out/(label+'.log')).open('w') as f:
            result=subprocess.run([str(x) for x in cmd],cwd=str(out),env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
        text=(out/(label+'.log')).read_text(errors='replace')
        ok=result.returncode==0 and not re.search(r'(?m)^Error:|Fatal:|FATAL|\$fatal|Timing violation',text)
        if marker:ok=ok and marker in text
        item={'label':label,'cwd':str(out),'command':[str(x) for x in cmd],'exit':result.returncode,'seconds':round(time.monotonic()-start,3),'passed':bool(ok)}
        record['stages'].append(item);print(label,'PASS' if ok else 'FAIL',flush=True)
        if not ok:raise RuntimeError(text[-6000:])
        return text
    def vcs(top,files,defines,tag,plus):
        out=OUT/tag
        timing_flags=['+neg_tchk'] if 'KWT_GATE_SIM' in defines else []
        run(['vcs','-full64','-sverilog','-timescale=1ns/1ps','-top',top,*timing_flags,*['+define+'+d for d in defines],*files,'-o','simv'],out,'compile')
        text=run([out/'simv',*plus],out,'run',marker='ALL PASS,')
        markers=re.findall(r'ALL PASS,\s*(\d+)/(\d+)',text)
        if not markers or any(x!=y for x,y in markers):raise RuntimeError('Incomplete test accounting')
        record['stages'][-1]['pass_markers']=markers
    try:
        if a.target in ('functional','activation'):
            cmd=['python3',ROOT/'py/run_linux.py','--sim','vcs','--tag','server_'+a.target,'--foundry',PUBLIC]
            if a.target=='activation':cmd+=['--tops','tb_kwt_system','--vectors',ROOT/'vec/activation_smoke/rtl']
            run(cmd,OUT,'regression_'+a.target)
            result=ROOT/'build'/('server_'+a.target)/'results.json'
            assert result.exists();record['regression']=json.loads(result.read_text())
        elif a.target=='sram150':vcs('tb_sram_150',MACROS+[HERE/'tb_sram_150.sv'],[],a.target,[])
        elif a.target=='dot150':
            vcs('tb_dot64_gate',[ROOT/'rtl'/n for n in ['kwt_quantize.sv','kwt_mul16_pipe.sv','kwt_dot64.sv']]+[HERE/'tb_dot64_gate.sv'],[],a.target,['+VEC_DIR='+str(ROOT/'vec')])
        elif a.target in ('synth','sta','gate'):
            libs=json.loads(a.libraries.resolve().read_text());record['library_config']=libs
            def environment(top,corner):
                env={'KWT_ROOT':str(ROOT),'KWT_TOP':top,'KWT_CORNER':corner,'KWT_STD_DB':libs['standard'][corner],
                     'KWT_SRAM_DBS':'|'.join(libs['sram'][corner]),'KWT_NETLIST':str(OUT/('synth_'+top)/'mapped.v')}
                if a.target=='sta':
                    log=(OUT/('synth_'+top)/'dc.log').read_text()
                    cap=re.findall(r'four_pin_cap=([0-9.eE+-]+)',log)
                    assert len(cap)==1 and float(cap[0])>0,'Cannot recover exact DC output load'
                    env['KWT_OUTPUT_CAP']=cap[0]
                return env
            if a.target=='synth':
                for top in ['kwt_dot64','kwt_nice_core']:
                    run(['dc_shell','-f',HERE/'synth.tcl'],OUT/('synth_'+top),'dc',environment(top,'ss'),'SYNTHESIS_COMPLETED '+top)
            elif a.target=='sta':
                for top in ['kwt_dot64','kwt_nice_core']:
                    assert (OUT/('synth_'+top)/'mapped.v').exists()
                    for corner in ['ss','ff']:
                        out=OUT/('sta_'+top+'_'+corner)
                        run(['pt_shell','-f',HERE/'sta.tcl'],out,'pt',environment(top,corner),'STA_COMPLETED '+top)
                        record['stages'][-1]['metrics']=(out/'metrics.txt').read_text()
                        values=[float(x) for x in re.findall(r'slack=([0-9.eE+-]+)',record['stages'][-1]['metrics'])]
                        assert len(values)==2 and all(math.isfinite(x) for x in values),'Invalid timing metrics'
                        record['stages'][-1]['timing_slack_met']=all(x>=0 for x in values)
                record['timing_slack_met']=all(s['timing_slack_met'] for s in record['stages'])
            else:
                folder=OUT/'synth_kwt_dot64'
                assert (folder/'mapped.sdf').exists()
                (OUT/'gate').mkdir(parents=True,exist_ok=True)
                shutil.copy2(str(folder/'mapped.sdf'),str(OUT/'gate/mapped.sdf'))
                record['sdf_sha256']=hashlib.sha256((OUT/'gate/mapped.sdf').read_bytes()).hexdigest()
                vcs('tb_dot64_gate',[libs['standard_verilog'],folder/'mapped.v',HERE/'tb_dot64_gate.sv'],['KWT_GATE_SIM'],a.target,
                    ['+sdfverbose','+VEC_DIR='+str(ROOT/'vec')])
                annotation=OUT/'gate/sdf_annotation.log'
                assert annotation.exists(),'SDF annotation log is required'
                sdf_log=annotation.read_text(errors='replace')
                record['sdf_annotation_tail']=sdf_log[-3000:]
                assert 'SDF annotation completed:' in sdf_log,'Incomplete SDF annotation'
                for field in ['errors','warnings']:
                    count=re.search(r'Total '+field+r':\s*(\d+)',sdf_log)
                    assert count and int(count.group(1))==0,'SDF '+field+' not zero'
        else:
            results={f.stem:json.loads(f.read_text()) for f in OUT.glob('*_result.json')}
            (OUT/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
            for name,result in sorted(results.items()):
                print(name,'completed='+str(result.get('completed')))
                if 'timing_slack_met' in result:print('TIMING_SLACK_MET',result['timing_slack_met'])
                for stage in result.get('stages',[]):
                    if 'metrics' in stage:print(stage['cwd'],stage['metrics'].strip())
            return
        record['completed']=True
    except Exception as e:
        record['completed']=False;record['error']=str(e);print(str(e)[-6000:],flush=True)
    finally:
        if a.target!='summary':(OUT/(a.target+'_result.json')).write_text(json.dumps(record,indent=2)+'\n')
    raise SystemExit(0 if record['completed'] else 1)
if __name__=='__main__':main()
