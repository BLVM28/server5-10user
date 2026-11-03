# TB · 如何定位错误

以下七个顶层各自打印 `ALL PASS, N/N`，任何 `$fatal`、退出码异常、缺少预期计数都算失败。服务器 `make run` 跑全部七组；Windows XSim 用同一组源文件。golden 与 DUT 分离。

| TB | 成功计数 | 查验内容 |
|---|---:|---|
| [tb_kwt_arithmetic](tb_kwt_arithmetic.sv) | 260/260 | 量化边界、最近偶数舍入、饱和标志、完整点积及复位恢复 |
| [tb_v3_carries](tb_v3_carries.sv) | 7/7 | v3 新增。独立 64 位整数参考覆盖最后一项跨两个段、两个进位同时挂起、正负极值、空拍和结果保持，在两个排空阶段分别 clear/reset 后验证下一任务 |
| [tb_kwt_icb](tb_kwt_icb.sv) | 4/4 | 单笔读写握手、背压、即时/延迟响应和错误 |
| [tb_kwt_system](tb_kwt_system.sv) | 29/29 | 12 个层任务、错误与恢复；逐项对照 40 位 acc、16 位 Y 和饱和计数，检查输出保护区及总线事务数 |
| [tb_kwt_overlap](tb_kwt_overlap.sv) | 5/5 | 当前行写回被阻塞时下一行仍可计算；检查结果保持、写错和恢复。此调度继承 v2 |
| [tb_kwt_negative](tb_kwt_negative.sv) | 58/58 | 非法指令、描述符、地址对齐、越界/回绕/重叠、读写错误和恢复；v3 支持缺省向量目录 |
| [tb_kwt_mul_pipeline](tb_kwt_mul_pipeline.sv) | 524288/524288 | 指定边界组合的完整乘积，连同复位和空拍共核对 527566 次；三级乘法继承 v2 |

[kwt_sram_sim.sv](kwt_sram_sim.sv) 是本地行为 SRAM。服务器 VCS 的日常入口用公共 RAMSP 宏模型，ASIC 综合用真正的 SRAM 库。NICE 请求和 ICB 外存由 TB 激励，真实 E203 跑固件属于下一层验证。

一个完整矩阵有 25,344 个 int16 输出，等于 12,672 个 32 位写字。系统套件运行 12 次首轮完整矩阵，并为恢复场景重复两次；比较吞吐时只取前 12 次。若 acc 已错，优先看输入配对和跨段进位；若 acc 正确而 Y 错，查量化、打包和写回地址。[逐层记录](../results/functional.json)

2026-11-03：保留 v2 比较口径，加入 v3 专项进位用例。
