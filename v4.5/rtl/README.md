# 加速器 RTL

综合顺序见 [rtl.f](../rtl.f)。顶层 `kwt_nice_core` 解析描述符、校验地址和格式、协调计算并返回状态。System Bus 版本由 SoC 封装发出同一启动握手。

| 模块 | 职责 |
|---|---|
| `kwt43_icb_master`、`kwt44_fifo` | 将内部请求变为有序 ICB 命令与应答，分别缓存出入方向，v4.5 总额度为 8 |
| `kwt43_reader`、`kwt43_unpack` | 读取 X、W、b，按各自位流解码并将数据送往本地宏，按流记录读回复归属 |
| `kwt43_xram`、`kwt43_wram`、`kwt43_yram`、`kwt_sp_ram` | 本地输入、权重和结果缓冲，按物理宏的同步读写协议组织 |
| `kwt43_core`、`kwt43_compute` | 排程、tile 调度、连接 MAC 和数据搬运 |
| `kwt43_dot`、`kwt_mul16_pipe`、`kwt_quantize` | 有符号点积、流水乘法、舍入及饱和 |
| `kwt43_writer`、`kwt_rice_pack` | 将定点 Y 编成有界位流并写回，等待最后一笔写应答 |

本版加速器改动集中在 ICB 在途额度、读流标签深度和写应答计数。数值对照与独立核测试见 [tb](../tb/README.md)。
