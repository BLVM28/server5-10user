# 5 号服务器个人工程区

工作根目录：`/storage2/2026contest/server5/s5_10usr`。常用入口是 **v2**。

```sh
cd /storage2/2026contest/server5/s5_10usr/v2
make env
make compile
make run
make timing
make gate JOBS=4
```

| 目录 | 内容 |
|---|---|
| [v2](v2/README.md) | 当前主线：三级乘法、计算/写回重叠；RTL、TB、向量、Makefile、最终映射及报告 |
| [v1](v1/README.md) | 保守对照版本，相同 Dense1 数值与接口契约 |
| [shared](shared/README.md) | 两版共用的服务器私有库、库配置、迁移清单及本轮总审计 |
| `kwt_public_snapshot.*` | 历史公共资料快照，仅参考，不作为另一个 v1/v2 工程 |
| `Desktop` | 既有桌面和上传暂存；不是活动工程入口 |

先读 [v2 操作手册](v2/SERVER_GUIDE.md)，再看 [实测结果](v2/SERVER_RESULTS.md)。`make` 显示帮助，`make report` 显示已有结果；每次修改 RTL 后要重新做功能、综合和时序检查，不能把历史 PASS 当作新改动的证明。

硬件完成 dot64 和 `99×64` 到 `99×256` 的 Dense1 矩阵计算。E203 通过 NICE 发描述符，ICB 搬运输入/权重/偏置，8 路 MAC 使用内部 SRAM，最后写回矩阵并报告完成。完整模型的 attention、LayerNorm、GELU、Dense2、分类头不等于这个 Dense1 硬件；yes/no 标签由完整模型给出。

当前公共 SoC 的 sysmem 仍是读零占位连接，正式共享 SRAM、固件和顶层验收尚缺。详细界限见实测报告。本次只在个人工作区写文件；公共目录只读，工艺文件和网表留在服务器。

2026-11-02 工作日志：旧 v1/v2 分别收进各自 history，逐文件校验归档；活动目录分开 rtl、tb、vec、流程、implementation、reports、packages。旧绝对路径只保留为历史证据，不再用于新 Makefile。迁移明细见 `shared/migration_20261102.json`。
