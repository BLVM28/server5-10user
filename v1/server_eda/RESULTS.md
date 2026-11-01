# 服务器实测：功能通过，初步时序未达标

日期：2026-11-01。此报告针对交付包中的 10 个自有 RTL 模块；本次没有修改设计 RTL、checkpoint 或金模预期。新增了服务器 Makefile、SRAM/点积 TB、综合和 STA 脚本。结果为实际服务器执行后通过 VNC 核对的摘要，不是下载的原始 EDA 日志。

## 工程、工具与来源

服务器工程：`/storage2/2026contest/server5/s5_10usr/kwt_eda_tmp_20261101/project`。

原始交付包 `kwt_rtl_v1.zip` 已上传个人工作目录并解包，236 个文件按 manifest 校验；压缩包 SHA-256：`327edf5c22e8a92b388195178e315a379d8a9998d6c7df4d643ec038d1d7fff9`。新增 harness 随修订上传，原始交付包保留。服务器 `upload_verified.json` 保留原包核验记录。

| 实际工具 | 版本 / 路径 |
|---|---|
| VCS | Q-2020.03-SP2-6，`/eda/synopsys/vcs/vcs_2020.03-SP2-6/bin/vcs` |
| Design Compiler | T-2022.03-SP5-5，`/eda/synopsys/dc/dc_2022.03-SP5-5/bin/dc_shell` |
| PrimeTime | T-2022.03-SP5-1，`/eda/synopsys/prime/prime_2022.03-SP5-1/bin/pt_shell` |
| Library Compiler | 2022.03-SP5，`/eda/synopsys/lib_compiler/lib_compiler_2022.03-SP5/bin/lc_shell` |
| 构建环境 | `/bin/make`、Python 3.6.8 |

标准单元取自公共 `SMIC40_2025/S40.tar.gz` 的 SCC40NLL VHSC40 HVT 库；使用 SS 0.99 V/125°C 和 FF 1.21 V/−40°C 的 basic DB。SRAM 取自公共 `SRAM_Lib_2025/RAMSP128X16`、`RAMSP1024X16` 的对应角 Liberty，用 LC 编译到个人临时目录，公共目录未改写。完整来源与哈希留在服务器 `timing_library_scan.json`、`library_selection.json`。这些公共 2025 库不自动等于已经确认的 2026 正式验收库。

## 功能与动态检查

| 检查 | 实测结果 | 范围 |
|---|---|---|
| VCS 算术 | **260/260** | 量化、32 个 dot64 向量和复位 |
| VCS ICB | **4/4** | 握手、背压、应答与错误 |
| VCS NICE/矩阵 | **29/29** | 真实 checkpoint 的 12 层参数、合成 X、错误/复位；真实 SRAM 的 ARM_UD_MODEL 功能分支 |
| 原模型对应层输入 | **29/29** | 静音输入截取的 12 层 X 与真实参数；不是语音验证集精度验收 |
| 新 SRAM 时序 TB | **1186/1186** | 默认厂商时序模型；SP1024/SP128 全地址、逐位写掩码、禁用保持；约 150 MHz |
| 新 dot64 RTL TB | **32/32** | 输入气泡、输出背压；约 150 MHz |
| dot64 标准单元 + SS SDF | **32/32** | 实际 DC 网表、真实标准单元模型；SDF 完成、0 errors/0 warnings；未关闭 timing checks/notifier |

最终点积 TB 在时钟上升沿后 1 ns 驱动输入，与 SDC 的最大输入延迟一致。初版下降沿驱动只留半周期，门级 case 2 触发 setup violation 并产生 X；该失败日志保留。修正的是测试平台时序预算，未修改 RTL、时钟频率、金模结果或门级时序检查。输出比较在背压期间等待稳定，握手仍按原接口执行。

仿真 `timescale 1ns/1ps` 将半周期 3.333334 ns 量化成 3.333 ns，实际周期 6.666 ns，约 150.015 MHz。SRAM 默认模型的检查不能替代 Liberty 角的完整 STA。dot64 门级动态通过也不证明完整加速器的 hold 问题已解决。

## 综合与静态时序

DC 分别综合 `kwt_dot64`、`kwt_nice_core`；完整加速器链接实际 SRAM timing DB，PT 统计得到 **8 个 RAMSP128X16 + 7 个 RAMSP1024X16**。完整加速器综合采用测试内存窗口 `MEM_BASE=0x10000000, MEM_BYTES=524288`，用于保留真实逻辑；该地址不是已确认的平台共享 RAM。

约束：周期 **6.666667 ns**；uncertainty **0.100 ns**；输入/输出 max delay **1.000 ns**，min delay **0.100 ns**；输入 transition **0.100 ns**；输出负载 **0.002852 pF**，SS/FF 同值。PT 报告时间单位为 1 ns、电容单位为 1 pF。未添加 false path、multicycle path 或复位时序豁免。

| 设计 | 库角 | 最大路径最差 slack / ns | 最小路径最差 slack / ns | 判断 |
|---|---|---:|---:|---|
| dot64 | SS | +0.002894 | −0.071293 | 最小路径违例：复位 removal |
| dot64 | FF | +3.930200 | +0.013860 | 本次 max/min slack 非负 |
| 完整 NICE 加速器 | SS | +0.000123 | −0.046896 | 数据 hold 违例，setup 几乎无余量 |
| 完整 NICE 加速器 | FF | +3.828464 | −0.145295 | 数据 hold 违例 |

