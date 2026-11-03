# RTL 模块导航

| 层级 | 模块 | 职责 |
|---|---|---|
| 指令端 | `kwt_nice_core`、`kwt_icb_master` | E203 NICE 握手，8 字描述符，异常状态与 ICB 命令保持、响应暂存。 |
| 调度 | `kwt_linear_core`、`kwt_tile_dma` | 分离当前计算页与预取/写回页，选择四种数据格式，统计饱和数与 core 周期。 |
| 新格式读 | `kwt_rice_reader`、`kwt_rice_unpack` | 读 X/W 元数据及偏置，维护四字 FIFO、跨字位游标、预测状态；长度或填充错误返回错误。 |
| 新格式写 | `kwt_rice_writer`、`kwt_rice_pack` | 读取本组 Y 的 Rice 参数，逐行量化、预测并编码，最后一个部分字补零，等待 ICB 写应答。 |
| 计算 | `kwt_tile_compute`、`kwt_stream_dot`、`kwt_mul16_pipe`、`kwt_quantize` | 默认四行八列，每点积累加 64 项；40 位末端进位独立折叠，最近偶数舍入、饱和。 |
| 存储 | `kwt_sp_ram`、`kwt_x_buffer`、`kwt_w_panel`、`kwt_result_pages` | X 四行并读，W/Y 双页并行访问。仿真 SRAM 模型和综合宏引用分开。 |
| 兼容 | `kwt_legacy_dma`、`kwt_row_pack`、三个 `kwt_block8_*` 模块 | 支持旧 int16、无损行差分和 Block8 描述符。 |
| 算术对照 | `kwt_dot64`、`kwt_mac8` | 保留独立算术接口/基线测试；默认四行数据通路实例化 `kwt_stream_dot`。 |

[编译顺序](../rtl.f) 给出 23 个源文件。[模块关系](../ARCHITECTURE.md) 和 [描述符](../integration/README.md) 分别说明周期与软件布局。
