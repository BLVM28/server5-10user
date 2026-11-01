# v1 → v2：RTL、性能与时序对比报告

日期：2026-11-01。最终 RTL 的数值与接口回归通过；固定延迟 ICB 下，12 次 NICE 任务周期减少 **20.2065%**，同频吞吐提高 **25.3235%**。修复后 SS/FF 最差 max/min slack 均为正，但 setup 余量很小，仍有电容与未测检查项，**不是物理后端签核通过**。

## 1. 冻结、范围与证据

- 本地：`releases/20261101_v2/v1.zip`、`v2.zip`；展开源码分别为 `v1/`、`v2/`。
- 服务器：`/storage2/2026contest/server5/s5_10usr/kwt_versions_20261101/v1.zip`、`v2.zip`；新工程在该目录 `v2/`。旧工程 `kwt_eda_tmp_20261101/project` 仅作只读对照。
- 本地 v1 冻结时 488 文件，经哈希审计保持不变。v2 仅修改 4 个设计模块；159 个向量文件与 v1 逐字节相同。两地压缩包含不同的本地/服务器证据，ZIP 哈希不同，RTL 与向量按文件校验。
- 原始 EDA 日志、网表和 SDF 留服务器；本地 `build/server_observed_v2.json` 是 VNC 观察整理，截图在 `过程与分析/05_工具/V2优化_20261101`。没有下载公共源码或服务器受限制文件。
- 覆盖赛题任务 1/2 的第一 Dense：`Y[99,256]=X[99,64]×W[64,256]+b[256]`，12 层分别提交。没有实现 Attention、GELU、第二 Dense 或完整语音分类链路。依据赛题印刷 p6–8、参考仓库 `transformer_utils.py:87–118`。
- 赛题统一时钟 **150 MHz**（`赛题介绍_原文.txt:38`）。早期 200 MHz 仅作流水试验，保留失败记录，不计作比赛加速。

## 2. 改动与依据

| 项目 | v1 | v2 |
|---|---|---|
| 乘法 | 单级完整 16×16 | 操作数寄存→并行部分积→32 bit 精确合并，3 级、II=1 |
| SRAM→乘法路径 | 读出、bank mux 与大乘法共周期 | 入口寄存切开 SRAM/mux 与乘法 |
| 行调度 | 计算完，写回 4 字，才算下一行 | 当前行 y_hold 写回期间计算下一行；MAC 输出保持待交接结果 |
| 错误恢复 | 单计算流 | 同步 clear 清空预计算有效位；写错误后下一任务无需全局复位 |
| ICB / SRAM | 单笔在途 / 8 lane / 15 宏 | 相同，不增加多在途、一致性或跨组乱序 |
| 实现优化 | 原始映射流程 | SS/FF 配对库、数据 hold 与复位短路径真实单元修复 |

精确恒等式为 `w = unsigned(w[7:0]) + signed(w[15:8])*256`。低部分积用 signed25 容器，高部分积 signed24，符号扩展后合并为 signed32；不截断、不近似。valid/last 随三级传递。X16/F11、W16/F16、bias32/F27、acc40/F27、Y16/F11、最终一次 RNE 和饱和均保持。

`kwt_linear_core` 的 prefetch_state/prefetch_row 只访问驻留 X/W。writer 独占 ICB，当前行 4 个写应答全成功才推进 row_m；整组 99 行完成才更换 W/b。两个结果槽是既有 y_hold 与 MAC 响应寄存器。慢写回时保持结果，错误时撤销预计算。不改变 E203 包装端口、指令 ABI、地址/层号/溢出检查。

修改文件是 `kwt_mul16_pipe.sv`、`kwt_dot64.sv`、`kwt_mac8.sv`、`kwt_linear_core.sv`。模块关系见 [实现规格](implementation_spec.md)和[架构依据](ARCHITECTURE_V2.md)。

一手来源支持工程方法，不能代替本项目实测：

