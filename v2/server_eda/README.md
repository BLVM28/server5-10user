# 服务器 EDA 流程入口（2026-11-02）

现在从版本根目录执行 `make`，或在本目录执行转发 Makefile。操作手册：[SERVER_GUIDE.md](../SERVER_GUIDE.md)；本轮结论：[SERVER_RESULTS.md](../SERVER_RESULTS.md)。

- `easy.py`：编译/功能回归、哈希绑定、综合、双角 STA、逐层并行 SDF、波形与结果汇总。
- `manual_synth.tcl`：读当前 RTL 和真实 SRAM 库进行综合。`reset_repair*` 与 `cap_eco5.tcl` 仅用于映射后的最小延迟/驱动修复。
- `manual_sta.tcl` + `constraints.tcl`：独立重建原始约束，输出 setup/hold、约束违例、覆盖与 SDF。不能把优化时的 margin 当作最终约束。
- `tb_core_all_gate.sv`：12 层完整矩阵的外部接口检查；每个进程可用 `+LAYER=N` 独立运行一层，汇总必须覆盖 0–11。
- `wave_dump.sv`：可选、限窗口的顶层接口 VCD，正常回归不产生大波形。

旧脚本仅保留参考；下面是 **2026-11-01 历史记录**，其路径和命令不能代替当前入口。既有正式 ZIP 不改。

---

> 2026-11-01 整理更新：本目录原有技术说明保留。最新完成度以工作区根 README 和 fix1 报告为准；本轮只整理本地资料，不自动同步新文档到 VM/服务器。 RESULTS.md 等是原阶段历史；fix1 最新无报告违例的实现与范围见 vm_eda/REPORT.md。
> [工作区首页](../../README.md) · [调试导读](../../02_项目导读/03_调试与E203接入.md)

# v2 服务器 EDA 流程

工程位于 `/storage2/2026contest/server5/s5_10usr/kwt_versions_20261101/v2`。实际结果见 [对比报告](../REPORT_V1_V2.md)。

```bash
cd /storage2/2026contest/server5/s5_10usr/kwt_versions_20261101/v2/server_eda
make all
```

默认 `PERIOD=6.666667 RAW_TAG=v2_150 TAG=v2_reset HOLD_FIX=1`。顺序执行功能、原模型输入、overlap、乘法专项、E203 包装、SRAM/dot 时序模型、综合、复位 min-delay 修复、独立 STA、dot 门级、完整核心一层门级、v1/v2 同 TB 计数与汇总。不要用 `-j`。fullgate 和 sram150 固定约 150 MHz，不是任意频率扫描器。

| 目标 | 内容 |
|---|---|
| functional / activation | VCS + SRAM ARM_UD_MODEL；算术/ICB/矩阵，原模型静音输入 |
| overlap / pipeline | 长总线背压与错误恢复；三级乘法边界穷举、气泡、clear |
| binding | 原始 E203 头文件与自有 NICE 包装，29 场景；不是 CPU 执行 |
| benchmark | 同一生成 TB 对原始 v1 和当前 v2 计数；固定 wait_count=2 |
| sram150 / dot150 | 默认 SRAM 时序模型 1186 比较；dot RTL 32 向量 |
| synth | 读取 RTL_ROOT，结果写入 build/RAW_TAG；SS/FF 配对库、hold 修复 |
| repair | 读取原始 DDC，以真实缓冲修复 reset 短路径，另写 build/TAG |
| sta | 从 mapped.v 和库独立建立原约束，不读取优化用 SDC |
| gate / fullgate | dot64 / 完整核心一层的 SS maximum SDF 和真实模型 |
| summary | 分别汇总工具完成、max/min slack 与约束违例 |

同流程重综合 v1（只读原 RTL，结果写在 v2/build）：

```bash
make synth repair sta gate RAW_TAG=v1_sameflow_150 TAG=v1_reset RTL_ROOT=/storage2/2026contest/server5/s5_10usr/kwt_eda_tmp_20261101/project
```

单独目标先完成依赖：synth → repair → sta/gate/fullgate。BASELINE 默认指向上述原始 v1。日志、网表、SDF 留服务器，没有下载。没有递归清理目标。

工具：VCS Q-2020.03-SP2-6、DC T-2022.03-SP5-5、PT T-2022.03-SP5-1、LC 2022.03-SP5、Python 3.6.8。脚本通过 which lc_shell 设置进程内 SYNOPSYS_LC_ROOT，不改系统配置；TMPDIR/TEMP/TMP 均在个人工作目录。

`../../library_selection.json` 指向个人目录已编译库，来源为只读公共 SMIC40_2025 和 SRAM_Lib_2025。发布包不含公共库；搬动个人库后须更新配置。

最终约束：6.666667 ns、uncertainty 0.100 ns，I/O max 1.000 ns/min 0.100 ns，input transition 0.100 ns，output load 0.002852 pF。保留 recovery/removal；无 false path 或 multicycle。综合临时 hold uncertainty 0.300 ns 和 reset min-delay 0.400 ns 是更严格优化目标，修复后恢复/移除；最终 PT 从零建原约束。

门级在上升沿后 1 ns 改变输入；1 ps 精度使实际周期为 6.666 ns。启用 +neg_tchk，不关闭 timing checks/notifier。必须同时满足退出码、完整 PASS、无 fatal/Timing violation、SDF 0 errors/0 warnings。

这只是布局前检查，没有 CTS/SPEF/OCV/全模式全角或功耗验收。综合测试窗口 0x10000000/524288 不代表真实共享 RAM 已接通。


工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。
