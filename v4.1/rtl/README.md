# 18 个可综合模块

顶层 [kwt_nice_core](kwt_nice_core.sv) 接收 NICE 指令、取八字描述符、检查地址、返回状态。[kwt_linear_core](kwt_linear_core.sv) 调度页切换、算术与搬运，对三种格式选择正确的保护区。[kwt_icb_master](kwt_icb_master.sv) 保持命令/返回稳定，覆盖同拍返回与阻塞。模块顺序在 [rtl.f](../rtl.f)。

| 部分 | 模块及职责 |
|---|---|
| 格式选择 | [kwt_tile_dma](kwt_tile_dma.sv) 按格式路由数据、应答和写使能。同一任务共享一套算术/宏/ICB。原始与无损路径使用 [kwt_legacy_dma](kwt_legacy_dma.sv) |
| 快速输入 | [kwt_block8_reader](kwt_block8_reader.sv) 读取并校验块头，四个尾数扩展为两对 int16，生成 X 条带地址和 W 页写地址。装载改按 W 八列一组连续寻址 |
| 快速输出 | [kwt_block8_writer](kwt_block8_writer.sv) 保留一个待发编码行，协调 SRAM 预读及最后应答。[kwt_block8_encoder](kwt_block8_encoder.sv) 用四级流水计算指数、移位、舍入和封装 |
| 无损输出 | [kwt_row_pack](kwt_row_pack.sv) 并行计算高字节有借位/无借位结果，保持 v4 的全部无损差分模式 |
| 存储 | [kwt_x_buffer](kwt_x_buffer.sv) 提供三条 X 读通路，[kwt_w_panel](kwt_w_panel.sv) 和 [kwt_result_pages](kwt_result_pages.sv) 分别负责 W 和 Y 双页。[kwt_sp_ram](kwt_sp_ram.sv) 适配指定单口宏 |
| 矩阵算术 | [kwt_tile_compute](kwt_tile_compute.sv) 驱动三个 [kwt_mac8](kwt_mac8.sv)，每个 mac8 含八个 [kwt_dot64](kwt_dot64.sv)。[kwt_mul16_pipe](kwt_mul16_pipe.sv) 连续接受 signed16 乘法。[kwt_quantize](kwt_quantize.sv) 对 40 位和完成 RNE 和饱和 |

一个任务的主路径为 NICE → linear_core → DMA 与 ICB → X/W 页 → 24 路 dot64 → Y 页 → 各格式输出器 → ICB 写应答 → NICE 完成。三种格式的数学和事务区别见[架构](../ARCHITECTURE.md)。
