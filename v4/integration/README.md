# E203 软件接口与无损输出布局

指令编码、rs1 描述符地址和 32 位 NICE/ICB 引脚沿用 v3.1。[kwt_driver.h](kwt_driver.h) 构造原格式描述符。[kwt_v4_output.h](kwt_v4_output.h) 提供紧凑描述符构造和独立 C 解码器。集成宏、指令冲突、正式共享 RAM 与固件时钟需由 SoC 确认。默认 MEM_BYTES=0 会拒绝任务，TB 的 0x10000000 不是正式平台地址。[E203 包装](e203_subsys_nice_core.v)

| 描述符 format | 输出空间 | 使用方式 |
|---|---:|---|
| 0x00010000 | 50,688 B | 行主序，连续 12,672 个 32 位字，每字两个 int16。原应用无需换格式 |
| 0x00010001 | 51,584 B | 前 12,672 字为固定容量载荷槽，末尾 224 字为标签。分配整块空间并在 NICE 成功后解码，目标仍为 25,344 个 int16 |

对 row=r、列组 g，载荷起始字为 `128*r+4*g`。标签字为 `12672+7*g+r/16`，其中第 `2*(r%16)` 起的两位表示模式。模式 0/1/2 分别用 4/8/12 位有符号差值，写 1/2/3 个 32 位字。模式 3 用 16 位绝对数，写 4 个字。lane 0 从最低位起排，跨 32 位边界时继续下一个字。每组的上一行初值为全零；绝对模式同样更新下次预测。最后标签未使用的高位为零。槽内未写的字无内容保证，消费者不得读取。PACK_LOW_FIRST=0 时每个物理字含标签统一交换两个 16 位半字。

```c
kwt_descriptor d = kwt_make_packed_descriptor(layer, x_addr, w_addr, b_addr, y_addr);
uint32_t status = kwt_run(&d);
if (status == KWT_OK)
    kwt_decode_packed((const uint32_t *)(uintptr_t)y_addr, KWT_PACKED_WORDS,
                      dense_y, KWT_M*KWT_N, 1);
```

实际固件应检查解码返回值，遵循平台的 trap、缓存维护及共享内存规定。src 和 dst 不重叠。输出编码在 RTL 内完成，C 解码只恢复最终 int16 数据，不代做点积、偏置和量化。如果下一模块要求稠密 Y，应纳入该模块真实消费成本。[主机解码探针](codec_probe.c) · [Python 参考](../py/codec.py)

使用 xPack GCC 15.2.0 已把原始和紧凑驱动用例编译为 RV32IMAC/ILP32 对象，并反汇编核对两条 custom3 指令。这个检查不包含 CPU 上电、执行或正式 RAM 绑定。[交叉编译记录](../results/driver.json)
