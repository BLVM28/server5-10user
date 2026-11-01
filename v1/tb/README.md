# v1 测试平台

测试平台用来激励和核对 RTL，不参加综合，也不是已运行真实 CPU 的证明。

| 文件 | 验证内容 | 通过意义 |
|---|---|---|
| tb_kwt_arithmetic.sv | dot64、bias、完整 acc、RNE、饱和、复位、连续任务/背压 | 260/260 算术场景与独立整数 golden |
| tb_kwt_icb.sv | ICB 同拍/延迟应答、命令保持与错误 | 4/4 协议场景 |
| tb_kwt_system.sv | NICE 请求、描述符、全部矩阵、12 层 W/b、范围/格式/复位/读写错误 | 29/29；行为内存与请求激励，不是真 E203 |
| kwt_sram_sim.sv | 本地同步 SRAM 行为模型 | 能做功能仿真，不能替代实际宏时序 |
| tb_foundry_sram.sv | 小规模真实宏接口功能检查 | 需要服务器库/专用入口 |

默认系统输入在 `../vec`；用 `--vectors` 指向新的模型激活目录。`KWT_TEST_SWAP` 测半字交换，`KWT_TEST_W1024` 测 W bank 大宏回退。比较失败先记录首个 layer/row/group/lane/word，禁止改 expected 值来迎合 RTL。

从根运行：`python v1/py/run_xsim.py --tag learn_system --tops tb_kwt_system`。原始日志归档，现有脚本会重建 build。

工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。

[返回工作区首页](../../README.md)
