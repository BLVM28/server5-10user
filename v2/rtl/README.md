# v2 RTL 模块

本目录只含硬件逻辑。顶层职责由 `kwt_nice_core` 负责，平台真正替换入口在 `../integration/e203_subsys_nice_core.v`；通过 `../rtl.f` 编译，TB 和 Python 不进综合。

| 文件 | 职责 | 主要接口/时序 |
|---|---|---|
| [kwt_nice_core.sv](kwt_nice_core.sv) | NICE 请求/描述符控制 | 32 位指令与 rs1；描述符 8 字；选择描述符或 core 的访存；末次写完成才回应。状态 IDLE/FETCH/FETCH_WAIT/VALIDATE/START/RUN/RESPONSE。 |
| [kwt_icb_master.sv](kwt_icb_master.sv) | ICB 事务桥 | 请求寄存→SEND→WAIT_RSP→RETURN_RSP；单笔在途；读写均需应答；valid/ready 等待时命令不变；size 固定 2。 |
| [kwt_linear_core.sv](kwt_linear_core.sv) | 整矩阵状态机 | 检查地址、装 X、按 32 个列组装 W/b、遍历 99 行/64 项，保持 8 路结果并分 4 字写回；管理错误与任务完成。 |
| [kwt_x_buffer.sv](kwt_x_buffer.sv) | 全部 X 缓存 | 6336 个 int16 放 7 个 SP1024；13 位线性索引，高 3 位选 bank，低 10 位是地址；读 bank 与 valid 寄存对齐。 |
| [kwt_w_panel.sv](kwt_w_panel.sv) | 当前 8 列 W 缓存 | 8 个独立 bank，每 bank 服务一个 lane；读同一个 k 得 8 个 W；一个总线字可写两个不同 lane。默认每 bank SP128。 |
| [kwt_mac8.sv](kwt_mac8.sv) | 8 路原子广播/汇合 | 单个 X 广播、8 个 W/b 独立；bias 总线 256 位、W/Y 总线 128 位、完整 acc 总线 320 位；所有 lane 同时握手。 |
| [kwt_dot64.sv](kwt_dot64.sv) | 一个输出的点积 | bias32 初始化 acc40；接受恰好 64 对 signed16；等待 mul_last 排空；量化后保持 out_y/out_acc 至接收。IDLE/RUN/ROUND/RESPONSE。 |
| [kwt_mul16_pipe.sv](kwt_mul16_pipe.sv) | 精确 signed16×16 | 输出完整 signed32，valid/last 与数据一致；不支持随意输出反压。v1 为一级，v2 为操作数/部分积/合并三级、II=1。 |
| [kwt_quantize.sv](kwt_quantize.sv) | 唯一结果量化点 | acc40/F27 → Y16/F11；最近偶数舍入、int16 饱和；不改变中间乘积/累加精度。 |
| [kwt_sp_ram.sv](kwt_sp_ram.sv) | 宏适配 | AW7/AW10 分别绑定 SP128/SP1024；CEN/GWEN/WEN 低有效、WEN16；行为仿真/厂商仿真/综合 cell 分支明确。 |

组合关系：`nice_core → linear_core → x_buffer/w_panel → mac8 → 8×dot64 → mul16_pipe/quantize`；nice_core 与 linear_core 分时复用一个 icb_master。x_buffer/w_panel 经 sp_ram 例化 15 个实际存储宏。

本版要点：v2 内部 clear 清乘法、dot 与预取状态；y_hold 和 MAC 响应寄存器组成两个结果槽，当前行慢写回时允许下一行先算完。

调试规则：valid&&ready 才接收；流水 last 随乘积推进；写命令握手不是写完成；复位不清 SRAM，全装载后才读。数值 X/W/Y 为 int16，b 为 int32，acc 为 int40；F 分别 11/16/11、27、27。修改这些值须同步金模、转换、向量和接口契约。

完整时序/内存例子见 [模块导读](../../02_项目导读/02_模块与数据流.md)。

工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。

[返回工作区首页](../../README.md)
