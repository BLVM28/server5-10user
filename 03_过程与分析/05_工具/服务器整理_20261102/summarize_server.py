"""Re-audit only our own reports and sources. Raw foundry files stay on server."""
from pathlib import Path
import hashlib,json,re,time
H=Path('/storage2/2026contest/server5/s5_10usr');assert Path.cwd().resolve()==H
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
summary={'date':'2026-11-02','scope':'Accelerator RTL and pre-layout mapped implementation; NOT real E203 SoC acceptance','versions':{}}
for v in ['v1','v2']:
 root=H/v;out=root/'build/manual';record={'functional':[],'timing':[],'gate':[]}
 rtl={str(p.relative_to(root)):sha(p) for p in sorted((root/'rtl').glob('*.sv'))}
 for f in sorted((out/'runs').glob('*/*/verified.json')):
  j=json.loads(f.read_text());assert j['passed'] and j['rtl_sha256']==rtl
  log=Path(j['log']);text=log.read_text();assert 'ALL PASS,' in text and not re.search(r'Fatal:|FATAL|Timing violation',text)
  for n,h in j['vectors_sha256'].items():assert sha(Path(j['vector_dir'])/n)==h
  top=j['top'];sig=json.loads((out/'compile'/top/'signature.json').read_text())
  for n,h in sig.items():assert sha(Path(n))==h,'Compiled source changed: '+n
  record['functional'].append({'name':str(f.parent.relative_to(out/'runs')),'counts':j['counts'],'log_sha256':sha(log)})
 for f in sorted(out.glob('timing_*.json')):
  for j in json.loads(f.read_text()):
   assert j['passed'] and not j['violations'] and min(j['slacks_ns'])>=0
   d=Path(j['directory']);assert sha(d/'mapped.sdf')==j['sdf_sha256']
   assert 'STA_COMPLETED '+j['top'] in (d/'pt.log').read_text()
   measured=[float(x) for x in re.findall(r'slack=([-0-9.eE+]+)',(d/'metrics.txt').read_text())]
   assert measured==j['slacks_ns']
   record['timing'].append({k:j[k] for k in ['top','corner','period_ns','slacks_ns','netlist_sha256','sdf_sha256']})
 for f in sorted((out/'gate').glob('*/*/*/verified.json')):
  j=json.loads(f.read_text());assert j['passed'] and j['matrices']==12 and len(j['layers'])==12
  assert sorted(x['layer'] for x in j['layers'])==list(range(12))
  for layer in j['layers']:
   d=Path(layer['directory']);assert sha(d/'run.log')==layer['log_sha256']
   assert sha(d/'sdf_annotation.log')==layer['annotation_sha256']
   text=(d/'run.log').read_text();assert 'ALL PASS, 1/1' in text
   ann=(d/'sdf_annotation.log').read_text()
   for key in ['errors','warnings']:
    m=re.search(r'Total '+key+r':\s*(\d+)',ann);assert m and int(m.group(1))==0
  record['gate'].append({'name':str(f.parent.relative_to(out/'gate')),'matrices':12,'corner':j['corner'],'sdf_sha256':j['sdf_sha256'],'netlist_sha256':j['netlist_sha256']})
 assert len(record['timing'])>=12,'Missing period/corner sweep'
 assert len(record['gate'])>=(4 if v=='v2' else 2),'Missing full 12-layer SDF corners/vectors'
 assert any(x['name']=='negative/tb_kwt_negative' and x['counts']==[['58','58']] for x in record['functional']) if v=='v2' else True
 record['rtl_sha256']=rtl;summary['versions'][v]=record
 print('AUDIT',v,'FUNCTION_SUITES',len(record['functional']),'STA_CASES',len(record['timing']),'GATE_MATRICES',sum(x['matrices'] for x in record['gate']),flush=True)
