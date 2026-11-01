# v1 fix1 — 2026-11-01

本轮更新的是实现修复、跨工具验证和交付入口；`rtl/` 的逐文件哈希与冻结 v1 相同，原归档 `releases/20261101_v2/v1.zip` 未改动。

- 原 SMIC40 负 hold/removal 使用 SS/FF 配对库、真实延迟单元和复位缓冲修复，正式结果标签 `v1_reset`。
- 新 RHEL7 VMware 工作区 `/home/eda/kwt_vm_20261101`，完整 RTL 功能回归、GPDK045 dot64 独立 STA 和门级 SDF 测试。
- 复现入口为工作区根的 `vm_eda/Makefile`，最新结论以 `vm_eda/REPORT.md` 为准。原 `validation.md`、`server_eda/RESULTS.md` 保留为当时的历史报告。
- 本次没有改变 ABI、正式地址默认禁用策略、定点数值语义或流水线延迟。工艺相关网表 ECO 不应写成 RTL 中的延迟语句，也不能照搬到其它工艺。
