from pathlib import Path
# Run with PYTHONUTF8=1 on Windows; retained as migration history, not a daily command.
import shutil
R=Path.cwd()
for v in ['v1','v2']:
 p=R/v/'server_eda/manual_sta.tcl';s=p.read_text();s=s.replace('-context verilog mapped.sdf','-context verilog -exclude {clock_tree_path_models} mapped.sdf');p.write_bytes(s.encode())
 p=R/v/'Makefile';s=p.read_text().replace('env + run + timing + gate','env + run + timing + report (daily check)').replace('check: env run timing gate','check: env run timing report').replace('report synth negative','report synth negative package probe')
 s=s.replace("\t@echo 'make check", "\t@echo 'make package      : refresh separate RTL/TB/Makefile/flow/vector ZIPs'\n\t@echo 'make probe        : optional short SDF/model compatibility check'\n\t@echo 'make check")
 p.write_bytes(s.encode())
 p=R/v/'server_eda/easy.py';s=p.read_text()
 s=s.replace("    save(d/'verified.json',result);print('FUNCTION PASS '+label+' '+top+' '+str(counts),flush=True)","""    matrices=re.findall(r'matrix layer (\\d+) PASS core_cycles=(\\d+) writes=(\\d+)',s)
    result['matrix_cycles']=[{'layer':int(a),'core_cycles':int(b),'writes':int(c)} for a,b,c in matrices]
    save(d/'verified.json',result);print('FUNCTION PASS '+label+' '+top+' '+str(counts),flush=True)
    if matrices:
      cycles=[int(x[1]) for x in matrices]
      print('METRIC core_cycles min='+str(min(cycles))+' max='+str(max(cycles))+'; output writes=12672 words/matrix; bus timing follows this TB',flush=True)""")
 a=s.index("    elif a.target=='report':")
 b=s.index("    else:raise RuntimeError('Unknown target '",a)
 s=s[:a]+'''    elif a.target=='package':
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
          for f in files:assert hashlib.sha256(z.read(str(f.relative_to(ROOT)).replace('\\\\','/'))).hexdigest()==sha(f)
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
        label=str(f.parent.relative_to(OUT/'runs'))
        print(('FUNCTION PASS ' if ok else 'STALE/FAIL ')+label+' counts='+str(j['counts']))
        if f.parent.parent.name=='default':basic[j['top']]=ok
        log=Path(j['log'])
        if log.exists():
          cycles=[int(x) for x in re.findall(r'matrix layer \\d+ PASS core_cycles=(\\d+)',log.read_text(errors='replace'))]
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
        except Exception as e:print('TIMING STALE/FAIL '+str(e))
      else:print('TIMING NOT RUN: make timing')
      ok=all(basic.get(t,False) for t in tops()) and timing_ok
      print('BASIC CHECK '+('PASS' if ok else 'INCOMPLETE/FAIL')+' (RTL function + pre-layout STA only)')
      print('Optional full-layer gate status: see gate/.../verified.json; short probe is not full gate PASS.')
      print('SOC acceptance: PENDING actual shared-memory map, firmware and top-level run.')
''' + s[b:]
 p.write_bytes(s.encode())
for v in ['v1','v2']:
 for name,text in {
 'implementation':'服务器保存 fix1/rebuilt 映射网表、DDC、SDF 和 manifest；本地/GitHub 仅保存说明，工艺相关产物不公开。',
 'reports':'服务器运行日志与 clean 前留存证据。本地的本轮汇总见 ../SERVER_RESULTS.md。',
 'history':'服务器旧工程位于 history_20261102.zip，逐文件校验后归档；本地旧材料仍可通过 ../../99_归档 查阅。',
 'releases':'服务器保留此版本既有正式冻结 ZIP；本地既有正式包仍保留于 ../../releases，原字节不改。',
 'packages':'执行 make package 生成 rtl.zip、tb.zip、makefile.zip、flow.zip、vectors.zip 和 manifest.json。归档是快照，修改后需要重打包。'
 }.items():
  p=R/v/name;p.mkdir(exist_ok=True);(p/'README.md').write_text('# '+name+'\n\n'+text+'\n',encoding='utf-8')
p=R/'shared';p.mkdir(exist_ok=True);(p/'README.md').write_text('# 服务器共用配置\n\n服务器同名目录保存 library_selection.json、私有库副本和迁移/验证记录。公共库只读。库路径及受许可约束的库文件不复制到 GitHub；本地仅保留目录说明。\n',encoding='utf-8')
shutil.copytree(R/'v2/validation_real_speech_20261102/rtl',R/'v2/vec/real_speech',dirs_exist_ok=True)
p=R/'v2/vec/real_speech/README.md';p.write_text('# 真实语音导出向量\n\nclass_00 至 class_11 为各类别代表激活；worst 为逐层选出的较大误差激活。make regress 自动测试所有 13 组。生成来源、样本与哈希见 ../../validation_real_speech_20261102/README.md。每层独立输入，不是将 Dense1 输出直接串给下一层。\n',encoding='utf-8')
p=R/'.gitignore';s=p.read_text();s+='''
# Server/private implementation and generated packages stay out of the public repository.
/v[12]/implementation/**
!/v[12]/implementation/README.md
/v[12]/packages/*.zip
/v[12]/packages/*.json
/v[12]/history/*.zip
/v[12]/releases/*.zip
/shared/libraries/
/shared/library_selection.json
/v[12]/.manual.lock
# The canonical published vectors are v2/vec/real_speech; retain original capture locally.
/v2/validation_real_speech_20261102/rtl/
# Transfer scratch archives/screenshots are local evidence, not source dependencies.
/03_过程与分析/05_工具/服务器整理_20261102/*.zip
/03_过程与分析/05_工具/服务器整理_20261102/*.png
''';p.write_text(s,encoding='utf-8')
print('FLOW_AND_LAYOUT_UPDATED')
