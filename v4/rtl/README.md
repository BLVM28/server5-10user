# RTL 模块与连接

顶层 kwt_nice_core，仅编译 [rtl.f](../rtl.f) 的当前版本。单任务接口 `NICE → 描述符 → linear_core → tile_dma ↔ icb_master → 共享 RAM`。计算数据路径为 `x_buffer + w_panel → tile_compute → 3×mac8 → 24×dot64 → result_pages → row_pack → ICB`。

| 模块 | 工作、边界与 v4 改动 |
|---|---|
| [kwt_nice_core](kwt_nice_core.sv) | 验证自定义指令、8 字描述符、区间和重叠，启动核并返回完成状态。支持两个 format，紧凑模式的输出范围包括标签 |
| [kwt_linear_core](kwt_linear_core.sv) | 总调度器。冷启动 X/W0，逐组运行 DMA 和计算，等两者汇合后翻页。记录 sat_count 和 core_cycles |
| [kwt_tile_dma](kwt_tile_dma.sv) | 新模块。产生 X、W、b、Y 与标签的地址。对每一笔命令和应答负责，按实际写字数结束，区分读错与写错 |
| [kwt_icb_master](kwt_icb_master.sv) | 单笔 ICB。无等待时直通，命令/响应反压时分别保存，支持同拍命令及应答，不打断外部协议 |
| [kwt_tile_compute](kwt_tile_compute.sv) | 新模块。3×8 并行，广播 W，统计 33 个三行块，收尾逐行提交结果。done 保持到下次启动 |
| [kwt_x_buffer](kwt_x_buffer.sv) | 三条带 X，跨 1024 和尾部 128 宏。低/高半字分两拍写，计算时单拍读三个 X |
| [kwt_w_panel](kwt_w_panel.sv) | 一页八路权重。相同模块实例化两份，一页读、一页写，读数据在同步 SRAM 延迟后有效 |
| [kwt_result_pages](kwt_result_pages.sv) | 新模块。双页 Y 存储，执行器和 DMA 各访问自己的物理页，规则由总调度器保证 |
| [kwt_row_pack](kwt_row_pack.sv) | 新模块。17 位精确差分、符号扩展检查和 4/8/12/16 位打包。不能压缩时回退到绝对结果 |
| [kwt_sp_ram](kwt_sp_ram.sv) | 统一 SP128/SP1024 行为模型、工艺功能模型和综合宏的单口适配 |
| [kwt_mac8](kwt_mac8.sv) | 八路原子握手，一个 X 配八个 W。每个行条带实例化一份 |
| [kwt_dot64](kwt_dot64.sv) | 64 项乘积加偏置，三段反馈及两拍收尾，再统一量化 |
| [kwt_mul16_pipe](kwt_mul16_pipe.sv) | 四级 signed16 乘法流水，完整 signed32，稳态每拍一对 |
| [kwt_quantize](kwt_quantize.sv) | int40/F27 至 int16/F11 的最近偶数舍入和饱和 |

定位错误先看 NICE/ICB 的有效及就绪信号，再看 group_n、dma_page、operand_read、result_commit、row_m、mac_acc。精度错误先查 40 位累加，再查量化输出，最后查物理写回和解码。[测试台](../tb/README.md)
