# 本科任务 1、2 最终提交 · v4.3-timing r8

冻结版本为 **r8**。`rtl.f` 的 15 个 RTL 文件与服务器实测源码逐字节一致。赛题工作点为 150 MHz，160 MHz 为本版加速器含接口的时序余量验证。以赛题印刷页 3、7–8、10–13 为准。[赛题原件](../01_核心参考/赛题介绍.pdf)

| 目录 | 提交内容 |
|---|---|
| [`rtl/`](rtl/README.md) 与 `rtl.f` | 任务 1 的乘法、点积、数值处理，以及任务 2 的矩阵、缓冲、控制、码流、读写与 NICE 接口 RTL |
| [`verification/`](verification/README.md) | 计分板、仿真 SRAM、冻结输入与预期结果、可运行 Makefile |
| [`model/`](model/README.md) | 与 RTL 一致的定点模型、冻结 profile、预训练参数导出、输入转换和精度计算 |
| [`interface/`](interface/README.md) | 数值与线格式、指令 ABI、E203 接口参考及 C 编解码头文件 |
| [`flow/`](flow/README.md) | P6 服务器上的功能与加速器 STA 复验入口 |
| [`reports/`](reports/README.md) | 功能、时序、数值精度报告，组件复测日志及实测源码身份 |

## 已验收的结果

| 检查 | r8 结果 |
|---|---|
| E203 整机 RTL 功能 | 两次 ROM 启动，12 项矩阵，58,547 个写回字全部逐位一致 |
| 加速器含接口，150 MHz 主条件 | 最差建立 / 保持 **+0.546274 / +0.011303 ns** |
| 加速器含接口，160 MHz 主条件及 35 组 PVT/RC | 最差建立 / 保持 **+0.253513 / +0.011303 ns**，转换时间、电容和扇出违例均为 0 |
| 同一整机测试的周期 | 2,015,289 拍，NICE 区间 1,216,225 拍 |

从 `final/` 在 Linux 或 WSL 执行以下命令。数值对照依赖 Python 和 NumPy，RTL 回归依赖 Make、Icarus、Verilator 与 C++ 工具链。

```bash
sha256sum --quiet -c SHA256SUMS.txt
make -C verification check
python3 -B model/verify_frozen.py
```

## 分工

本目录是任务 1、2 的交付件和对接资料。任务 3 负责人用此版 RTL 完成平台驱动、整机 STA 与约束、综合网表和综合前后一致性、正式吞吐、面积和功耗报告。原 P6 整机仍有 IFU 建立、共享 SRAM 保持、UART 覆盖和平台电气违例，`SOC_160_PASS=0`。原 v4.3 自选 600 样本的模型精度和本版 12 项 RTL 逐位验证分别列在报告中。 [时序与边界](reports/02_时序与面积.md) [精度口径](reports/03_数值精度.md)

模型及权重来源为 ARM `keyword-transformer` 提交 `237e4097` 的 KWT-1 `best_weights`。RTL 源自本项目 v4.3/r8，文件内保留原许可证标记。P6 对接参考固定到提交 `5530ae66d132c73af3dac3683a995a456bd53afa`。 [模型上游](https://github.com/ARM-software/keyword-transformer/tree/237e4097)
