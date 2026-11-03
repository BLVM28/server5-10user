# v4.1 · 150 MHz 的 Dense1 吞吐版本

**保守主频 200 MHz，最高双角通过测试点 205 MHz**。210 MHz 慢角建立违例。完整核心前端映射面积 0.340720 mm²，较 v4 增加 6.55%。[八个频点与余量](RESULTS.md)

一个任务从 NICE 接收指令起算，冷读描述符、输入、权重、偏置，完成 99×64 乘 64×256 并等待最后写应答。同一批 12 层，Block8 用 **1,127,815 拍**，150 MHz 下为 **1,596.01 tasks/s**。目标上限是 1,200,000 拍，余量 72,185 拍。实际 E203 指令调度和数据消费另需上板或整机测量。[实测与时钟](RESULTS.md) · [复现命令](SERVER_GUIDE.md)

v4.1 从 v4 的三行八列阵列继续开发。保留原始定点输出和 v4 的无损差分输出，增加格式 0x00010002。新格式用每组一个指数和八位有符号尾数减少总线流量。新格式有量化误差，自选 600 条验证语音的最大逐层 NRMSE 是 **1.32842%**，最差单样本单层 **1.61337%**。v4 的历史整数格式对应 **0.03891%** 最大逐层 NRMSE。比赛要求每个性能任务独立满足 3%。[准确度记录](results/accuracy.json) · [赛题印刷页 10–11](../01_核心参考/赛题介绍_原文.txt)

| 目录 / 材料 | 使用方式 |
|---|---|
| [架构](ARCHITECTURE.md) · [rtl](rtl/README.md) | 读数、计算、输出编码、临界路径的调整 |
| [integration](integration/README.md) · [py](py/README.md) | 描述符、三种格式、C 编码与解码、准确度复现 |
| [tb](tb/README.md) · [vec](vec/README.md) | 总线压力、完整矩阵、14 组数据与可独立重建的黄金值 |
| [server_eda](server_eda/README.md) · [服务器验收](SERVER_RESULTS.md) | VCS、DC、PT、SDF 及日常 make |
| [results](results/README.md) · [packages](packages/README.md) · [releases](releases/README.md) | 数值证据、五个分类包和校验清单 |
| [history](history/README.md) · [reports](reports/README.md) · [implementation](implementation/README.md) · [build](build/README.md) | 实验记录、服务器私有工艺结果、本地产物 |
