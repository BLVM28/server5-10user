"""Server manual entry points. Logs are evidence; missing evidence is never PASS."""
from pathlib import Path
import argparse, hashlib, json, math, os, re, shutil, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1]
HOME=Path('/storage2/2026contest/server5/s5_10usr')
PUB=Path('/storage1/admin_public_dir/SRAM_Lib_2025')
OUT=ROOT/'build/manual'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def source_hashes():
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'rtl').glob('*.sv'))}
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def libs(): return json.loads((HOME/'shared/library_selection.json').read_text())
def run(cmd,d,log,marker=None,extra=None,timeout=3600):
    d.mkdir(parents=True,exist_ok=True);(d/'tmp').mkdir(exist_ok=True)
    env=os.environ.copy();env.update({k:str(d/'tmp') for k in ['TMP','TEMP','TMPDIR']})
    if shutil.which('lc_shell'):env['SYNOPSYS_LC_ROOT']=str(Path(shutil.which('lc_shell')).resolve().parent.parent)
    if extra:env.update(extra)
    f=d/(log+'.log')
    if f.exists(): f.rename(d/(log+'.'+str(int(time.time()*1000000))+'.log'))
    start=time.time()
    with f.open('w') as stream:
        r=subprocess.run([str(x) for x in cmd],cwd=str(d),env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
    s=f.read_text(errors='replace')
    ok=r.returncode==0 and not re.search(r'(?im)^Error[:\-]|Fatal:|FATAL|Timing violation|Timing Violation|\*E,|\*F,',s)
    if marker:ok=ok and marker in s
    rec={'command':[str(x) for x in cmd],'exit':r.returncode,'passed':bool(ok),'seconds':round(time.time()-start,3),'log':str(f.relative_to(ROOT)),'log_sha256':sha(f)}
    save(d/(log+'_result.json'),rec)
    if not ok:raise RuntimeError('FAILED '+str(f)+'\n'+s[-2500:])
    return s
def tops():
    return ['tb_kwt_arithmetic','tb_kwt_icb','tb_kwt_system']+([t for t in ['tb_kwt_overlap','tb_kwt_mul_pipeline'] if (ROOT/'tb'/(t+'.sv')).exists()])
def sources(top):
    files=[ROOT/n.strip() for n in (ROOT/'rtl.f').read_text().splitlines() if n.strip()]
    files += [PUB/m/'verilog'/(m+s) for m in ['RAMSP128X16','RAMSP1024X16'] for s in ['.v','_rtl.v']]
    files += [ROOT/'tb'/(top+'.sv')]
    if top=='tb_kwt_system':files += [ROOT/'server_eda/wave_dump.sv']
    return files
def signature(top): return {str(p):sha(p) for p in sources(top)}
def compile_one(top):
    d=OUT/'compile'/top
    stamp=d/'signature.json'
    sig=signature(top)
    if (d/'simv').exists() and stamp.exists() and json.loads(stamp.read_text())==sig:return
    run(['vcs','-full64','-sverilog','-debug_access+all','-timescale=1ns/1ps','-top',top,*(['-top','kwt_wave_dump'] if top=='tb_kwt_system' else []),
         '+define+KWT_USE_FOUNDRY_SRAM','+define+ARM_UD_MODEL',*sources(top),'-o','simv'],d,'compile')
    save(stamp,sig);print('COMPILE PASS '+top,flush=True)
def simulate(top,vec,label,wave=False):
    d=OUT/'runs'/label/top
    if (d/'verified.json').exists():(d/'verified.json').unlink()
    compile_one(top)
    cmd=[OUT/'compile'/top/'simv','+VEC_DIR='+str(vec.resolve())]
    if wave:cmd+=['+WAVES']
    s=run(cmd,d,'run','ALL PASS,')
    counts=re.findall(r'ALL PASS,\s*(\d+)/(\d+)',s)
    assert counts and all(int(x)==int(y)>0 for x,y in counts),'Incomplete test count'
    expected={'tb_kwt_system':29,'tb_kwt_arithmetic':260,'tb_kwt_icb':4,'tb_kwt_overlap':5,'tb_kwt_negative':58}
    if top in expected:assert any(int(x)==expected[top] for x,y in counts),'Unexpected test total'
    if top=='tb_kwt_mul_pipeline':assert 'total_checked=527566' in s,'Missing bubble/reset product accounting'
    result={'passed':True,'top':top,'counts':counts,'vector_dir':str(vec),'rtl_sha256':source_hashes(),
            'vectors_sha256':{f.name:sha(f) for f in sorted(vec.glob('*.hex'))},'log':str(d/'run.log'),'log_sha256':sha(d/'run.log')}
    matrices=re.findall(r'matrix layer (\d+) PASS core_cycles=(\d+) writes=(\d+)',s)
    result['matrix_cycles']=[{'layer':int(a),'core_cycles':int(b),'writes':int(c)} for a,b,c in matrices]
    save(d/'verified.json',result);print('FUNCTION PASS '+label+' '+top+' '+str(counts),flush=True)
    if matrices:
      cycles=[int(x[1]) for x in matrices]
      print('METRIC core_cycles min='+str(min(cycles))+' max='+str(max(cycles))+'; output writes=12672 words/matrix; bus timing follows this TB',flush=True)
    return result
def selected_netlist(name):
    n=ROOT/'implementation'/name
    m=json.loads((n/'manifest.json').read_text())
    assert m['rtl_sha256']==source_hashes(),'STA refused: RTL changed since selected netlist was built. Re-synthesize and close timing.'
    for f,h in m['mapped_sha256'].items():assert sha(n/f)==h,'Mapped artifact changed: '+f
    return n
def synthesize(period):
    l=libs();generation=str(int(time.time()*1000000));work=OUT/'synthesis'/generation
    for top in ['kwt_dot64','kwt_nice_core']:
      env={'KWT_ROOT':str(ROOT),'KWT_RTL_ROOT':str(ROOT),'KWT_TOP':top,'KWT_PERIOD':str(period),
           'KWT_STD_DB':l['standard']['ss'],'KWT_MIN_STD_DB':l['standard']['ff'],
           'KWT_SRAM_DBS':'|'.join(l['sram']['ss']),'KWT_MIN_SRAM_DBS':'|'.join(l['sram']['ff']),
           'KWT_HOLD_FIX':'1','KWT_OUTPUT_CAP':'0.002852'}
      raw=work/('raw_'+top)
      run(['dc_shell','-f',ROOT/'server_eda/manual_synth.tcl'],raw,'dc','SYNTHESIS_COMPLETED '+top,env)
      repaired=work/('synth_'+top);env['KWT_DDC']=str(raw/'mapped.ddc')
      run(['dc_shell','-f',ROOT/'server_eda/reset_repair_run.tcl'],repaired,'dc','RESET_REPAIR_COMPLETE '+top,env)
      if ROOT.name=='v2' and top=='kwt_nice_core':
        eco=work/'eco_core';env['KWT_DDC']=str(repaired/'mapped.ddc')
        run(['dc_shell','-f',ROOT/'server_eda/cap_eco5.tcl'],eco,'dc','ECO_REPAIR_COMPLETE '+top,env)
        for f in eco.iterdir():
          if f.is_file():shutil.copy2(str(f),str(repaired/f.name))
    dest=ROOT/'implementation/rebuilt'
    if dest.exists():dest.rename(ROOT/'implementation'/('previous_rebuilt_'+generation))
    dest.mkdir(parents=True)
    for top in ['kwt_dot64','kwt_nice_core']:shutil.copytree(str(work/('synth_'+top)),str(dest/('synth_'+top)))
    save(dest/'manifest.json',{'rtl_sha256':source_hashes(),'created':time.ctime(),'period_ns':period,
      'mapped_sha256':{str(p.relative_to(dest)):sha(p) for p in dest.rglob('*') if p.is_file()}})
    print('SYNTHESIS PASS. Timing is NOT yet qualified: make timing NETLIST=rebuilt; make gate NETLIST=rebuilt',flush=True)
def sta(period,name):
    n=selected_netlist(name);l=libs();result=[]
    stamp=OUT/('timing_'+name+'_'+str(period)+'.json')
    if stamp.exists():stamp.unlink()
    for top in ['kwt_dot64','kwt_nice_core']:
      for c in ['ss','ff']:
        d=OUT/'timing'/name/str(period)/(top+'_'+c)
        env={'KWT_ROOT':str(ROOT),'KWT_TOP':top,'KWT_CORNER':c,'KWT_STD_DB':l['standard'][c],
             'KWT_SRAM_DBS':'|'.join(l['sram'][c]),'KWT_NETLIST':str(n/('synth_'+top)/'mapped.v'),
             'KWT_PERIOD':str(period),'KWT_OUTPUT_CAP':'0.002852'}
        run(['pt_shell','-f',ROOT/'server_eda/manual_sta.tcl'],d,'pt','STA_COMPLETED '+top,env)
        text=(d/'metrics.txt').read_text();slacks=[float(x) for x in re.findall(r'slack=([-0-9.eE+]+)',text)]
        violations=[s.strip() for s in (d/'violations.rpt').read_text().splitlines() if 'VIOLATED' in s]
        assert len(slacks)==2 and all(math.isfinite(x) for x in slacks),'Invalid STA evidence'
        coverage=(d/'coverage.rpt').read_text()
        rec={'top':top,'corner':c,'period_ns':period,'frequency_mhz':1000/period,'slacks_ns':slacks,
             'violations':violations,'passed':min(slacks)>=0 and not violations,'coverage':coverage,
             'netlist_sha256':sha(n/('synth_'+top)/'mapped.v'),'sdf_sha256':sha(d/'mapped.sdf'),
             'directory':str(d)}
        result.append(rec);print('TIMING '+('PASS' if rec['passed'] else 'FAIL')+' '+top+' '+c+' '+str(slacks),flush=True)
    save(OUT/('timing_'+name+'_'+str(period)+'.json'),result)
    assert all(r['passed'] for r in result),'Timing constraint violation; inspect reports'
    return result
def gate(period,name,vec,jobs,probe_only=False):
    from concurrent.futures import ThreadPoolExecutor,as_completed
    n=selected_netlist(name);l=libs();results=[]
    timing=json.loads((OUT/('timing_'+name+'_'+str(period)+'.json')).read_text())
    for c in ['ss','ff']:
      sta_dir=OUT/'timing'/name/str(period)/('kwt_nice_core_'+c)
      assert (sta_dir/'mapped.sdf').exists(),'Run make timing with same PERIOD and NETLIST first'
      proof=[x for x in timing if x['top']=='kwt_nice_core' and x['corner']==c]
      assert len(proof)==1 and proof[0]['passed'],'No passing STA proof for this corner'
      assert proof[0]['netlist_sha256']==sha(n/'synth_kwt_nice_core/mapped.v'),'STA netlist is stale; rerun timing'
      assert proof[0]['sdf_sha256']==sha(sta_dir/'mapped.sdf'),'STA SDF changed; rerun timing'
      d=OUT/'gate'/name/str(period)/(vec.name+'_'+c);d.mkdir(parents=True,exist_ok=True)
      # VCS 2020 statically compiles SDF: install and audit it before compilation.
      shutil.copy2(str(sta_dir/'mapped.sdf'),str(d/'mapped.sdf'))
      mac=[PUB/m/'verilog'/(m+s) for m in ['RAMSP128X16','RAMSP1024X16'] for s in ['.v','_rtl.v']]
      defs=['+define+KWT_PERIOD_NS='+str(period)]+(['+define+KWT_SDF_MIN'] if c=='ff' else [])
      run(['vcs','-full64','-sverilog','+neg_tchk','-sdfretain','-timescale=1ns/1ps','-top','tb_core_all_gate',*defs,l['standard_verilog'],*mac,
          n/'synth_kwt_nice_core/mapped.v',ROOT/'server_eda/tb_core_all_gate.sv','-o','simv'],d,'compile')
      annotation=d/'sdf_annotation.log'
      ann=annotation.read_text(errors='replace');assert 'SDF annotation completed:' in ann
      for key in ['errors','warnings']:
        m=re.search(r'Total '+key+r':\s*(\d+)',ann);assert m and int(m.group(1))==0,'Compile SDF '+key
      compiled_sha256=sha(d/'simv')
      probe=d/'annotation_probe';probe.mkdir(parents=True,exist_ok=True)
      shutil.copy2(str(sta_dir/'mapped.sdf'),str(probe/'mapped.sdf'))
      run([d/'simv','+sdfverbose','+ANNOTATION_ONLY'],probe,'run','ANNOTATION_PROBE PASS')
      shutil.copy2(str(annotation),str(probe/'sdf_annotation.log'))
      ann=(probe/'sdf_annotation.log').read_text(errors='replace')
      assert 'SDF annotation completed:' in ann
      for key in ['errors','warnings']:
        m=re.search(r'Total '+key+r':\s*(\d+)',ann);assert m and int(m.group(1))==0,'Probe SDF '+key
      print('ANNOTATION PROBE PASS '+c,flush=True)
      if probe_only:continue
      def one(layer):
        w=d/('layer%02d'%layer);w.mkdir(parents=True,exist_ok=True)
        shutil.copy2(str(sta_dir/'mapped.sdf'),str(w/'mapped.sdf'))
        text=run(['nice','-n','10',d/'simv','+sdfverbose','+VEC_DIR='+str(vec.resolve()),'+LAYER='+str(layer)],w,'run','ALL PASS, 1/1')
        assert ('matrix gate layer '+str(layer)+' PASS writes=12672 transactions=24296') in text,'Incomplete matrix accounting'
        assert re.search(r'Doing SDF annotation[^\r\n]*Done',text),'Runtime did not apply compiled SDF'
        assert sha(d/'simv')==compiled_sha256,'Compiled simulation image changed'
        shutil.copy2(str(annotation),str(w/'sdf_annotation.log'))
        ann=(w/'sdf_annotation.log').read_text(errors='replace')
        assert 'SDF annotation completed:' in ann,'Missing SDF annotation'
        for key in ['errors','warnings']:
          m=re.search(r'Total '+key+r':\s*(\d+)',ann);assert m and int(m.group(1))==0,'SDF '+key+' not zero'
        item={'layer':layer,'passed':True,'directory':str(w),'log_sha256':sha(w/'run.log'),'annotation_sha256':sha(w/'sdf_annotation.log')}
        save(w/'verified.json',item);print('GATE LAYER PASS '+c+' '+str(layer),flush=True)
        return item
      with ThreadPoolExecutor(max_workers=jobs) as pool:
        records=[f.result() for f in as_completed([pool.submit(one,i) for i in range(12)])]
      assert sorted(x['layer'] for x in records)==list(range(12))
      result={'corner':c,'passed':True,'matrices':12,'layers':sorted(records,key=lambda x:x['layer']),
              'sdf_sha256':sha(sta_dir/'mapped.sdf'),'netlist_sha256':sha(n/'synth_kwt_nice_core/mapped.v'),
              'tb_sha256':sha(ROOT/'server_eda/tb_core_all_gate.sv'),'simv_sha256':compiled_sha256,
              'annotation_phase':'VCS compile; identical audit log copied to each independent runtime directory',
              'vectors_sha256':{p.name:sha(p) for p in vec.glob('*.hex')},'directory':str(d)}
      save(d/'verified.json',result);results.append(result);print('GATE PASS '+c+' 12/12 matrices, SDF errors=warnings=0',flush=True)
    return results
def main():
    p=argparse.ArgumentParser();p.add_argument('target');p.add_argument('--period',type=float,default=6.666667)
    p.add_argument('--jobs',type=int,default=4);p.add_argument('--netlist',default='fix1');p.add_argument('--vec',type=Path,default=ROOT/'vec')
    a=p.parse_args()
    assert ROOT.parent==HOME,'Run only from the organized v1/v2 under the authorized server home'
    assert math.isfinite(a.period) and a.period>0
    assert 1<=a.jobs<=16
    assert re.fullmatch(r'[A-Za-z0-9_]+',a.netlist)
    import fcntl
    lock=(ROOT/'.manual.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    OUT.mkdir(parents=True,exist_ok=True)
    if a.target=='env':
      for x in ['python3','make','vcs','dc_shell','pt_shell','verdi']:
        loc=shutil.which(x);print(x,loc);assert loc,'Missing tool '+x
      for f in [v for vs in [libs()['standard'].values(),sum(libs()['sram'].values(),[])] for v in vs]:assert Path(f).is_file(),f
      print('ENV PASS; source='+str(ROOT));return
    if a.target=='clean':
      # Archive logs/results, then discard only generated executables and waveforms.
      assert OUT.resolve()==ROOT/'build/manual' and ROOT in OUT.resolve().parents
      archive=ROOT/'reports'/('before_clean_'+str(int(time.time()*1000000)))
      for f in OUT.rglob('*'):
        if f.is_file() and f.suffix in ['.json','.log','.rpt','.txt']:
          dest=archive/f.relative_to(OUT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(str(f),str(dest))
      shutil.rmtree(str(OUT));print('CLEAN PASS; evidence preserved in '+str(archive));return
    if a.target=='compile':
      for t in tops():compile_one(t)
      return
    if a.target in ['run','regress','waves']:
      results=[]
      if a.target=='waves':results.append(simulate('tb_kwt_system',a.vec,'waves',True))
      else:
        for t in tops():results.append(simulate(t,a.vec,'default'))
        if a.target=='regress':
          for v in sorted((ROOT/'vec/real_speech').glob('*')):
            if v.is_dir() and (v/'matrix_sat.hex').exists():results.append(simulate('tb_kwt_system',v,v.name))
      save(OUT/(a.target+'_summary.json'),{'passed':True,'rtl_sha256':source_hashes(),'results':results})
      print('FUNCTION ALL PASS; '+str(len(results))+' suites. Not an E203 CPU/firmware acceptance test.',flush=True)
    elif a.target=='negative':simulate('tb_kwt_negative',a.vec,'negative')
    elif a.target=='synth':synthesize(a.period)
    elif a.target=='timing':sta(a.period,a.netlist)
    elif a.target=='gate':gate(a.period,a.netlist,a.vec,a.jobs)
    elif a.target=='probe':gate(a.period,a.netlist,a.vec,a.jobs,True)
    elif a.target=='sweep':
      for period in [6.666667,7.142857,8.0]:sta(period,a.netlist)
    elif a.target=='verdi':
      d=OUT/'runs/waves/tb_kwt_system';v=d/'waves.vcd'
      assert v.exists(),'Run make waves first'
      env=os.environ.copy();env.update({k:str(d/'tmp') for k in ['TMP','TEMP','TMPDIR']})
      subprocess.Popen(['verdi','-sv','+define+KWT_USE_FOUNDRY_SRAM','+define+ARM_UD_MODEL',*[str(f) for f in sources('tb_kwt_system')],'-top','tb_kwt_system','-ssf',str(v)],cwd=str(d),env=env,stdout=(d/'verdi.log').open('w'),stderr=subprocess.STDOUT)
      print('Verdi started; this command does not assert verification PASS.')
    elif a.target=='package':
      import zipfile
      package=ROOT/'packages';package.mkdir(exist_ok=True);manifest={}
      groups={'rtl':[ROOT/'rtl',ROOT/'rtl.f'],'tb':[ROOT/'tb'],
              'makefile':[ROOT/'Makefile',ROOT/'server_eda/Makefile'],
              'flow':[ROOT/'server_eda',ROOT/'integration',ROOT/'py'],
              'vectors':[ROOT/'vec']}
      for name,paths in groups.items():
        files=sorted(set(f for p in paths for f in (p.rglob('*') if p.is_dir() else [p]) if f.is_file() and '__pycache__' not in f.parts))
        dest=package/(name+'.zip');tmp=package/(name+'.tmp')
        with zipfile.ZipFile(str(tmp),'w',zipfile.ZIP_DEFLATED) as z:
          for f in files:z.write(str(f),str(f.relative_to(ROOT)))
        with zipfile.ZipFile(str(tmp)) as z:
          for f in files:assert hashlib.sha256(z.read(str(f.relative_to(ROOT)).replace('\\','/'))).hexdigest()==sha(f)
        tmp.replace(dest);manifest[name]={'sha256':sha(dest),'files':len(files)}
        print('PACKAGE PASS '+name+' files='+str(len(files)),flush=True)
      save(package/'manifest.json',manifest)
    elif a.target=='report':
      current_rtl=source_hashes();basic={};print('=== FUNCTION: current-source results ===')
      for f in sorted((OUT/'runs').glob('*/*/verified.json')):
        j=json.loads(f.read_text());ok=j.get('passed') and j.get('rtl_sha256')==current_rtl
        sig=OUT/'compile'/j['top']/'signature.json'
        ok=ok and sig.exists() and json.loads(sig.read_text())==signature(j['top'])
        ok=ok and all((Path(j['vector_dir'])/n).exists() and sha(Path(j['vector_dir'])/n)==h for n,h in j['vectors_sha256'].items())
        if j.get('log_sha256'):ok=ok and Path(j['log']).exists() and sha(Path(j['log']))==j['log_sha256']
        label=str(f.parent.relative_to(OUT/'runs'))
        print(('FUNCTION PASS ' if ok else 'STALE/FAIL ')+label+' counts='+str(j['counts']))
        if f.parent.parent.name=='default':basic[j['top']]=ok
        log=Path(j['log'])
        if log.exists():
          cycles=[int(x) for x in re.findall(r'matrix layer \d+ PASS core_cycles=(\d+)',log.read_text(errors='replace'))]
          if cycles:print('  METRIC core_cycles min=%d max=%d; 12672 output words/matrix'%(min(cycles),max(cycles)))
      print('=== TIMING: selected netlist / period ===')
      timing=OUT/('timing_'+a.netlist+'_'+str(a.period)+'.json');timing_ok=False
      if timing.exists():
        try:
          n=selected_netlist(a.netlist);records=json.loads(timing.read_text());timing_ok=len(records)==4
          for j in records:
            ok=j['passed'] and j['netlist_sha256']==sha(n/('synth_'+j['top'])/'mapped.v')
            timing_ok=timing_ok and ok
            print(('TIMING PASS ' if ok else 'TIMING STALE/FAIL ')+j['top']+' '+j['corner']+' MHz=%.3f setup=%+.6f ns hold=%+.6f ns'%(1000/j['period_ns'],*j['slacks_ns']))
        except Exception as e:
          timing_ok=False;print('TIMING STALE/FAIL '+str(e))
      else:print('TIMING NOT RUN: make timing')
      ok=all(basic.get(t,False) for t in tops()) and timing_ok
      print('BASIC CHECK '+('PASS' if ok else 'INCOMPLETE/FAIL')+' (RTL function + pre-layout STA only)')
      print('Optional full-layer gate status: see gate/.../verified.json; short probe is not full gate PASS.')
      print('SOC acceptance: PENDING actual shared-memory map, firmware and top-level run.')
    else:raise RuntimeError('Unknown target '+a.target)
if __name__=='__main__':
    try:main()
    except Exception as e:print('FAIL: '+str(e),file=sys.stderr);sys.exit(1)