关键路径：

- dot64 SS max：`pair_x[7] -> mul/out_product_reg_31_/D`；SS min：`rst_n -> out_acc_reg_24_/RDN`，属于异步复位撤销的 removal 检查。
- 完整核心 SS max：`core/xbuffer/bank_1__ram/sp1024_ram/CLK -> core/mac/lane_7__dot/mul/out_product_reg_31_/D`，即 SRAM 读出到乘法结果寄存器。
- 完整核心 SS min：`core/load_word_reg_16_/CK -> core/wbuffer/lane_7__ram/sp128_ram/D[0]`。
- 完整核心 FF min：`core/load_word_reg_0_/CK -> core/wbuffer/lane_6__ram/sp128_ram/D[0]`。

四组 `check_timing` 均执行成功。完整核心 SS 的 analysis coverage：17659 项检查中 14503 满足、128 违例、3028 未测试；FF 为 14351 满足、280 违例、3028 未测试。已观察到固定响应高位的 `no_paths`，以及固定 EMA/EMAW/RET1N 条件使部分宏弧禁用；不能把 `check_timing succeeded` 当作 100% 覆盖或签核。`coverage.rpt`、`untested.rpt`、`disabled_arcs.rpt` 保留具体原因。脚本没有人为添加时序豁免。DC 另有 unused/unconnected 输出等 lint 警告，保留在 check_design 报告中；SDF 零警告不代表综合日志零警告。

两角的未测试原因均为 `no_clock=2195`、`constant_disabled=781`、`no_paths=52`。抽查 `no_clock` 项为异步复位 RDN 低脉宽检查：本次没有给复位建立周期波形，正式最短复位脉宽仍须按平台契约补验；不能误把它当作工作时钟没有创建。`constant_disabled` 样例包括未使用的 W SRAM A[6] 和 RET1N 条件相关弧。

因此：**完成了实际 ASIC 库综合和布局前时序检查，但完整加速器未通过本次 150 MHz 时序判据。** 最大路径正余量仅 0.000123 ns，不能作为可靠余量；hold 负余量也不会因简单降低频率自动消失。这里没有布线 SPEF、CTS、OCV、正式平台 I/O 预算或全模式全角签核，不报最终频率、版图面积或功耗达标。

## 重跑和原始证据

```bash
cd /storage2/2026contest/server5/s5_10usr/kwt_eda_tmp_20261101/project/server_eda
make all
```

`make all` 验证各工具/仿真是否执行成功；STA 报告的 `completed=true` 表示分析完成。`sta_result.json` 中 `timing_slack_met=false` 和 summary 输出明确记录时序未满足，不能只看 make 退出码。

最终已实际执行一遍完整 `make all`：全部目标完成，summary 明确输出 `TIMING_SLACK_MET False`，功能计数与上表一致（本地证据截图 `33_final_all_results.png`）。门级 SDF 含 7503 条 IOPATH、3290 条 INTERCONNECT、140 个 TIMINGCHECK 块；回标日志零错误/警告。条目数是 SDF 内容统计，不是正式的每条弧覆盖率证明。

以服务器 project 为相对根：

- `build/server_functional/`、`build/server_activation/`：完整功能日志、向量/源码哈希与 results.json。
- `build/server_eda/sram150/`、`dot150/`、`gate/`：编译/运行日志；gate 另有实际 mapped.sdf 与 sdf_annotation.log。
- `build/server_eda/synth_kwt_dot64/`、`synth_kwt_nice_core/`：DC 日志、综合网表、DDC、SDF、面积/约束报告。
- `build/server_eda/sta_<设计>_<ss或ff>/`：PT 日志、units、setup、hold、coverage、untested、disabled_arcs、metrics 与宏数量。
- `build/server_eda/*_result.json`、`summary.json`：执行与时序状态分别记录。工具重跑前将旧主日志复制至对应 `prior_logs/`；工作根另保留各次 make 日志。

本地证据截图与操作脚本位于 `过程与分析/05_工具/服务器验证_20261101/`。原始公共库、服务器综合网表与大日志留在服务器，没有通过下载规避平台限制。上传只使用平台 FTP，临时上传区位于个人 home 的 Desktop 下。

## 仍需解决

1. **时序**：根据真实 SoC 约束检查复位同步撤销；对寄存器到 SRAM 的短数据路径做实际实现阶段 hold 修复；对 SRAM 读出→乘法长路径评估输入寄存/流水或实现优化。应在单独修订中改变 RTL/实现后重新跑功能与时序，不能为通过而删检查或降低金模要求。
2. **平台**：真实共享 RAM 地址与互联、正式平台库/顶层、CPU 程序和复位/一致性契约尚未实机验收。若正式接口预算或宏不同，替换参数与绑定后重跑；当前测试地址不可直接用于交板。
3. **模型**：本次仍是 FFN 第一 Dense 的 12 层独立任务，非全部语音网络的硬件实现。真实语音验证集精度与 CPU 驱动完整模型的运行仍未完成。
