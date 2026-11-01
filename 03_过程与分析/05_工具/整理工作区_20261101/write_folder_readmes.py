from pathlib import Path
import os,json
R=Path(__file__).resolve().parents[3]
LOG='工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。'
def link(folder,target):return os.path.relpath(R/target,R/folder).replace('\\','/')
def write(folder,body):
 p=R/folder/'README.md';p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(body.rstrip()+'\n\n'+LOG+'\n\n[返回工作区首页]('+link(folder,'README.md')+')\n',encoding='utf8')
rtl_rows=[
('kwt_nice_core.sv','NICE 请求/描述符控制','32 位指令与 rs1；描述符 8 字；选择描述符或 core 的访存；末次写完成才回应。状态 IDLE/FETCH/FETCH_WAIT/VALIDATE/START/RUN/RESPONSE。'),
('kwt_icb_master.sv','ICB 事务桥','请求寄存→SEND→WAIT_RSP→RETURN_RSP；单笔在途；读写均需应答；valid/ready 等待时命令不变；size 固定 2。'),
('kwt_linear_core.sv','整矩阵状态机','检查地址、装 X、按 32 个列组装 W/b、遍历 99 行/64 项，保持 8 路结果并分 4 字写回；管理错误与任务完成。'),
('kwt_x_buffer.sv','全部 X 缓存','6336 个 int16 放 7 个 SP1024；13 位线性索引，高 3 位选 bank，低 10 位是地址；读 bank 与 valid 寄存对齐。'),
('kwt_w_panel.sv','当前 8 列 W 缓存','8 个独立 bank，每 bank 服务一个 lane；读同一个 k 得 8 个 W；一个总线字可写两个不同 lane。默认每 bank SP128。'),
('kwt_mac8.sv','8 路原子广播/汇合','单个 X 广播、8 个 W/b 独立；bias 总线 256 位、W/Y 总线 128 位、完整 acc 总线 320 位；所有 lane 同时握手。'),
('kwt_dot64.sv','一个输出的点积','bias32 初始化 acc40；接受恰好 64 对 signed16；等待 mul_last 排空；量化后保持 out_y/out_acc 至接收。IDLE/RUN/ROUND/RESPONSE。'),
('kwt_mul16_pipe.sv','精确 signed16×16','输出完整 signed32，valid/last 与数据一致；不支持随意输出反压。v1 为一级，v2 为操作数/部分积/合并三级、II=1。'),
('kwt_quantize.sv','唯一结果量化点','acc40/F27 → Y16/F11；最近偶数舍入、int16 饱和；不改变中间乘积/累加精度。'),
('kwt_sp_ram.sv','宏适配','AW7/AW10 分别绑定 SP128/SP1024；CEN/GWEN/WEN 低有效、WEN16；行为仿真/厂商仿真/综合 cell 分支明确。')]
for v in ['v1','v2']:
 role='当前开发主线' if v=='v2' else '保守实现对照基线'
 write(v,f'''# {v}：{role}

固定任务 `X[99,64] × W[64,256] + b[256] → Y[99,256]`。这是本科第一 Dense 加速器，不是完整语音识别硬件。先读 [项目导读](../02_项目导读/README.md)。

| 目录/文件 | 功能 | 建议阅读顺序 |
|---|---|---|
| [rtl](rtl/README.md) | 10 个可综合模块，8 lane、15 个内部 SRAM 宏 | 先 linear_core，再 dot64/mac8，最后 NICE/ICB |
| [integration](integration/README.md) | E203 同名包装、RV32 驱动头、宏/时钟模板 | SoC 联调前必读，默认内存窗口关闭 |
| [tb](tb/README.md) | 算术、总线、矩阵/错误/复位测试 | 根据症状选层级，不用分类结果猜硬件错误 |
| [py](py/README.md) | 整数金模、转换、运行脚本 | 先 numeric_model，再 capture_activations |
| [vec](vec/README.md) | 固定 golden/权重/模型 smoke | 可以直接仿真，不必重生成 |
| [server_eda](server_eda/README.md) | 竞赛服务器专用综合/仿真流程 | 须使用实际服务器工具和库，勿在本地直接套跑 |
| [build](build/README.md) | 结果摘要/新的运行输出 | 历史完整构建已归档 |
| [dist](dist/README.md) | 历史打包脚本输出位置 | 正式交付以 ../releases 为准 |
| implementation_spec.md | 数值、状态、地址、错误的实现规格 | 精确契约 |
| rtl.f / sim.f / run.sh | 源文件顺序及 Linux 回归入口 | 加入正式平台 filelist 时核对路径 |
| REVISION_FIX1.md | 本轮实现修复说明 | fix1 没改 RTL 算法 |

当前时序/VM 结论以 [fix1 报告](../vm_eda/REPORT.md) 为准；validation.md、旧 server_eda/RESULTS.md 与 v2 阶段报告保留其历史日期，不代表最新完成度。正式 CPU/共享 RAM 和真实语音验证集仍待验收。

{'v2 相对 v1 使用三级精确乘法及相邻行计算/写回重叠，数值和外部 ABI 保持相同；固定等待 TB 的 12 次 NICE 周期减少 20.2065%，不能写成完整语音或 CPU 性能。' if v=='v2' else 'v1 保留一级寄存乘法和较保守的顺序调度，用来与 v2 作同条件对照；新增开发优先放在 v2，避免无意改变基线。'}

本地快速检查：`python {v}/py/run_xsim.py --tag learn --tops tb_kwt_arithmetic`（从工作区根执行）。私有 VM 用 `make -C flow {v}`，不是在 Windows 本目录执行。''')
 write(v+'/rtl',f'''# {v} RTL 模块

本目录只含硬件逻辑。顶层职责由 `kwt_nice_core` 负责，平台真正替换入口在 `../integration/e203_subsys_nice_core.v`；通过 `../rtl.f` 编译，TB 和 Python 不进综合。

| 文件 | 职责 | 主要接口/时序 |
|---|---|---|
'''+ '\n'.join('| ['+f+']('+f+') | '+role+' | '+detail+' |' for f,role,detail in rtl_rows)+f'''

组合关系：`nice_core → linear_core → x_buffer/w_panel → mac8 → 8×dot64 → mul16_pipe/quantize`；nice_core 与 linear_core 分时复用一个 icb_master。x_buffer/w_panel 经 sp_ram 例化 15 个实际存储宏。

本版要点：{'v2 内部 clear 清乘法、dot 与预取状态；y_hold 和 MAC 响应寄存器组成两个结果槽，当前行慢写回时允许下一行先算完。' if v=='v2' else 'v1 的 mul16_pipe 为一级寄存乘法；没有 v2 相邻行计算/写回预取控制，阅读时不要把 v2 的 clear 端口要求强加到本版。'}

调试规则：valid&&ready 才接收；流水 last 随乘积推进；写命令握手不是写完成；复位不清 SRAM，全装载后才读。数值 X/W/Y 为 int16，b 为 int32，acc 为 int40；F 分别 11/16/11、27、27。修改这些值须同步金模、转换、向量和接口契约。

完整时序/内存例子见 [模块导读]({link(v+'/rtl','02_项目导读/02_模块与数据流.md')})。''')
 write(v+'/tb',f'''# {v} 测试平台

测试平台用来激励和核对 RTL，不参加综合，也不是已运行真实 CPU 的证明。

| 文件 | 验证内容 | 通过意义 |
|---|---|---|
| tb_kwt_arithmetic.sv | dot64、bias、完整 acc、RNE、饱和、复位、连续任务/背压 | 260/260 算术场景与独立整数 golden |
| tb_kwt_icb.sv | ICB 同拍/延迟应答、命令保持与错误 | 4/4 协议场景 |
| tb_kwt_system.sv | NICE 请求、描述符、全部矩阵、12 层 W/b、范围/格式/复位/读写错误 | 29/29；行为内存与请求激励，不是真 E203 |
| kwt_sram_sim.sv | 本地同步 SRAM 行为模型 | 能做功能仿真，不能替代实际宏时序 |
| tb_foundry_sram.sv | 小规模真实宏接口功能检查 | 需要服务器库/专用入口 |
'''+('''| tb_kwt_overlap.sv | 行写回与下一行计算重叠、慢总线、错误后重启 | 5/5 v2 调度专项 |
| tb_kwt_mul_pipeline.sv | signed 乘法边界遍历、气泡、复位/clear | 524288 对核心边界样本，另含流水控制检查 |
''' if v=='v2' else '')+f'''
默认系统输入在 `../vec`；用 `--vectors` 指向新的模型激活目录。`KWT_TEST_SWAP` 测半字交换，`KWT_TEST_W1024` 测 W bank 大宏回退。比较失败先记录首个 layer/row/group/lane/word，禁止改 expected 值来迎合 RTL。

从根运行：`python {v}/py/run_xsim.py --tag learn_system --tops tb_kwt_system`。原始日志归档，现有脚本会重建 build。''')
 write(v+'/py',f'''# {v} PC 数值工具与回归入口

| 文件 | 输入 → 输出 | 使用边界 |
|---|---|---|
| numeric_model.py | 编码 X/W/b → int64 软件累加、RNE、int16 Y、饱和计数 | 独立整数金模；RTL 必须逐位相同；不用 TensorFlow |
| export_weights.py | 指定 best_weights → 12 套 Dense1 W/b NPZ + format.json | 检查 checkpoint SHA 和 shape；不训练、不改原权重 |
| make_vectors.py | 现有参数 + 测试数据 → ../vec/*.hex | 会写固定向量目录；平时仿真不需要运行 |
| capture_activations.py | 原模型 + smoke/真实 WAV manifest → report.json、首样本 12 层 RTL HEX | 统计全部样本但只导出首样本；split 合法性需独立确认 |
| run_xsim.py | RTL/TB/HEX → Windows Vivado XSim build 日志 | 退出码及 ALL PASS 双重检查；默认 Vivado 2023.2 |
| run_linux.py | 相同材料 → VCS 或 Xcelium 日志 | --sim vcs/xrun；完整核功能，不是 CPU 或 STA |
| run_foundry_server.py / run_binding_server.py | 服务器真实宏/公共头 + 本方核 → 特定验证 | 有固定工作目录断言，属于早期专用入口；不用来自动改正式平台 |
| package_release.py | 源码和指定历史 build → dist ZIP | 历史打包器依赖旧 build，归档后需先恢复；当前正式包见 releases |

常用命令和真实音频注意事项见 [调试导读]({link(v+'/py','02_项目导读/03_调试与E203接入.md')})。只读已有 HEX 的 RTL 回归无需 TensorFlow；模型截取使用保留的 tf24_env，不能随意移动该环境。run_linux.py 首部“Xcelium 未本地验证”是初建时注释，当前 VM 实测结果以 fix1 报告为准；本轮保持发布源码字节，不据旧注释否认新证据。''')
 write(v+'/vec',f'''# {v} 固定数据与期望值

这些是回归基准，不能为消除 FAIL 手改。v1/v2 原有 159 个数据文件相同，整理仅增加 README。

| 路径/模式 | 数据含义 | 用法 |
|---|---|---|
| quant_acc/y/sat.hex | 单独量化的输入、舍入/饱和期望 | arithmetic TB |
| dot_x/w/b/acc/y/sat.hex | 64 项点积及完整精度/输出期望 | arithmetic TB |
| layer00…11_x/w/b/y/acc.hex | 十二套完整矩阵，x/w/y 每行 32 位装两个 int16，b32，acc40 | system/overlap TB；不是 12 个编码器完整推理 |
| matrix_sat.hex | 各层预期输出饱和计数 | 检查数值路径一致 |
| vectors.json | 生成配置/尺寸等元数据 | 核对生成身份 |
| [weights](weights/README.md) | checkpoint 第一 Dense 参数与转换记录 | 金模/导出一致性 |
| [activation_smoke](activation_smoke/README.md) | 静音/合成音调的原模型捕获 | 流程检查，不能替代真实验证集 |

低半字优先时，第一个元素放总线字 [15:0]。不要把十六进制字符串直接当 float；输出真实值为 signed int16 /2048。''')
 write(v+'/vec/weights','''# 指定 checkpoint 的第一 Dense 参数

`layer00.npz` … `layer11.npz` 每个对应一个编码器的第一 Dense：w(64,256)、b(256)，同时保存浮点原值与定点编码。`format.json` 保存源 checkpoint SHA、参数名、饱和计数和幅值范围。

W 为 signed16/F16，b 为 signed32/F27。不是 Q/K/V 参数，也不是 Dense2。由 export_weights.py 精确命名导出；capture_activations.py 会与 TensorFlow 原层参数逐元素核对。layer 编号仅标识来源，硬件不会读本目录文件。''')
 write(v+'/vec/activation_smoke','''# 原模型 smoke 捕获

`report.json` 统计静音和 440 Hz 合成音调两样本的逐层误差/饱和；`layerXX_first.npz` 保存第一个样本各层的 float X/reference、整数 Y、完整 acc；`rtl/` 是这个首样本的 12 层 HEX。

已确认重放原层对象所得 logits 与原模型调用逐位相同。最大逐层汇总 NRMSE 约 0.0522%，仅针对这两个样本；不是真实语音验证集精度，不是分类准确率。所有层输出不能直接串接成完整识别。''')
 write(v+'/vec/activation_smoke/rtl','''# 首个 smoke 样本的 RTL 向量

这里保存静音样本第 0–11 层对应的 X/W/b、Y、acc 和饱和计数，格式与上两级 vec 相同。把本目录传给运行脚本 `--vectors`，系统 TB 就切换到这些真实模型中间输入。

report.json 统计两个样本，本目录只覆盖第一个；不能据一次 29/29 宣称两个样本都跑了 RTL。不要修改这些 golden。''')
 write(v+'/06_xcelium','''# 简易 Xcelium 功能入口

`run.sh` 切到上级项目目录后调用 `py/run_linux.py --sim xrun --tag xcelium`，参数继续向后传。需要 Linux 已配置 xrun；默认算术/ICB/系统三个 TB。

私有 VM 更完整、已适配的入口是其根目录 `make -C flow v1` 或 `v2`，包含 STA/SDF 和审计。此小入口只做 RTL 功能，不替代完整工具流程。''')
 write(v+'/build',f'''# {v} 构建输出与历史摘要

保留根目录的服务器观察 JSON，供追溯；其日期对应原版阶段，最新结论看 vm_eda/REPORT.md。历史完整编译/仿真日志、工具缓存、波形/中间副本已压缩到 [归档]({link(v+'/build','99_归档/20261101_整理/04_'+v+'_构建记录.zip')})，ZIP 内保留原始 `{v}/build/...` 路径和逐文件 SHA。

后续仿真会创建 build/<新 tag>/，不会依赖旧日志。若要运行历史 package_release.py，它引用特定旧文件，应先从归档恢复到单独副本；不要修改正式包迁就脚本。''')
 write(v+'/dist','''# 旧打包输出位置

正式冻结交付集中在工作区 `releases/`，日常不要从这里挑包。本目录原有早期包/上传补丁已按原路径压缩入 99_归档 的“旧交接与临时输出”ZIP（v2 原目录为空）。

保留空入口是为了兼容历史 package_release.py；以后运行该脚本可能再次生成文件。当前推荐发布包是 releases/20261101_fix1；本轮新增导航未改这些冻结 ZIP。''')