- [Gemmini 官方 README](https://github.com/ucb-bar/gemmini/blob/master/README.md)：流水寄存、PE 延迟、输入对齐及访问/执行解耦。这里采用轻量相邻行重叠，没有移植完整 systolic array。
- [Ibex 官方乘法文档](https://ibex-core.readthedocs.io/en/latest/03_reference/instruction_decode_execute.html#multiplier-divider-block-mult-div)及[源码](https://github.com/lowRISC/ibex/blob/master/rtl/ibex_multdiv_fast.sv)：较小乘法单元组合完整乘法；ASIC 结果依赖综合。本版为自主编写的三级全吞吐实现。
- [OpenROAD 官方 timing repair](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html#repair-timing)：真实缓冲修复 hold、避免破坏 setup、CTS 后复核。本次使用 Synopsys 布局前实现。

## 3. 同频性能实测

服务器 benchmark.py 生成同一 TB 分别编译冻结 v1 和最终 v2。TB SHA-256：`f0240db31240f64b32666e734ac4f09c10a216304a7908b08075df9cf98d1ccf`。两版本均 29/29；下表取前 12 次合法层任务。请求无随机反压、BFM wait_count=2，事务量与向量完全相同。

| 指标 | v1 | v2 | 变化 |
|---|---:|---:|---:|
| 每层 core_cycles | 403,137 | 321,665 | −81,472 |
| 12 层 core_cycles | 4,837,644 | 3,859,980 | −20.2095% |
| 每层 NICE 任务周期 | 403,197 | 321,725 | −81,472 |
| 12 层 NICE 任务周期 | 4,838,364 | 3,860,700 | **−20.2065%** |
| 按 150 MHz 换算 NICE 时间 | 32.25576 ms | 25.73800 ms | −6.51776 ms |
| 同频任务吞吐比 | 1.0000 | **1.253235** | **+25.3235%** |
| 每层事务 / 写应答 | 24,296 / 12,672 | 相同 | 不靠漏算漏写提速 |

NICE 周期从请求接受采样沿到首次采样响应有效，包含描述符处理，不含 TB 故意施加的最终响应反压。仍不含 CPU 发射、软件准备、其它模型算子或 SoC 仲裁。计数 TB 时钟 10 ns；表中 150 MHz 时间为同频换算，不是板级测量或官方端到端成绩。随机背压 layer0 也从 442,642 降至 340,094 拍，但不与固定延迟指标混算。

## 4. 功能与网表验证

| 最终 v2 检查 | 结果 | 范围 |
|---|---|---|
| XSim / VCS 算术、ICB、矩阵 | 260/260、4/4、29/29 | 12 层真实参数，输出/acc/事务/guard/饱和计数 |
| 乘法专项 | 524288/524288 边界组合 | 8 个 X × 所有 W；加随机、气泡、reset、clear，总比较 527566 |
| overlap 专项 | 5/5 | 长背压、保持、写错后不复位重启、待写复位；重叠 301447 拍、MAC 保持 34213 拍 |
| PACK=0、WAW=10 | 29/29 | 本地最终 RTL，交换半字与大 W 宏回退 |
| 原模型静音各层 X | 29/29 | VCS SRAM 功能分支；不是语音验证集 |
| 实际 E203 头文件与包装 | 29/29 | 真实 config.v/e203_defines.v、同名宏；不是 CPU 整机 |
| SRAM 默认时序模型 / dot RTL | 1186/1186、32/32 | 约 150 MHz |
| 最终 dot 网表 + SS SDF | 32/32 | 0 回标 errors/warnings；未关闭时序检查 |
| 完整核心一层 SDF | **1/1** | 全部 12672 输出字、24296 事务和 guard 正确；SS maximum SDF，真实标准单元和默认 SRAM 时序模型，回标 0 errors/0 warnings |

每次完整 RTL 矩阵比较 25,344 个 40 bit 累加和、25,344 个 int16 输出。负例覆盖指令/描述符/层号/对齐/重叠/溢出、描述符/W/Y 访存错误和运行中复位。金模与期望值未为迁就实现而修改。门级驱动遵循上升沿后 1 ns 输入预算；1 ps 精度将周期量化为 6.666 ns。

## 5. 库、约束与时序

工具为 VCS Q-2020.03-SP2-6、DC T-2022.03-SP5-5、PT T-2022.03-SP5-1。标准单元是 SMIC40 SCC40NLL VHSC40 HVT，SS 0.99 V/125°C 与 FF 1.21 V/−40°C；SRAM 是 SP128/SP1024 对应角 Liberty/DB。2025 公共库尚不能自动视为 2026 正式验收库。

最终 PT 独立重建约束：6.666667 ns、uncertainty 0.100 ns，I/O max 1.000 ns/min 0.100 ns，input transition 0.100 ns，output load 0.002852 pF（两角相同）。没有 false path、multicycle 或 reset 豁免。综合临时 hold uncertainty 0.300 ns、reset min-delay 0.400 ns 为更严格优化目标，修复后恢复/移除；最终 PT 不读取这些优化约束。

| 实现 | SS max / min slack (ns) | FF max / min slack (ns) |
|---|---:|---:|
| 原始 v1 dot | +0.002894 / −0.071293 | +3.930200 / +0.013860 |
| 原始 v1 完整核心 | +0.000123 / −0.046896 | +3.828464 / −0.145295 |
| 最终 v2 dot | +0.006241 / +0.336904 | +4.393198 / +0.200376 |
| 最终 v2 完整核心 | **+0.000262 / +0.399041** | **+3.500699 / +0.192947** |
| 同流程 v1 dot | +0.003661 / +0.449117 | +3.930788 / +0.191499 |
| 同流程 v1 完整核心 | +0.000217 / +0.384746 | +3.731268 / +0.199938 |

v2 SS 最长路径转至 lane3 的 40 bit accumulator 反馈链（acc_reg_2_ → acc_reg_39_）。三级乘法没有消除累加反馈瓶颈。0.000262 ns 仅约 **0.262 ps**，不能承诺布线后仍满足 150 MHz。降频无法解决 hold；本次以真实单元延迟修复短路径。

完整核心 setup/hold 各 3670 检查：3512 满足、158 未测；recovery/removal 各 2884 全测满足。总计 22482 检查，18765 满足、3717 未测（含 constant_disabled、no_paths、复位脉宽 no_clock）。复位脉宽未测不能当作验证通过。SS 仍有 2 处最大电容违例：master/U381/ZN 实际 0.073936 pF、上限 0.072321 pF，U1770/Z 实际 0.074555 pF、上限 0.074552 pF。因此只可说“本次 max/min slack 非负”，不能说“所有约束通过”。

check_design 仍报告未负载输入 8、未连接端口 1492、常量连接 1318、同单元多脚网 120、无负载网 419。已观察示例包括未外露 cycle/acc 调试输出和固定 size；没有做 formal equivalence 或逐条 waiver，不宣称 lint-clean。

## 6. 面积和收益归因

| DC 库面积单位 | 原始 v1 | 最终 v2 | 变化 |
|---|---:|---:|---|
| dot64 total cell area | 3116.030403 | 4948.557612 | 增加流水与修复单元 |
| 完整核心 total cell area | 127551.855752 | 147845.634293 | **+15.9102%** |
| SRAM macro area | 85456.079102 | 85456.079102 | 相同 |
| 扣宏后的面积 | 42095.776650 | 62389.555191 | 含流水与 hold/reset 缓冲 |

同流程 v1 的 dot 面积为 **3665.054420**，完整核心 **137444.502288**；v2 相对同流程 v1 总单元面积增加 **7.5675%**。同流程 v1 的 max/min slack 也均为正，dot SDF 32/32、0 回标错误/警告。因此 hold 修复主要是实现流程收益，不能归功于三级乘法；v2 的独有实测收益是相邻行重叠减少任务周期，setup 余量并无数量级改善。

同流程 v1 的 report_constraint 没有报告违例；v2 的两处 cap 违例是仍需修复的退步，未隐去。两者均存在模型/常量/复位脉宽的覆盖限制，不因此升格为后端签核。

DC 单元面积不是最终芯片面积；时钟树、布线、拥塞、功耗未测。SRAM 仍为 8×SP128 + 7×SP1024，16 KiB。

## 7. 不足与待确认

1. **后端未签核**：需正式库、SoC I/O 预算、CTS、SPEF、OCV、全角复验，处理 cap 与未测检查。若 setup 不足，应先评估 accumulator 反馈链优化，再做逐位等价和矩阵回归；不能仅给乘法继续加级数。
2. **共享 RAM 未确认**：0x10000000/524288 仅测试窗口，默认 MEM_BASE/MEM_BYTES=0 拒绝任务。平台窗口/字序不同则调整参数、软件布局与互联，跑实际 E203 程序、错误陷阱和整域复位。
3. **单笔 ICB 限速**：慢外存仍限制收益，列组装载没有与计算重叠。未来多在途/双面板必须先确认 LSU 容量和响应顺序。
4. **不是完整语音验收**：静音/合成音调仅 smoke；未获得官方 600 条清单，未跑正式语音验证集逐层 NRMSE、完整模型 CPU+加速器端到端计时。
5. **复位/无应答**：仍要求 NICE 与应答域一起复位；无硬件超时。若平台允许独立复位 NICE，应增加隔离/排空。

## 8. 复现与历史记录

命令见 [README](README.md)和[服务器说明](server_eda/README.md)。`v2_150` 为修复前映射，`v2_reset` 为最终；`v1_sameflow_150/v1_reset` 为原 RTL 对照。benchmark_comparison.json 保留逐层计数、TB/RTL 哈希。

保留早期 200 MHz pipeline-only 试验、SDF 多端口网警告、benchmark 插入位置编译失败、日志负载解析失败。后两项只修正测试/报告脚本；SDF 警告通过 set_fix_multiple_port_nets 处理，未关闭检查。早期失败不是最终通过证据，日志未删除。
