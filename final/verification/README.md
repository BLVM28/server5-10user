# 功能验证工程

从 `final/` 在 Linux 或 WSL 运行。默认 DUT 文件清单为 `../rtl.f`，编译与仿真输出位于 `verification/build/`。`BUILD` 可指定其他绝对输出目录，`JOBS` 控制 Verilator 构建并行数。

```bash
make -C verification units
make -C verification matrix
make -C verification check
make -C verification model
```

| 入口 | 检查与通过标记 |
|---|---|
| `units` | ICB `completed=2000 aborted=2 zero=1000 delayed=1001`。乘法 `checked=16449 aborted=2`。点积 `ALL PASS, 64/64` |
| `matrix` | 6.25 ns RTL 仿真时钟，`STREAM GUARD PASS 25/25` 及 `ALL PASS, 29/29 NICE/matrix scenarios` |
| `model` | 从 36 个原始定点输入重新生成 100 个固定 hex，`MODEL_FROZEN_PASS layers=12 raw_files=36 hex_files=100` |

`tb/` 的计分板覆盖符号、舍入、饱和、连续点积、气泡、反压、异常、复位、跨页读写与码流边界。`vec/raw/` 是每层的原 X/W/b，`vec/worst/` 是同一组 12 层矩阵的码流、累加和黄金结果，逐文件 SHA256 见 `vec/manifest.json`。`worst` 是原验证组名。验证数据只由计分板与软件复核入口读入。

本地功能和数值对照见 [复测日志](../reports/README.md)。E203 启动及厂商 SRAM 验证使用 [P6 服务器流程](../flow/README.md)。
