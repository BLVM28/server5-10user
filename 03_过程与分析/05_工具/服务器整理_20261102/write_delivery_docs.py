from pathlib import Path
R=Path.cwd();H='/storage2/2026contest/server5/s5_10usr'
guide='''# 服务器手动测试：从这里开始

在 VNC 中打开 Terminal，进入 `{home}/{v}`。根目录的 Makefile 是统一入口；不要进入旧 kwt_* 路径。Windows 本地使用同一份源码，但服务器 EDA 命令需要在 Linux 服务器执行。

## 日常只需这些命令

```sh
cd {home}/{v}
make env
make clean
make compile
make run
make timing
make report
```

也可以直接 `make check`，顺序执行环境检查、基础功能、双角时序、结果汇总。正常约 1–2 分钟（取决于许可证和服务器负载），首次编译略慢。`make compile` 只说明编译成功；`make run` 才验证功能。失败返回非零，终端给出日志路径。`make clean` 先保存日志/报告到 reports，再删除 build/manual；不会删除 RTL、向量或最终网表。

| 命令 | 做什么 | 成功判据/指标 |
|---|---|---|
| `make run` | 算术、总线、完整矩阵；v2 还含重叠和乘法流水线 | 每项完整 `ALL PASS, N/N`；打印 core_cycles 范围、每矩阵 12672 次 32 位写回 |
| `make timing` | 固定网表，dot64/完整核心 × SS/FF | 四项 `TIMING PASS`；setup/hold slack 非负、无报告约束违例 |
| `make report` | 汇总当前源码对应的已有结果 | 功能计数、矩阵周期、MHz、setup/hold；缺失或源码改变显示 INCOMPLETE/STALE |
| `make timing PERIOD=8.0` | 检查 125 MHz | 其它约束不变；随后用 `make report PERIOD=8.0` 查看 |
| `make sweep` | 同一网表扫描 150/140/125 MHz | 每周期四个角/模块组合 |
| `make waves` / `make verdi` | 生成 VCD / 打开 Verdi | 波形只辅助调试；不以界面打开代替 PASS |
| `make regress` | 基础功能 + v2 的 13 组真实语音激活 | v2 18 组；约 10 分钟，可按需要运行 |
| `make negative` | v2 新增 58 个非法描述符/地址/错误/恢复场景 | `ALL PASS, 58/58`；v1 不适用 |
| `make synth` | 从当前 RTL 重新综合并做已验证修复 | 产生 implementation/rebuilt；还要做 timing |
| `make package` | 刷新分类 ZIP 并校验每个成员 | rtl/tb/makefile/flow/vectors 各自 PASS |

`core_cycles` 是该测试激励下的硬件周期数，受总线反压影响；乘以目标周期可估算相同激励下的硬件时间，不能当作 E203 整机实测延时。

## 看波形

```sh
make waves
make verdi
```

默认保存前 200,000 ns 的顶层接口，功能检查仍完整执行。Verdi 打开后在 nWave 中 Add Signals，优先加入 nice_req_valid/ready、nice_rsp_valid/ready/err/rdat、nice_icb_cmd_valid/ready/addr/read/wdata、nice_icb_rsp_valid/ready/err/rdata。valid 与 ready 同时为 1 才完成握手；反压期间载荷必须保持，最后一笔写响应收回后才能报告完成。无需先研究所有内部波形。

## 改过 RTL 后

```sh
make run
make synth
make timing NETLIST=rebuilt
make report NETLIST=rebuilt
```

默认 NETLIST=fix1 对应已有修复网表。源码 SHA 改变时，脚本拒绝用旧网表冒充当前时序结果。综合完成不等于 timing 通过。固定实例的 ECO 若因结构变化失配会明确报错，需要按新违例调整，不能删断言继续。建议重要改动后追加 `make regress` 和 v2 的 `make negative`。

## 可选的门级测试

`make probe` 只验证 SS/FF 的 SDF 与模型能否正确注释，不运行矩阵；`make gate JOBS=4` 才做两角各 12 层完整矩阵，可能耗时较长，不放进日常 make check。本轮扩展全层门级测试没有完成，不写成通过；此前 fix1 的单矩阵门级结果保留在历史记录。

导出使用 PrimeTime 原生命令 `write_sdf -context verilog -exclude {{clock_tree_path_models}}`：条件表达式与提供的 Verilog 模型匹配，省去模型没有对应路径的内部 CLK→CLK 表示；完整 STA 不排除这些库信息。VCS 保留 `-sdfretain +neg_tchk`。没有修改黄金值、SRAM 模型、时序检查数值或设置 mask_violations。SDF 编译注释日志必须 errors=warnings=0，逐层运行同一角已核验的程序；日志副本明确标注来源。

## 目录与模块关系

| 路径 | 用途 |
|---|---|
| rtl/、rtl.f | 10 个硬件模块与编译顺序 |
| tb/ | 自检平台；不是 E203 CPU |
| vec/ | 定点输入/权重/偏置/黄金值；v2/vec/real_speech 含 13 组真实激活 |
| py/ | 数值金模、生成器及本地仿真入口 |
| integration/ | NICE 包装和 C 驱动模板 |
| server_eda/ | 当前 Makefile 调用的 Python/Tcl/门级 TB |
| implementation/ | 服务器的 fix1/rebuilt 网表、SDF、DDC、哈希；本地只有说明 |
| build/manual/、reports/ | 当前产物、日志和 clean 前证据 |
| packages/ | RTL/TB/Makefile/流程/向量分开打包 |
| history/、releases/ | 历史工程归档、原冻结包；不作为当前活动源码 |
| ../shared/ | 服务器库配置/私有库/迁移记录；公共库只读 |

数据流：E203 NICE 发描述符 → nice_core 检查任务/地址 → linear_core 调度搬运 → X/W SRAM 缓存 → mac8 的 8 路 dot64 → quantize 舍入/饱和 → ICB 写回 Y → 等写响应后通知完成。详见 rtl/README.md。

本科硬件输出 `Y[99,256] = X[99,64] × W[64,256] + b[256]`，不是 yes/no。真实语音经原模型的前处理、attention、LayerNorm 得到 X；Dense1 之后还需要 GELU、Dense2、后续层及分类头。12 层是 12 个独立的 Dense1 任务，不能把上一层 256 列 Y 直接当下一层 64 列 X。

当前功能/时序通过范围与频率见 SERVER_RESULTS.md。真实 E203、正式共享 SRAM 地址/实现、固件和顶层约束仍需整机联调，测试窗口 0x10000000/512 KiB 不代表官方地址。

## 工作日志

2026-11-02：历史 v1/v2 分别归档并逐项校验；源码不改，补充 Makefile、异常 TB、STA 扫描与操作说明。按用户要求收敛验证范围：基础回归和 STA 为日常验收，全层门级为可选。源码、TB、向量和流程目录在本地/服务器同步；工艺库、工具二进制和生成网表保留在服务器。失败探针及未完成实验保留记录，不计入 PASS。
'''
for v in ['v1','v2']:
 (R/v/'SERVER_GUIDE.md').write_text(guide.format(home=H,v=v))
 report=f'''# {v} 服务器实测结果（2026-11-02）

本轮没有修改 RTL。以下是加速器的功能与综合前端时序结果，不是 E203 整机验收；有限回归不等于对任意输入的形式证明。

| 项目 | 已完成结果 |
|---|---|
| 基础功能 | 算术 260/260，ICB 4/4，系统 29/29；{'v2 重叠 5/5，乘法边界 524288/524288（含空拍/复位共检查 527566 次）' if v=='v2' else 'v1 保守架构基线'} |
| 真实语音服务器 RTL | {'13 组 × 29 = 377/377；与本地 XSim 结果一致' if v=='v2' else '本轮仅 v2 做真实语音扩展'} |
| 新增异常测试 | {'VCS 和本地 XSim 均 58/58；含地址/描述符/错误响应及恢复' if v=='v2' else '本轮新增测试用于 v2'} |
| 固定网表 STA | 150/140/125 MHz × SS/FF × dot/core 共 12 组合通过 |
| 从 RTL 重新综合 | {'420.29 秒；去掉纯注释/空白后映射 Verilog 代码与 fix1 一致；重建网表四项 STA 通过。此比较不是形式等价证明' if v=='v2' else '本轮使用已有 fix1，未重复综合 v1'} |
| SDF 兼容性 | v2 SS/FF 短探针通过，注释 errors/warnings 均 0；不是完整矩阵门级通过 |
| 扩展全层门级 | **未完成**。按用户最新范围不再追加长回归；保留 make gate 为可选入口 |

## v2 核心频率依据

同一最终网表、SMIC40 HVT 与实际 SRAM 库；SS=0.99V/125°C，FF=1.21V/−40°C。时钟不确定度 0.100ns，I/O max/min 1.000/0.100ns，输入转换 0.100ns，输出负载 0.002852pF；没有 false path/multicycle/reset 例外。

| MHz | 周期 ns | SS setup ns | FF hold ns |
|---:|---:|---:|---:|
| 约 150 | 6.666667 | +0.000262 | +0.123025 |
| 约 140 | 7.142857 | +0.476452 | +0.123025 |
| 125 | 8.0 | +1.333595 | +0.123025 |

**保守联调建议 125 MHz。** 150 MHz 的最差 setup 仅 0.262ps，工程裕量很小。这个建议只覆盖加速器的上述约束，不保证 CPU、共享 SRAM 和整个 SoC 的频率。真实布线/顶层约束可能改变结论。

STA 覆盖：v2 核心共 22,482 项，18,765 项满足、0 项违例、3,717 项 untested；check_timing 成功。未测试项包含复位 no_clock、常量禁用/无路径等，详见服务器 coverage.rpt/untested.rpt，不声称 100% 时序覆盖。

## 能确认什么，仍缺什么

- 600 个本地自选用例的最大层汇总 NRMSE=0.03891237%（阈值 3%）；13 组导出向量做过 RTL。589/600 是原浮点模型分类结果，不能标成 RTL 识别率。
- 公共快照 e203_soc_top.v:135–170 中 sysmem 是读零占位连接。仍需要正式共享 SRAM 地址/实现、E203 启动/linker/驱动运行以及顶层时钟/I/O 约束，才能完成整机任务。没有伪造地址来宣布接通。
- 组委会最终 600 个样本与最终评测尚待；当前结果是已知模型、现有库、明确测试激励范围内的证据。

## 整理与证据

服务器旧 v1 2091、v2 3357 个归档条目逐项 SHA 校验后收进各版 history/history_20261102.zip；清除了对应散文件，原正式 ZIP 字节不变。路径迁移表见 shared/migration_20261102.json。本地已有历史资料继续由 99_归档 索引；不把服务器工艺库/网表发布到 GitHub。

服务器 reports/ 保存本轮命令记录，build/manual/ 保存细分日志；make report 会核对当前源码并打印功能计数、周期和时序余量。短探针失败、静态 SDF 位置探索和未完成长门级任务均不计入通过结果。SDF 最终兼容设置及日常操作见 SERVER_GUIDE.md。
'''
 (R/v/'SERVER_RESULTS.md').write_text(report)
