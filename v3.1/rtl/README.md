# RTL · 从指令、页缓冲到矩阵写回

综合顶层为 kwt_nice_core。只使用 [rtl.f](../rtl.f) 中的 10 个源文件。外部指令和 ICB 之间的访问协议继承 v3，变化均在计算核内部。

| 模块 | 功能、相邻模块和 v3.1 变化 |
|---|---|
| [kwt_nice_core](kwt_nice_core.sv) | 接 NICE 请求，读 8 个描述符字，检查 magic/格式/层号/地址，启动 linear_core，汇合完成和错误 |
| [kwt_icb_master](kwt_icb_master.sv) | 将请求转为寄存 ICB 命令，处理零等待、延迟和反压，最多一笔在途。输入、权重预取和输出复用这一通道 |
| [kwt_linear_core](kwt_linear_core.sv) | **改动**。主状态机控制 32 组、99 行、64 项和写响应。保留行间运算重叠，新增 PANEL_IDLE/REQ/WAIT/STORE，记录另一页已提交字数，切页时可补读 |
| [kwt_x_buffer](kwt_x_buffer.sv) | 7×SP1024×16 装 6,336 个 X，按地址选 bank 并对齐读有效位。预取占 W 端口时同步暂停 X/W 发读 |
| [kwt_w_panel](kwt_w_panel.sv) | **改动**。8×SP128×16。地址 bit 6 选择上下页，低 6 位选 k，每次装两路，一次计算读八路。控制器确保同口读写互斥 |
| [kwt_sp_ram](kwt_sp_ram.sv) | 宏包装，选择行为、工艺功能模型或综合 cell，处理低有效控制和同步读。宏数组无需复位 |
| [kwt_mac8](kwt_mac8.sv) | 广播一个 X，接 128 位 W，八路同时握手。输出保持到控制器接收。每行产生 8 个 Y、累加值与饱和标志 |
| [kwt_dot64](kwt_dot64.sv) | 64 个 signed16 乘积加一次偏置，经三段进位反馈、排空和量化。由乘法器的 valid/last 决定结束，不硬编码返回拍数 |
| [kwt_mul16_pipe](kwt_mul16_pipe.sv) | **改动**。把 24 位重合部分的进位传播拆为两段，四级流水，每拍可接收一对输入，完整输出 signed32 |
| [kwt_quantize](kwt_quantize.sv) | int40/F27 转 int16/F11，最近偶数舍入、饱和并给出 saturated |

调试先看 nice_req、ICB 命令/应答握手。定位预取时同时看 group_n、panel_words、panel_state、issue_k、operand_read、mac_result_valid、take_result。STORE 拍不能发新的 W/X 读。定位精度时从 out_acc 到 out_y，最后检查所有 12,672 个写回字。[状态与边界](../ARCHITECTURE.md) · [自检平台](../tb/README.md)
