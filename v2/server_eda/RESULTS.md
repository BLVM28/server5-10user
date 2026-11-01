# v2 服务器结果入口

实际结果统一见 [v1/v2 对比报告](../REPORT_V1_V2.md)，本地结构化摘要为 `../build/server_observed_v2.json`。这是 VNC 观察整理，不是下载的原始日志。

原始证据在 `/storage2/2026contest/server5/s5_10usr/kwt_versions_20261101/v2/build`：

- server_functional、server_activation、server_overlap、e203_binding：最终 RTL 回归。
- v2_150：150 MHz 初次映射和宏模型/乘法专项结果。
- v2_reset：最终修复后网表、SDF、SS/FF PT、门级记录。
- benchmark_comparison.json、benchmark_v1、benchmark_v2：同 TB 周期比较。
- v1_sameflow_150、v1_reset：原 v1 用相同优化流程的对照，冻结 v1 不变。

工具完成与时序满足是不同判据。请同时查看 sta_result.json 的 timing_slack_met、reported_constraints_met，以及每角 coverage.rpt、untested.rpt、violations.rpt。max/min slack 非负不表示所有电容、覆盖率或后端签核问题已解决。