# Result leaf descriptions, keeping raw artifacts out of the main reading path.
write('vm_eda/results','''# VM 最终结果摘要

先读 v1/summary.json、v2/summary.json，再按问题下钻。当前只保留最终 JSON 和双角关键 STA 文本；完整网表、原/兼容 SDF、所有日志及修复前报告已压缩入 99_归档/20261101_整理/05_VM原始验证产物.zip，fix1 正式包也含原结果。

这次整理只改变本地阅读布局，VM 的 results 原样保留，`make -C flow check` 仍在 VM 执行。本地 Windows 目录不能直接当作完整 Tempus 运行目录。''')
for v in ['v1','v2']:
 base='vm_eda/results/'+v
 s=json.loads((R/base/'summary.json').read_text())
 write(base,f'''# {v} VM 验证摘要

`summary.json` 把功能计数、RTL SHA、结构审计、时序和 SDF 产物关联在一起，最终 completed=true。范围是行为 SRAM 完整加速器 RTL + GPDK045 dot64 布局前 STA/SDF，不是完整 CPU/语音/物理签核。

| 角 | setup slack ns | min slack ns |
|---|---:|---:|
'''+ '\n'.join('| '+c['corner']+' | '+str(c['setup_slack_ns'])+' | '+str(c['hold_slack_ns'])+' |' for c in s['timing']['corners'])+'''

functional 看 RTL；eco_dot 看缓冲等价审计；sta_eco_* 看双角约束/覆盖；gate_eco_* 看 32/32、注释完整性及网表/SDF SHA。timing_run/eco_run 只说明阶段执行，不能单独代替约束通过。

修复前失败和完整原始产物在上级说明所列归档；请勿把已归档的 baseline sta_slow/fast 当作最终 STA。''')
 for d in sorted((R/base).rglob('*')):
  if not d.is_dir():continue
  rel=d.relative_to(R).as_posix();name=d.name
  if name=='eco_dot':body='新增同相缓冲的变化清单和独立结构审计。changes.json 记录端点/单元数量；structural_audit.json 核对旁路缓冲后的原单元类型/引脚连接，不是正式顺序等价证明。mapped.v 原始网表已归档，SHA 保留。'
  elif name.startswith('sta_eco_'):body='最终 '+name.rsplit('_',1)[1]+' 角 STA。setup.rpt/hold.rpt 给路径，constraints.rpt/DRV 检查限制，coverage.rpt 记录未覆盖情况；sdf_compatibility_audit.json 验证仅将负检查限收紧为零。原始/兼容 SDF、tool.log 已归档；STA 始终使用原 Liberty。'
  elif name.startswith('gate_eco_'):body='最终 '+name.rsplit('_',1)[1]+' 角 Xcelium dot64 门级检查。results.json 需同时看 passed、32/32、annotation_complete、SDF 警告和网表/SDF SHA；只看功能打印不足。完整日志归档。'
  elif name=='functional':body='完整加速器 RTL 功能回归：default、fallback、activation。results.json 记录源码 SHA 与各场景计数；raw 子目录保留原运行器结果 JSON。行为 SRAM/请求激励不等于真实 E203 CPU。'
  elif name=='raw':body='原回归运行器的简短 results.json；各子目录对应一个运行 tag，完整 stdout/编译日志已归档。'
  elif name=='vm_default':body='默认布局的算术、ICB、系统测试；v2 还含 overlap 和乘法流水边界。结果计数含场景语义，不是语音样本总数。'
  elif name=='vm_fallback':body='半字交换 KWT_TEST_SWAP 与 W bank 深度回退 KWT_TEST_W1024 的系统测试。验证可配置分支，不声明正式平台采用该配置。'
  elif name=='vm_activation':body='指定模型首个 smoke 样本的 12 层 Dense1 激活回归；当前为静音。与两样本软件统计的覆盖范围不同。'
  else:body='本目录保存该阶段的 JSON 证据；完整原始文件见 VM 原始验证产物归档。'
  write(rel,'# '+v+' / '+name+'\n\n'+body)

