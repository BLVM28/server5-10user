# v4.4 Dense1 加速器

本版在 v4.3 的四路码流、双页缓存和 8×16 MAC 上改造 SRAM 边界、乘法流水和数据搬运。矩阵仍为 99×64 乘 64×256 后加偏置。描述符格式 0x00010004、固定数值格式、层参数和黄金结果沿用 v4.3。

| 目录 | 内容 |
|---|---|
| rtl/、rtl.f | 独立可综合的任务 1、2 RTL。kwt_nice_core 保留原 NICE/ICB 端口，支持有序返回和反压。 |
| tb/ | 算术和 4 种总线端点的 bit-exact 回归，复用 v4.3 的向量。 |
| soc/rtl/ | 按队友 P6/P7 的平台接线实现 System Bus 版本，包含 512 KiB 共享 SRAM、ITCM/DTCM 适配和复位输出。 |
| soc/firmware/ | RV32 驱动、启动代码和 ITCM 装载映像。 |
| soc/tb/ | ROM 启动、CPU 自检、12 层结果写回和门级对照。 |
| soc/flow/ | 仿真与综合共用源清单、VCS 回归、DC 35 组合和 SDF。 |
| results/ | 实测结果与适用范围。 |

## RTL 与集成入口

独立任务 1、2 可以用原来的 v4.3 测试向量跑 kwt_nice_core。整机候选选用赛题印刷 p3 允许的 System Bus 方式。CPU 写 0xA0080000 提交描述符地址，读 0xA0080004 获取状态，bit31 为忙，低 31 位为返回码。数据仍通过 0xA0000000 起始的 512 KiB 共享 SRAM 交换。E203 执行真实启动程序、描述符写入和命令下发。加速器作为独立的 32 位 DMA 主设备访问同一 SRAM。E203 原 NICE 插槽在这个整机配置下拒绝自定义指令，原 NICE 入口留在独立核。

[架构与时序路径](ARCHITECTURE.md) · [结果与验收状态](results/README.md)

## 服务器复现

在服务器个人工作区部署一份独立 v4.4 目录，核对源清单。配置集中在 soc/flow/paths.tcl。使用比赛原始平台、P6 已验证的宏模型、SMIC40 和原 v4.3 向量。工程自带已经用于回归的 RV32 固件。如果在服务器嵌套目录重建固件，执行 `make firmware ABI=/实际路径/v4.3/integration`。

1. make run 运行 VCS 回归，并在相同 TB 中对照 P6 的串行及流水装载。
2. make timing 运行整机映射、GPIO/AON 短输出缓冲及七个 PVT × 五个 RC。主组合仍有违例时输出原始报告并返回失败。可用 `make timing RESUME=/实际路径/原映射运行目录` 恢复同源检查点。恢复前比对 RTL SHA256，恢复后比对原主组合各路径组的裕量。
3. make gate 用建立和保持各自最差组合的 SDF 完成 12 层整机复查。
4. make check 顺序执行以上三步。

功能门级可单独运行 `make gate-functional MAPPED_RUN=/实际路径/映射运行目录`。它使用同一设计的综合网表和真实功能模型，逐字核对 12 层结果。若仅更新下载固件，可用 `make gate DC_RESULT=/实际路径/last_dc.json` 对同源网表复跑 SDF，脚本先核对 RTL SHA256。

原始网表、工艺文件、逐角波形和完整 EDA 日志保留在授权的服务器工作区。提交时按赛题使用同一版 RTL、网表、约束和测量窗口。
