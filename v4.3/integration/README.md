# E203 接口、格式与软件

## 硬件对接

`e203_subsys_nice_core.v` 是公共 demo NICE 核的替代 wrapper，不能同时编译原 demo 同名模块。它连接全部 NICE 请求/响应、active、mem_holdup 和 ICB 端口，没有引入额外总线。配置需 E203_XLEN=E203_ADDR_SIZE=32，`E203_HAS_NICE` 开启。`KWT_MEM_BASE/KWT_MEM_BYTES` 必须设置为正式分配的共享 RAM 窗口；默认 0 字节有意拒绝访问。

长指令为 custom3 opcode 0x7b、funct7=0x40、funct3=110、rs2=x0。rs1 为 4 字节对齐的描述符指针，rd 返回 32 位状态。C 驱动用 memory clobber 和 fence 保持顺序。窗口需无缓存或按正式系统协议做一致性处理。命令期间 `nice_mem_holdup` 有效，结果在最后一笔输出写应答之后才有效并保持到 `nice_rsp_ready`。

32 位 ICB 单在途，cmd_size=2 表示 4 字节。旧请求应答被消费时可以接下一笔，响应被内部暂存时不偷发命令。实际 E203 LSU 的单在途设置与之匹配；不能把握手交接称作多在途 DMA。公共控制器及其来源见 [upstream](upstream/README.md)。

## 描述符与地址

| 32 位字 | 字段 | 值 |
|---:|---|---|
| 0 | magic | 0x3154574b |
| 1 | format | **0x00010004**，不兼容 v4.2 的线格式 |
| 2 | layer | 0–11 |
| 3 | X 指针 | 预留 16 KiB |
| 4 | W 指针 | 预留 64 KiB |
| 5 | bias 指针 | 256×32 bit，共 1 KiB |
| 6 | Y 指针 | 预留 64 KiB |
| 7 | sx/sw/sy | 分别占 [3:0]/[7:4]/[11:8]，高 20 位为零 |

所有区域及 32 B 描述符须在共享窗口内、4 字节对齐、互不重叠且无地址溢出。sx=1–5、sw=3–5、sy=0–5；正式运行使用冻结 `kwt_v42_profiles[layer]`。W_BANK_AW 仅旧 wrapper 兼容，不改变 v4.3 固定的 128 字组织。

测试分配：BASE=0x10000000，描述符 BASE+0x200，X BASE+0x1000，W BASE+0x5000，b BASE+0x16000，Y BASE+0x18000；整个窗口 512 KiB。该地址是测试假设，不能作为比赛平台地址已核准的证据。

返回：0 成功；1 范围/重叠/码流错误；2 输入 DMA 失败；3 输出 DMA 失败；4 层号错误；0x10 指令错误；0x11 描述符地址错误；0x12 描述符格式错误；0x13 描述符读取失败；0xff 内部状态错误。失败后 Y 可能只写了一部分，调用者不能当有效矩阵消费。

## 四路槽布局

所有数据字的规范表示采用低半字在前；`PACK_LOW_FIRST=0` 为每字高低 16 位交换，C 编解码必须同设。Rice 位流在规范字内从 LSB 起排列；word length 表示 payload 字数，不包含头。

- **X**：4 个 1,024 字槽。子流 s 的输入为行 s、s+4…，每列 25 个值，行 99 以零补齐且不参与输出。字 0 是 payload 长度，字 1–8 是 64 个 4-bit Rice k；payload 按列 c=0…63，再按子流行 r=0…24。每列首值相对零，后续用同列前值预测。最后 padding 行的编码参与长度检查。
- **W**：16 列一组，共 16 组，每组 4 子流，每槽 256 字。子流 s 的四列为 16g+s+4j，j=0…3。字 0 为 payload 长度，字 1 的低 16 位存四个 W k，高 16 位存对应四个 Y k；payload 为 k=0…63、再 j=0…3 的绝对权重。
- **bias**：原有 256 个 32 位字，每列一个，按当前组读取 16 个。
- **Y**：同样 16 组×4 子流×256 字。字 0 仅低 16 位四个 Y k，高 16 位必须零；其后按有效行 0…98、再四列 j 输出差分 Rice。每列首值相对零。没有额外长度字，消费者恰好解码 396 个符号；实际写字数由内容决定，剩余槽保持原值。

bounded Rice 的 zigzag 差分为非负 z。若 z>>k<4，用 unary 1、结束 0、k 位余数；否则四个 1 后带宽为 16-shift 的绝对量化数。最多 20-shift 位/符号，最后字高位必须零。量化/舍入规则沿用 profile42，传输分流不改变最终数值。

## 软件文件及使用步骤

`kwt_v43_streams.h` 提供本版 descriptor、X/W 编码和 Y 解码；`kwt_v42_profile.h` 是逐字冻结参数，名称保留便于确认未再降精度；旧头文件只为公共类型和 Rice 基础函数依赖，不代表 v4.3 接受旧格式。示例入口为 `streams_rv32_probe.c`。

1. 由完整模型取得当前层 X，量化到原始 Q4.11；W/bias 来自同一 checkpoint 对应层。
2. 对 X 调 `kwt_encode_streams_x`，对 W 调 `kwt_encode_streams_w`。只读 W 可预处理；动态 X 的编码成本若在 CPU 上执行，正式整机吞吐必须计入。
3. 将帧和 bias 放入获准窗口，使用 `kwt_make_streams_descriptor` 构造描述符，再 `kwt_run` 发长指令。
4. 检查状态为 0；`kwt_decode_streams_y` 得到 99×256 的 Q4.11 int16，以 2048 缩放可和浮点参考比较。
5. 在完整 KWT 中继续后续层运算；最终分类头才会产生 yes/no 等标签。

主机 C 对照：336 个两字序软件帧和 12 个实际 RTL 输出均通过。RV32IMAC 已交叉编译并检查真实 custom3 字段；这仍不是 CPU 实机固件运行证明。

```powershell
python -B v4.3/py/audit_driver.py --cc D:/Dev-C++/Dev-Cpp/MinGW64/bin/gcc.exe
python -B v4.3/py/rv32_verify.py D:/xpack/xpack-riscv-none-elf-gcc-15.2.0-1-win32-x64/xpack-riscv-none-elf-gcc-15.2.0-1/bin/riscv-none-elf-
```

## 还缺什么平台信息

公共源码证明接口和一拍控制器行为，但其中顶层的共享 sysmem 是读零占位实现。需队伍确认正式 512 KiB RAM 的物理宏/银行与仲裁、地址译码、CPU 调度固件，以及输入编码/搬运计时口径。只有这些落地，才能将当前“加速器条件吞吐”升格为正式 E203 整机吞吐。本版也未计入 CPU、共享 RAM 和物理时钟树功耗。
