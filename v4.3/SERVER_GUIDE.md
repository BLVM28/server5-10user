# 服务器手动功能、时序和功耗验证

## 进入目录

在 VNC 的终端先输入：
```bash
cd /storage2/2026contest/server5/s5_10usr/v4.3
make env
```
应显示 Python3、make、VCS、DC、PrimeTime、Formality、Verdi 的路径和 ENV PASS。若环境命令不存在，先使用该服务器原有 EDA 环境的终端，不要改公共环境脚本或目录。所有输出仅放在本账号 v4.3；脚本会拒绝其他工作位置。

## 最常用操作

```bash
make clean
make compile
make run
make timing
make report
```

| 命令 | 做什么 | 怎样看结论 |
|---|---|---|
| clean | 先存日常证据到 reports/before_clean_*，再清理 build/manual | CLEAN PASS；不删除 RTL、向量、实现和功耗 |
| compile | 编译四个总线条件的当前 RTL | 每顶层 COMPILE PASS；已是同一哈希则复用 |
| run | 固定 worst 输入的四种条件，完整 12 层及错误/复位 | FUNCTION PASS 29/29、guards25/25；MEASURE 给总拍数与 150 MHz tasks/s |
| timing | 对当前合格网表，SS/FF 两角 150 MHz STA | 两行 TIMING PASS，setup/hold≥0，violations=0 |
| report | 检查上两项源码、日志、网表和 SDF 身份 | REPORT PASS 并输出完整面积 |
| check | env/run/timing/report 顺序执行 | 日常完整入口，任何失败停止 |
| regress JOBS=2 | 14 组输入×两种主要总线，另零延迟与公共控制器，共 30 套 | FUNCTION ALL PASS 30 suites |
| paired | 上一版与本版使用同公共 SRAM 端点 | PAIRED V42 和当前公共端点 MEASURE |
| sweep | 同网表两角 150/160/170/180 MHz | 逐点打印 PASS/FAIL，不代表布局后保证 |
| synth | 重新综合、短路径修复、死单元等价清理、两角扫点并安装新快照 | 150 MHz full-core…PASS、IMPLEMENTATION PASS |
| gate_sample | SS/FF 各一张完整矩阵的真实宏门级 SDF | GATE/POWER PASS v43 ss/ff；不是单纯注释测试 |
| power | SS 150 MHz 门级整任务 VCD + PrimeTime PX | GATE/POWER PASS；mW/能量详读报告和覆盖 |
| vectors | 哈希校验；缺失时标准库独立重建 | STREAM VECTORS PASS 1400 |
| package | 回读核对五个独立 ZIP | 五行 PACKAGE PASS |

`make run` 的吞吐计时从 NICE 请求接收至响应有效，含该任务的描述符、X/W/b 读取和 Y 写回。每层单独冷启动，没有把下一任务的权重提前放在加速器内。总吞吐=任务数×150,000,000/总拍数。不同总线条件的测量不能混成一个值。

## 看波形

```bash
make waves
make verdi
```
waves 跑 worst 第 0 层完整矩阵并生成 `build/manual/waves/task.vcd`；必须看到 1/1 完整矩阵通过。verdi 检查波形与 RTL 哈希后打开查看器。先看 nice_req_valid/ready、nice_icb_cmd/rsp、nice_rsp_valid/rdat/err；再看 core.group_n、DMA/compute 和 Y 页面。ICB 有等待时地址/方向/数据须稳定；最后一笔写返回前不能宣告任务结束。没有波形或源码改过时，重新 make waves。

## 改 RTL 后的正确顺序

先 make compile、make run；需要全部数据组时 make regress JOBS=2。功能通过后 make synth，再 make timing 和 make gate_sample；最后 make power。旧快照的哈希与 RTL 不同，timing/report 会直接拒绝，不能靠旧时序报告证明新代码。

默认周期 PERIOD=6.666667 ns。若手动 `make timing PERIOD=6.25`，它是在 160 MHz 检查当前网表，不重新综合。报告频率按周期换算；本版发布工作点固定 150 MHz，为物理实现留余量。

## 指标与报告路径

- VCS：`build/manual/runs/<组>/<测试顶层>/run.log`、verified.json。
- STA：`build/manual/timing/rebuilt/6.666667/kwt_nice_core_ss/` 和 ff/；查看 setup.rpt、hold.rpt、violations.rpt、coverage.rpt。
- 完整面积/网表：`implementation/rebuilt/synth_kwt_nice_core/`。
- 功耗：`build/power/v43_ss_layer00/px/power.rpt`、power_hierarchy.rpt、switching.rpt、unannotated.rpt；VCD 与 SDF 在其上一级。VCD 可能数 GB，运行比 RTL 仿真慢。
- 公布结果：`results/*.json`、RESULTS.md、SERVER_RESULTS.md。

功耗是含本地 72 个 SRAM 宏的完整加速器，排除了 CPU/共享 512 KiB/互连/时钟树/提取寄生。检查报告的 Power 单位再换算 mW；任务能量=功率×活动时长。活动覆盖、宏能量表及默认活动必须看，不能只摘总功耗一行。

功能 PASS、时序 PASS 和评分整机验收是三件分别要成立的事。当前对一拍公共控制器/同步 RAM 有高吞吐证明；正式共享 RAM 地址与结构仍需平台方落实，随机长等待压力吞吐也在报告中保留。
