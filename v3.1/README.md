# v3.1 · 八路 Dense1 权重预取与乘法流水

同一批 12 个 Dense1 矩阵任务，v3 用 **4,157,612 拍**，v3.1 用 **3,454,643 拍**。本地 XSim 和服务器 VCS 对 v3.1 得到相同周期，固定时钟下吞吐提高 **20.35%**。频率和面积用本版从头综合的完整 NICE 核单独评估。[时序、面积与吞吐表](RESULTS.md)

## 一条指令如何得到矩阵

CPU 把描述符地址放在 rs1，发自定义指令。NICE 前端检查层号与 X/W/b/Y 区间，经 32 位 ICB 读入 X 和第一组 W/b。每拍一个 X 广播给 8 个乘加器，每路读自己的一列权重。64 项有符号乘积加偏置，经 40 位累加、舍入和饱和得到 8 个 int16。总线用四笔 32 位写应答交回一行的这 8 列。32 组 × 99 行后，最后一次写应答成功才向 CPU 报完成。输出是 99×256 的 Dense1 矩阵。“yes”“no”等词由完整模型后续层和分类头生成。

## 相对 v3 的两项变化

| 改动 | v3 | v3.1 |
|---|---|---|
| 下一块权重 | 99 行完成后，从 ICB 串行装 256 个权重字 | 计算当前组时预取下一组，用原有 8 个 SP128 的地址 0–63 / 64–127 交替存放。进度不足时只补缺少的后缀 |
| 乘法末级 | 部分积到完整乘积在同一级合并，是 v3 的最差建立路径 | 在结果位 19/20 之间寄存进位，合并拆为两级，流水深度由 3 变 4。填满后仍每拍收一组 |
| 资源、接口 | 8 路、15 个 SRAM 宏、一笔在途 | 相同并行度与宏数。源码变化集中在 linear_core、w_panel、mul16_pipe 三个模块，另七个 RTL 与 v3 相同 |

## 从哪里开始

| 目录 | 阅读或运行目的 |
|---|---|
| [架构说明](ARCHITECTURE.md) · [RTL](rtl/README.md) | 数学等价、状态机、页切换、端口冲突及每个模块的职责 |
| [TB](tb/README.md) · [向量](vec/README.md) · [本地脚本](py/README.md) | 逐元素检查、慢总线回退、错误恢复和同 workload 周期 |
| [服务器操作](SERVER_GUIDE.md) · [EDA 脚本](server_eda/README.md) | 在正式目录运行 make，读实际通过/失败标志 |
| [结果](results/README.md) · [服务器验收](SERVER_RESULTS.md) · [私有映射](implementation/README.md) | 区分 RTL 功能、布局前 STA、SDF 及整机结论 |
| [E203 接入](integration/README.md) | 描述符、驱动、共享 RAM 配置及待整机验证事项 |
| [分类包](packages/README.md) · [交付记录](releases/README.md) · [运行报告](reports/README.md) · [构建区](build/README.md) · [试验记录](history/README.md) | 源码、可复现实验、证据和生成物的位置 |

服务器从 `/storage2/2026contest/server5/s5_10usr/v3.1` 运行 `make check`。只比较吞吐时运行 `make paired`，只看赛题统一 150 MHz 时序时运行 `make timing PERIOD=6.666667`。
