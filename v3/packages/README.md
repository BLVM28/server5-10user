# 分类包 · 取哪个文件

| 包 | 包含内容 | 适合的工作 |
|---|---|---|
| [rtl.zip](rtl.zip) | rtl/ 的 10 个模块、说明、rtl.f | 看硬件实现或提供综合 filelist |
| [tb.zip](tb.zip) | 七个自检顶层、行为 SRAM 和 TB 说明 | 在本地或服务器重新验证功能 |
| [makefile.zip](makefile.zip) | 版本根 Makefile 与 server_eda 转发 Makefile | 恢复统一命令入口 |
| [flow.zip](flow.zip) | server_eda、integration、py、操作手册、架构/结果说明、工艺结果摘要 | 恢复仿真、综合、STA 和 CPU 对接工具 |
| [vectors.zip](vectors.zip) | vec/ 全部黄金数据、各子目录说明、固定向量指纹清单 | 提供可直接使用的仿真输入和期望值 |

成员路径以 v3 根目录为基准，例如 rtl.zip 内是 `rtl/kwt_dot64.sv` 和 `rtl.f`。把所需包展开到同一版本根。VCS/工艺工具还需要服务器已有的 v2 启动器、shared 库配置及合法库环境。

[manifest.json](manifest.json) 给出每个 ZIP 的 SHA-256、大小、成员数及逐成员 SHA-256。服务器运行 `make package`，Windows 在克隆库根运行 `python v3/py/assets.py package`。生成器固定成员顺序和时间戳，发布前重新读出每个成员并核对其内容。公开包收录工程源码、导出向量及其说明；工艺库、网表、DDC、SDF 在服务器的 implementation/build 下单独保存。
