# 服务器复验流程

`check_server.py` 和 `measure.tcl` 为 r8 的 P6 复现版。输入使用已有 P6 工程、宏库、固件、编译命令和冻结向量。任务 3 负责人在获准的服务器个人工作目录中把 `rtl/`、`rtl.f`、`flow/` 放入同一候选目录，再执行 `python3 -B flow/check_server.py`。输出位于候选的 `work/`。

脚本按 `rtl.f` 替换 P6 的 15 个 DUT 文件，并核对平台源码、固件、向量及活动综合脚本 SHA256。相对个人主目录的输入路径集中在 `check_server.py`。使用其他平台时由整机负责人提供其真实源码、库、约束、地址和独立结果。

同一次 6.25 ns 映射下报告 160 与 150 MHz 主条件。STA 原约束为 P6 的 SMIC40 HVT、真实 SRAM、TLUPlus 1P9M_2TM、0.300/0.100 ns 建立与保持不确定度，以及 P6 输入输出预算和路径例外。映射阶段增加的优化余量在报告前恢复。160 MHz 加速器主条件通过后检查 7 个 PVT × 5 个 RC。

| 输出 | 判据 |
|---|---|
| `simulation.log` | `SOC_EXECUTION_ALL_PASS tasks=12 checked_words=58547 boots=2`，另读 `SOC_PERFORMANCE_TOTAL` |
| `reports/kwt_paths.tsv` | KWT 内部、接口路径和整机最差建立/保持 |
| `reports/electrical.tsv` 与 `violations.rpt` | 最大转换时间、电容和扇出记录数及原始对象 |
| `reports/check_timing*.rpt` | 各范围未约束端点与覆盖 |
| `reports/acceptance.txt` | `KWT_160_PASS` 与 `SOC_160_PASS` 分别判定，查看 35 个实际组合 |

脚本退出码按整机验收判定。已验证的 P6/r8 组合是加速器通过而整机失败。版本身份、覆盖审核及现有结果见 [时序报告](../reports/02_时序与面积.md)。
