# 活动 RTL

编译从本包根目录使用 `-f rtl.f`。14 个模块，顶层 `kwt_nice_core`。硬件仍计算 `(99×64) × (64×256) + bias = 99×256`，每次一层，支持驱动连续选择 12 层输入和参数；不承担 GELU、第二线性层或 yes/no 分类。

| 模块 | 作用和连接 |
|---|---|
| `kwt_nice_core` | 自定义指令、8 字描述符、地址/格式校验；启动 core，最后写应答完成后返回状态。新格式必须是 `0x00010005` |
| `kwt43_icb_master` | 32 位、单笔在途 ICB，r8 命令/应答寄存原样保留；需接原 NICE→LSU/BIU→System Bus |
| `kwt43_core` | 输入加载、16 列组调度，W/Y 两页交替；计算与另一页传输重叠，Y 区仍保守预留 64 KiB |
| `kwt43_reader`、`kwt43_unpack` | 原四路 X/W 输入编码的解码与合法性检查，bias 直接读；未改数值或加载协议 |
| `kwt43_compute`、`kwt43_dot`、`kwt_mul16_pipe` | 8 行×16 列、128 路乘累加，归约 64 项，40 位分段累加和 r8 七级乘法保持不变 |
| `kwt_quantize` | 累加 F27→F11，最近偶数舍入、signed16 饱和 |
| `kwt43_xram/wram/yram`、`kwt_sp_ram` | 8 个 1024×16 和 64 个 128×16 宏，共 32 KiB；r8 下降沿请求寄存和宏驱动保留 |
| `kwt43_writer` | **重写**。每行读出当前列组的 16 个结果，保留 sy 数值舍入后恢复为完整 signed16/F11，每拍写两个元素。没有预测、Rice、输出头或压缩槽 |

Y 地址为 `Y_base + 2*(row*256 + col)`。列组 g 覆盖列 `16g..16g+15`，组内每行 8 个总线字，行间地址差 512 字节。每组 792 字，16 组共 12,672 字/50,688 字节。传输按列组进行，最终内存为普通行优先完整矩阵。其余 14,848 字节保留不写。

writer 在单笔应答之前不发下一笔；反压期间地址/数据稳定，写失败返回 3，最后应答后才 done；系统复位必须同时取消 CPU、NICE 和总线在途事务。输入旧元数据中的 Y Rice key、reader/core 的旧 key 连接为兼容保留，writer 不使用，综合可裁掉。旧 `kwt_rice_pack.sv` 已从本候选及编译表移除。

综合须定义 `KWT_USE_FOUNDRY_SRAM` 和 `SYNTHESIS` 并提供指定库，使用实际 `RAMSP1024X16/RAMSP128X16` 与 HVT buffer cells。`verification/tb/kwt_sram_sim.sv` 仅为功能模型。不要把 RTL 时钟周期设置当作 STA 结果。
