# v4.2 · 降低 Dense1 误差

同一组 600 个验证输入，最大逐层 NRMSE 从 v4.1 的 **1.32842%** 降到 **0.14181%**，最差单样本单层为 **0.19385%**。150 MHz、固定 12 个冷任务实测 **2,028.51 tasks/s**；12 类语音代表输入合计 144 个任务为 **1,916.67 tasks/s**。合成压力组为 **1,276.68 tasks/s**。[结果、慢层及边界](RESULTS.md)

四行八列阵列、精度优先的分层定点和可逆残差编码共用同一份 RTL 与网表。SMIC40 布局前 150 MHz 慢角建立余量 **+0.947604 ns**，保持 **+0.153858 ns**，整核面积 **0.397244 mm²**，较 v4.1 **+16.59%**。[模块关系](ARCHITECTURE.md) · [服务器实测](SERVER_RESULTS.md)

| 我想做什么 | 入口 |
|---|---|
| 在 5 号服务器复现 | [手工指南](SERVER_GUIDE.md)，在 v4.2 下运行 `make precision`、`make timing` |
| 理解计算与协议、把矩阵交给 E203 | [RTL 导航](rtl/README.md)、[C API 和内存布局](integration/README.md) |
| 独立验证、找每组原始拍数 | [测试](tb/README.md)、[模型](py/README.md)、[数据](vec/README.md)、[实测 JSON](results/README.md) |
| 取得交付和确认文件身份 | [五个分类包](packages/README.md)、[发布清单](releases/README.md)、[本轮迭代](HISTORY.md) |