write('releases','''# 冻结交付包

| 目录 | 选择依据 |
|---|---|
| [20261101_fix1](20261101_fix1/README.md) | 当前实现修复与 VM 验证包，源码/流程/结果/清单完整 |
| [20261101_v2](20261101_v2/README.md) | 原 v1/v2 冻结包，用作原始版本对照；历史违例状态不能当成最新 fix1 |

ZIP 保持原字节及 SHA。候选 r1/r2/r3 和一次性 flow 补丁已归档；最新阅读文档在工作区根和 02_项目导读，未重新打包到这些冻结 ZIP。服务器 SMIC40 包留在服务器；本地/VM GPDK 包不是同一个工艺实现。''')
write('过程与分析','''# 过程材料与依据

| 目录 | 看什么 |
|---|---|
| [01_平台资料](01_平台资料/README.md) | 本地平台使用手册，供登录/使用规则查阅；不是接口规范替代品 |
| [02_交给AI](02_交给AI/README.md) | 已确认事实、未知项、冻结的 RTL 数值/接口契约 |
| [03_我的工作区](03_我的工作区/README.md) | 设计取舍、版本演进、为什么采用该架构 |
| [05_工具](05_工具/README.md) | 活跃模型运行环境、少量关键取证和整理工具；大量历史散文件已归档 |

初学项目请先看根目录 README 和 02_项目导读，不要按这里历史文件的顺序从头猜当前状态。事实基线按阶段追加，旧“未生成/有违例”可能已被后续章节更新。''')
write('过程与分析/01_平台资料','''# 平台参考手册

保留本地 `2026NICT EDA平台_用户登录及使用手册_V10-副本-副本.pdf`，本轮从工作区根移入，文件内容/哈希未改变。用于平台使用规则和连接方式；E203 信号、共享 RAM 地址、SRAM 行为必须依据实际生效源码/库，不能由使用手册推断。

服务器 V11 使用规则曾在服务器查阅，未导出原始平台源码。本目录不会保存明文账号密码。''')
write('过程与分析/02_交给AI','''# 项目事实与冻结契约

| 文件 | 应该怎样读 |
|---|---|
| 事实基线.md | 带来源的事实和未知项；最新章节 K 是本次整理/理解更正，J 是 fix1，G–I 是实现历史。旧状态按后续更新解释 |
| RTL生成任务书.md | 数值格式、接口、边界和验证要求；改算法/位宽/ABI 前先核对，不能仅凭习惯修改 |

权威顺序仍是赛题原文 → 指定源码/权重 → 本台账。过时交接 DOCX 已归档，不用其中“任务 2 未生成”描述当前工程。术语和整体工作流见工作区 02_项目导读。''')
write('过程与分析/03_我的工作区','''# 架构决定记录

`架构设计.md` 按阶段记录保守 v1、改良 v2 和 fix1 的取舍、依据与代价。它是决策历史，不是另一个可编译实现；当前代码在 v2，精确行为以 implementation_spec/源码为准。

阅读当前实现先看该文件末尾的 v2/fix1/整理补充。早期未知项保留作证据，后续事实可能已消除；不要把未发生的候选方案描述为最终实现。''')
write('过程与分析/05_工具','''# 运行环境与取证工具

| 目录 | 保留原因 / 使用方式 |
|---|---|
| tf24_env + python_runtimes | 可用 Python3.8/TF2.4/Addons 环境及其基础解释器；有绝对路径依赖，不能随意移动；模型提取需要 |
| checkpoint_deps | 不加载 TensorFlow 时的 checkpoint 读取备用依赖；保留以复现早期导出 |
| vnc_client_deps | 访问既有 VNC 的客户端依赖；不是 RTL/模型，也不参加交付综合 |
| 各 *_20261101 取证目录 | 仅留少量关键证据/导航，完整脚本和迭代截图已归档 |
| 整理工作区_20261101 | 本轮归档脚本、删除计划、目录文档生成与检查；日常无需重跑 |

uv_cache 是包下载/解包缓存，确认 TF 环境独立可导入后清理；不包含用户写的 RTL。第三方环境内部成千上万个目录不逐个插入项目 README，以免修改依赖树；各环境根提供说明。''')
deps={'tf24_env':'已安装的 Python3.8 虚拟环境：TensorFlow2.4.0、Addons0.12.1、NumPy1.19.5。用 Scripts/python.exe 运行 capture_activations.py。pyvenv.cfg 依赖旁边 python_runtimes，不要移动或删除；无 CUDA DLL 时可走 CPU，之前已实际导入通过。',
 'python_runtimes':'tf24_env 的基础 CPython3.8 解释器。不能当重复下载缓存删除；pyvenv.cfg 指向本目录。日常使用 tf24_env/Scripts/python.exe，不直接修改运行库。',
 'checkpoint_deps':'备用 tensorflow_checkpoint_reader 及依赖，供 export_weights.py --reader-deps 指定。它是读取 checkpoint 的工具，不是训练模型；与 TF 正常读取交叉核验曾通过。',
 'vnc_client_deps':'VNC 客户端第三方依赖，供服务器只读核查/个人目录操作的历史工具使用；账户凭据不写入本目录。不会参与 RTL 仿真和综合。'}
