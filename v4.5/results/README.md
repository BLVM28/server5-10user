# 结果与源文件核验

| 文件 | 内容 |
|---|---|
| [r7_performance.json](r7_performance.json) | 同一 VCS 计时平台下，v4.4 和当前 v4.5 的周期拆解、加载字数和每秒任务数换算 |
| [r7_source_sha256.txt](r7_source_sha256.txt) | 当前 RTL 的服务器 VCS 与 DC 源码包逐文件 SHA256 |
| [r7_timing.json](r7_timing.json) | 当前网表的时钟周期、裕量、面积及服务器原始报告位置 |
| [rtl_performance.json](rtl_performance.json) | v4.5 r2 在修订取指逻辑前的配对结果 |
| [r2_source_sha256.txt](r2_source_sha256.txt) | 比赛服务器 VCS 与 DC 运行用包的逐文件 SHA256 |

当前运行目录为 `/storage2/2026contest/server5/s5_10usr/v4.5/r7`。源码包 SHA256 为 `07f62dae5e4a8efaa1dd6f3b9973407ced9228d4e4d71f98550cdd0eef841895`。VCS 结果在 `soc/work/rtl_20261109_100519_706043`。同一目录的 `performance.json`、`input_sha256.json` 和各 `run_*.log` 可核对原始周期与通过标记。EDA 原始文件保留在比赛服务器个人工作目录。

综合、回标和功耗的状态见 [验证报告](../REPORT.md)。
