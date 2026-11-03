# 测试台与判据

系统 BFM 沿用 v4 的 RNG 种子 0x20261101、单响应队列、随机等待、ready/valid 连续性检查和计时起止点。每组跑 12 个首次冷任务、出错/复位恢复和两次恢复重测。吞吐只取前 12 次。FAST 分支监视已执行的全部 25,344 个 acc40，检查物理 6,752 字、解码的全部 int16、写保护、饱和数以及实际读写计数。

| 测试 | 覆盖 |
|---|---|
| tb_kwt_arithmetic、tb_v3_carries、tb_kwt_mul_pipeline | 算术 260 项、分段进位及取消 7 项、穷举 524,288 个乘法边界样本（含空拍和复位另作核对） |
| tb_kwt_icb、tb_kwt_overlap、tb_kwt_negative | 4 项总线握手、5 大类交叠/恢复、58 项非法输入及读写错误 |
| tb_kwt_system、tb_kwt_compact | 旧两种格式，每套 29/29。tb_kwt_codec 独立测试 4096 组差分边界 |
| [tb_kwt_block8](tb_kwt_block8.sv) | 三种格式共享同一系统台。每套 29/29 外加非法 X 头、非法 W 头、最后指数字写错、末地址越界 4 项 |
| [tb_kwt_bfp_codec](tb_kwt_bfp_codec.sv) | 穷举 65,536 个有符号输入，改变相邻七列，逐拍核对四级编码结果 |
| [tb_kwt_block8_immediate](tb_kwt_block8_immediate.sv) | 12 层都在接收 ICB 命令的同拍返回应答，逐笔检查数据并导出实际 RAM。用于 C 消费端交叉检查，与随机等待计分分开 |
| [tb_kwt_modes](tb_kwt_modes.sv) | 单实例不断电、不复位，中间故意给出坏 W 头，在三种格式间反复切换，逐笔检查合法任务与错误恢复 |
| [门级台](../server_eda/tb_core_all_gate.sv) | 在引脚检查紧凑新格式的实际网表仿真，回标 SS/FF 的 SDF，核对全部载荷、指数及解码元素 |

[服务器测试命令](../SERVER_GUIDE.md) · [准确度报告](../RESULTS.md)
