# 服务器运行记录

`delivery_checks/` 保存正式目录的首次命令日志与退出状态。`before_clean_*` 保存 clean 前的日志、JSON、文本及时序报告。当前详细功能日志在 `../build/manual/runs/default/<TB>/run.log`；对应的 verified.json 记录计数、源码/向量/日志哈希和矩阵周期。

时序失败先到 `../build/manual/timing/<NETLIST>/<PERIOD>/kwt_nice_core_ss` 或 `_ff` 查看 setup.rpt、hold.rpt、violations.rpt。coverage.rpt 说明未测项，metrics.txt 给出最差路径端点。GitHub 中可直接阅读的是 [正式目录验收](../SERVER_RESULTS.md) 和 [频率研究报告](../RESULTS.md)。
