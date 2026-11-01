# v2 fix1 — 2026-11-01

本轮更新的是实现修复、跨工具验证和交付入口；`rtl/` 的逐文件哈希与冻结 v2 相同，原归档 `releases/20261101_v2/v2.zip` 未改动。

- SMIC40 在 `v2_reset` 基础上修复两处电容并重新平衡三处延迟单元，正式结果标签 `v2_eco5`，复现脚本见 `vm_eda/smic40/cap_eco.tcl`。
- 新 RHEL7 VMware 工作区 `/home/eda/kwt_vm_20261101`，完整 RTL 功能回归、GPDK045 dot64 独立 STA 和门级 SDF 测试。
- 复现入口为工作区根的 `vm_eda/Makefile`，最新结论以 `vm_eda/REPORT.md` 为准。原 `REPORT_V1_V2.md`、`server_eda/RESULTS.md` 保留为历史报告。
- 精确三级乘法和相邻行重叠仍保持原 v2 行为。新一轮没有声称额外周期加速；修复代价和时序余量在最新报告中单列。