for d,body in deps.items():write('过程与分析/05_工具/'+d,'# '+d+'\n\n'+body+'\n\n内部是第三方代码/安装数据，保留其原说明，不递归增加项目 README。')
hist={'本轮查证_20261101':'最早模型/文档提取与架构核算，当前均属历史材料。',
 '服务器取证_20261101':'公共目录原件身份、哈希及导出边界；不代表平台源码已下载。',
 '服务器验证_20261101':'v1 初次 VCS/DC/PT 检查及当时的负 slack；最终修复见 VM验证/fix1。',
 'RTL实施取证_20261101':'实际 NICE 端口、译码、sysmem 占位和宏接口的关键证据；保留部分最终截图。',
 'V2优化_20261101':'v2 流水/相邻行重叠和早期修复迭代；原始候选与过程全部归档。',
 'VM验证_20261101':'fix1 最终服务器 STA/SDF、VM 工具差异、包校验及本轮记录；保留最终证据，失败迭代同样可从归档恢复。'}
for d,body in hist.items():
 f='过程与分析/05_工具/'+d
 kept=[p.name for p in (R/f).iterdir() if p.is_file() and p.name!='README.md']
 write(f,'# '+d+'\n\n'+body+'\n\n完整原始文件在 [历次取证与调试 ZIP]('+link(f,'99_归档/20261101_整理/02_历次取证与调试.zip')+')，成员路径保留 `'+f+'/...`；逐文件映射在归档 archive_map.json。旧文档若引用缺失日志，请查这里，不是证据被丢弃。\n\n当前散文件：'+('、'.join('`'+n+'`' for n in kept) if kept else '仅导航；历史内容均在归档')+'。')