p=R/'README.md';s=p.read_text();s=s.replace('[协作与克隆说明](GitHub协作说明.md)','[公开仓库](https://github.com/BLVM28/server5-10user)');s=s.replace('[最新验证报告](vm_eda/REPORT.md)','[服务器最新验证报告](v2/SERVER_RESULTS.md)')
s+='''
## 服务器日常操作（2026-11-02）

本地与服务器的 v1/v2 源码、TB、Makefile 和流程目录一致；生成产物和工艺库不在公开仓库复制。先读 [v2 手动操作](v2/SERVER_GUIDE.md) 和 [本轮结果](v2/SERVER_RESULTS.md)。

```sh
cd /storage2/2026contest/server5/s5_10usr/v2
make check
make waves
make verdi
```

`make check` = 环境 + 基础功能 + SS/FF STA + 指标汇总。`make clean/compile/run/timing/report/package` 可分别执行。保守联调建议 125MHz；150MHz 静态检查通过但 setup 余量极小。长门级测试属于可选项，正式 E203 整机接入仍需共享 SRAM 与固件材料。
''';p.write_text(s)
p=R/'03_过程与分析/02_交给AI/事实基线.md';s=p.read_text();s+='''

## 2026-11-02 服务器整理与手动 EDA（本轮补充）

[已确认] 个人区归并为 v1/v2；历史归档分别 2091/3357 条逐项 SHA 校验后移除旧散文件。公共库只读；源码/测试/流程本地与服务器统一，库和映射产物只在服务器保存。

[已确认] v2 VCS 18 组基础/真实激活回归通过，其中真实 13×29=377/377；新增异常场景 VCS/XSim 各58/58。新综合 420.29 秒，去纯注释/空白后网表代码与 fix1 相同；四项 STA 通过。v1 基础三组及12项STA扫描通过。详见 v2/SERVER_RESULTS.md 与服务器 reports。

[已确认] v2 SS0.99V125°C/FF1.21V−40°C、uncertainty0.1ns、I/O1.0/0.1ns、load0.002852pF：150MHz SSsetup+0.000262ns，125MHz+1.333595ns；FFhold+0.123025ns。无时序例外。覆盖22482项、18765满足、0违例、3717untested，不是全覆盖。

[已确认] PT默认SDF条件与SRAM Verilog不匹配；原生 -context verilog 后剩60个CLK→CLK路径警告，按本机man write_sdf使用 -exclude {clock_tree_path_models} 后SS/FF短探针0 errors/0 warnings。此选项只改仿真导出表示，不改STA；短探针不等于全矩阵门级。

[待确认] 本轮未完成扩展全层门级，不计PASS；按用户收敛范围保留可选make gate。公开快照 e203_soc_top.v:135–170 sysmem为读零占位，正式共享SRAM、地址、固件/启动/linker/顶层约束及官方600例仍需整机验收；若后续给出不同地址/约束，应更新参数/驱动并重新验证，不沿用测试窗口。
''';p.write_text(s)
p=R/'03_过程与分析/03_我的工作区/架构设计.md';s=p.read_text();s+='''

### 2026-11-02 手动测试交付与范围取舍

[决定] 不改RTL和数值契约；统一版本根Makefile。日常make check仅做环境、基础功能、双角STA和指标汇总；真实激活regress、58例negative、全层gate按需运行。保留完整失败日志，不让可选门级长回归阻挡本轮交付。依据是用户要求从参赛者角度控制验证范围。

[实测] v2真实激活服务器377/377、新异常双仿真器58/58、固定网表12项时钟/角扫描通过。保守联调选择125MHz，SSsetup+1.333595ns；150MHz仅+0.000262ns，因此作为目标检查而非裕量充足的保证。正式SoC仍需实际存储/固件验证。
''';p.write_text(s)
print('DOCS_READY')
