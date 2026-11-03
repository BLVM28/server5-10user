# RTL · 一次矩阵任务经过哪些硬件

综合入口是 `kwt_nice_core`。只编译 [rtl.f](../rtl.f) 指向的本版本 10 个模块。NICE 前端与矩阵控制器分时使用同一个 ICB master；内部计算路径为 `linear_core → x_buffer/w_panel → mac8 → 8 × dot64 → 乘法与量化`。

| 模块 | 工作和连接 | 相对 v2 |
|---|---|---|
| [kwt_nice_core](kwt_nice_core.sv) | 接收指令和 rs1 描述符指针，读取 8 个 32 位字，检查后启动 linear_core；向 CPU 返回状态或错误 | 同文件 |
| [kwt_icb_master](kwt_icb_master.sv) | 寄存命令，发起对齐的 32 位读/写，固定 size=2，最多一笔在途；读和写都等待响应 | 同文件 |
| [kwt_linear_core](kwt_linear_core.sv) | 装载全 X 和一个 W/b 面板，循环 32 组、99 行和 64 项；握手后写回 4 字；维护错误、饱和计数和 core_cycles | 同文件，包括当前行写回与下一行计算重叠 |
| [kwt_x_buffer](kwt_x_buffer.sv) | 6336 个 X 映射到 7 个 1024×16 单口 bank；13 位地址高 3 位选 bank，读 bank 与 valid 对齐 | 同文件 |
| [kwt_w_panel](kwt_w_panel.sv) | 当前 64×8 权重由 8 个 bank 分担；装载时一个 32 位字写两个 lane，计算时同一 k 同时读出八个 W | 同文件 |
| [kwt_sp_ram](kwt_sp_ram.sv) | 适配 AW=7/10 的 SP128/SP1024 宏，处理低有效 CEN/GWEN/WEN。仿真选择厂商包装或行为模型，综合选择库 cell | 同文件 |
| [kwt_mac8](kwt_mac8.sv) | 单个 X 广播给 8 路，权重总线 128 位、偏置 256 位、累加结果 320 位。所有 lane 共同接受一组操作数、共同交付结果 | 例化 dot 时设置 `EXPOSE_BUSY=0`，省去没有接收者的输出驱动 |
| [kwt_dot64](kwt_dot64.sv) | 偏置初始化，接收 64 对 signed16。乘积返回时更新三段，最后排空、量化并保持结果直到 out_ready | 40 位反馈拆分为 14+13+13 位加两个进位位，这是提频的主要 RTL 改动 |
| [kwt_mul16_pipe](kwt_mul16_pipe.sv) | 16×16 有符号乘法，操作数、部分积、合并三级，给出完整 signed32；valid/last 随数据同行，可连续每拍发射 | 同文件 |
| [kwt_quantize](kwt_quantize.sv) | int40/F27 到 int16/F11，最近偶数舍入和饱和；同时报告 saturated | 同文件 |

**读 dot64 的顺序。** `IDLE` 用 bias 写入所有累加字段，`RUN` 的有效乘积才推进和。`FOLD_FIRST`、`FOLD_LAST` 各加一次零，吸收延迟的跨段进位。`ROUND` 输出标准二进制的 out_acc 并量化，`RESPONSE` 保持结果。独立 dot 的 `EXPOSE_BUSY` 默认值为 1。两拍排空的周期代价和数值不变量详见 [架构说明](../ARCHITECTURE.md)。

调试时先看 req_valid/ready，再看 ICB cmd/rsp 的 valid/ready、地址、数据及 error。只有 valid 和 ready 同时有效才算完成该通道握手。`nice_rsp_valid` 应在最后一次写应答之后出现。若总线正确、数值仍错，用算术和进位 TB 比较 out_acc，再比较 out_y。[自检平台](../tb/README.md)

2026-11-03：发布通过 200 MHz 布局前 STA 的完整核心源文件，映射后的单元修复单独保存在 server_eda。