# Keep rich existing integration/tool/release documentation, add status/navigation.
for folder in ['v1/integration','v2/integration','v1/server_eda','v2/server_eda','vm_eda','vm_eda/smic40','releases/20261101_v2','releases/20261101_fix1']:
 p=R/folder/'README.md';old=p.read_text(encoding='utf8')
 note='本目录原有技术说明保留。最新完成度以工作区根 README 和 fix1 报告为准；本轮只整理本地资料，不自动同步新文档到 VM/服务器。'
 if folder.endswith('integration'):note+=' 本目录解决端口/驱动封装，尚不是完整 CPU 固件；正式共享 RAM、异常与一致性仍须联调。赛题不要求布局布线。'
 if folder.endswith('server_eda'):note+=' RESULTS.md 等是原阶段历史；fix1 最新无报告违例的实现与范围见 vm_eda/REPORT.md。'
 if folder=='vm_eda':note+=' results 中保留摘要与关键 STA，完整原始网表/SDF/日志归档到 99_归档；VM 实际运行目录不受本地整理影响。'
 p.write_text('> 2026-11-01 整理更新：'+note+'\n> [工作区首页]('+link(folder,'README.md')+') · [调试导读]('+link(folder,'02_项目导读/03_调试与E203接入.md')+')\n\n'+old+'\n\n'+LOG+'\n',encoding='utf8')
print('Folder READMEs written')
