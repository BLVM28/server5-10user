# v4.3：保留 v4.2 精度的四路码流与 8×16 阵列

本版完成本科 Dense1 加速器的 RTL、NICE/ICB 接口、软件编解码、测试和服务器 EDA 脚本。一个 task 是一张 `99×64 · 64×256 + bias` 矩阵，从接受 NICE 指令计时，包含冷装载 X/W/b 和最后一次 Y 写应答。12 个层参数复用同一硬件；这不是一秒语音识别的次数。

责任及状态以根目录 [材料划分](../材料划分.md) 为准：任务1、2交付RTL和独立功能/数值验证；任务3负责实际SoC、正式综合/统计和最终提交。当前正式整机吞吐未测得，下列吞吐/PPA均为明确条件下的独立核预评估。精度公式修订记录见 [metric_fix.json](results/metric_fix.json)。

固定 12 任务在公共 E203 SRAM 控制器加一拍同步 RAM 下为 **193,356 拍，150 MHz 为 9,309.25 tasks/s**。150 MHz 慢角建立余量约 **1.47 ns**；完整加速器综合面积约 **1.044 mm²**。精度参数与 v4.2 完全相同，600 样本重新验证的最差单层汇总 NRMSE 为 **0.14181%**。最终逐组、工艺角和功耗数据见 [结果](RESULTS.md)、[服务器证据](SERVER_RESULTS.md)，不要只引用这一段的固定输入成绩。

| 入口 | 要解决的问题 |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 为什么扩大到 8 行 16 列；模块如何协作；哪里仍受总线限制 |
| [rtl/README.md](rtl/README.md) | 15 个正式 RTL 文件及信号、流水和存储职责 |
| [integration/README.md](integration/README.md) | E203 对接、描述符、四路数据格式、C/RV32 接口 |
| [tb/README.md](tb/README.md) | 四种总线、独立计分板、错误与复位、门级测试 |
| [SERVER_GUIDE.md](SERVER_GUIDE.md) | 在服务器直接 make clean/compile/run/waves/verdi/timing/power |
| [py/README.md](py/README.md) | 原始向量、两种独立生成器、语音复测、交付校验 |
| [results/README.md](results/README.md) | 可公开的机器可读测量，不混入网表或工艺库 |
| [packages/README.md](packages/README.md) | rtl/tb/makefile/flow/vectors 五个独立 ZIP |
| [HISTORY.md](HISTORY.md) | 本轮决策、修改、验证和仍待整机补齐的事项 |

**本地工作区**为 Git 克隆库下的 `v4.3`；旧桌面工作区的同名目录是该目录的链接。**服务器工作目录**为 `/storage2/2026contest/server5/s5_10usr/v4.3`。源码、说明、向量与包的发布清单在 `releases/source_manifest.json`，服务器私有的综合网表、波形和工具输出位于各自的 `implementation/`、`build/`。

公共库的 E203 控制器已实际参加仿真，但公共顶层仍未提供比赛正式的 512 KiB 共享 RAM 实现和地址分配。高吞吐要求 SRAM 路径支持一拍响应及应答/新命令同拍交接；旧版随机长等待压力条件也保留并分别报告。当前功耗为加速器本体含局部 SRAM 的前布局估算；CPU、共享 RAM、互连和布线后寄生需后续整机补测。