summary['pending']=['Official selected 600 cases and final evaluation environment','Actual E203 top, 512KiB shared-memory map/implementation, startup/linker/driver run','Top-level area/power/timing under actual SoC constraints']
summary['conservative_clock']={'accelerator_mhz':125,'basis':'same final v2 mapped netlist SS setup +1.333595 ns at 8 ns, FF hold +0.123025 ns','not_a_soc_clock_guarantee':True}
(H/'shared/verification_20261102.json').write_text(json.dumps(summary,indent=2)+'\n')
for v,j in summary['versions'].items():
 lines=['# '+v+' 服务器验证结果（2026-11-02）','','本报告由实际日志、源码/向量哈希、SDF 注释和 STA 结果重新核对生成。不是 E203 整机验收。','',
 '| 检查 | 本轮结果 |','|---|---|',
 '| 功能运行组数（包含基线、波形及独立异常组） | '+str(len(j['functional']))+'，各组完整计数通过 |',
 '| STA 拓扑×角×周期组合 | '+str(len(j['timing']))+'，setup/hold 非负且无 reported constraint violation |',
 '| 完整矩阵 SDF 执行数 | '+str(sum(x['matrices'] for x in j['gate']))+'，每角每组 12/12；SDF errors/warnings 均 0 |','',
 '## 核心时序：fix1 固定网表','','SMIC40 HVT + 实际 SRAM 库，SS=0.99V/125°C，FF=1.21V/−40°C。period 扫描不改变其他约束：uncertainty 0.1ns；I/O max/min 1.0/0.1ns；输入转换 0.1ns；输出负载 0.002852pF。没有 false path/multicycle/reset 例外。','',
 '| 周期 ns | 角 | setup ns | hold ns |','|---:|---|---:|---:|']
 for x in j['timing']:
  if x['top']=='kwt_nice_core':
   # Select records by the exact fixed mapped netlist hash, not by filenames alone.
   if x['netlist_sha256']==sha(H/v/'implementation/fix1/synth_kwt_nice_core/mapped.v'):
    lines.append('| '+str(x['period_ns'])+' | '+x['corner']+' | '+str(x['slacks_ns'][0])+' | '+str(x['slacks_ns'][1])+' |')
 lines+=['','## 功能和门级清单','']
 lines += ['- '+x['name']+': '+str(x['counts']) for x in j['functional']]
 lines += ['- SDF '+x['name']+': 12/12' for x in j['gate']]
 lines+=['','## 结论和边界','','当前 v2 加速器建议以 **125 MHz** 作为保守联调设置：SS setup +1.333595 ns，FF hold +0.123025 ns。150 MHz 通过，但 v2 SS setup 仅 +0.000262 ns，不能描述为裕量充足。这不是正式 E203 SoC 的保证频率。',
 '','原版 600 条本地数值验证的最大层汇总 NRMSE=0.03891237%，本轮服务器 RTL 使用其导出的 13 组代表/最差激活；并未声称 600 条音频全部完成 HDL。Dense1 输出矩阵，yes/no 标签属于完整原模型。',
 '','仍缺正式共享 SRAM 实现及地址、E203 固件/启动/linker 与真实 SoC 仿真、官方最终 600 例及顶层 PPA。公共 `e203_soc_top.v:135–170` 中 sysmem 仍为读零占位连接。当前不能保证比赛全部任务已验收，也不能以有限回归承诺所有输入“万无一失”。',
 '','## 目录迁移及日志','','历史文件分别存于各版 history/history_20261102.zip：v1 2091、v2 3357 个条目逐项 SHA 校验后收起散文件。迁移路径见 ../shared/migration_20261102.json；原正式 ZIP 保持原字节。',
 '','第一次 12 层串行门级运行因耗时改为逐层独立并行，未完成运行不计入 PASS。原日志保留，说明在 ../shared/serial_gate_superseded.txt。首次并行流程的 SDF 静态编译位置和 RETAIN 处理未满足严格检查，亦未计入；最终流程按工艺角编译并使用 -sdfretain、+neg_tchk，保存共享编译注释证据及逐层运行日志。12 并发仿真在各自目录运行，使用较低调度优先级；检查标准未减少。',
 '','完整机器记录：../shared/verification_20261102.json。原始命令日志在 reports/，细分日志在 build/manual/。手动运行方法见 SERVER_GUIDE.md。','']
 (H/v/'SERVER_RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
print('REPORT AUDIT PASS',flush=True)
