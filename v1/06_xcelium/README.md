# 简易 Xcelium 功能入口

`run.sh` 切到上级项目目录后调用 `py/run_linux.py --sim xrun --tag xcelium`，参数继续向后传。需要 Linux 已配置 xrun；默认算术/ICB/系统三个 TB。

私有 VM 更完整、已适配的入口是其根目录 `make -C flow v1` 或 `v2`，包含 STA/SDF 和审计。此小入口只做 RTL 功能，不替代完整工具流程。

工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。

[返回工作区首页](../../README.md)
