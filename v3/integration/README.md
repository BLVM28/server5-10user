# E203 接入 · CPU 如何调用矩阵加速器

这组接口文件从 v2 复用。v3 改动位于点积单元内部，外部指令、数据格式、NICE 和单笔 ICB 协议沿用已有契约。

| 文件 | 用途 |
|---|---|
| [e203_subsys_nice_core.v](e203_subsys_nice_core.v) | E203 同名 NICE 包装。使用真实配置头、32 位数据/地址和 E203_HAS_NICE，实例化 v3 的 kwt_nice_core |
| [kwt_driver.h](kwt_driver.h) | RV32 描述符、16 位数据打包、状态码及自定义长指令调用。编译/运行用平台的工具链和异常处理 |
| [driver_compile_probe.c](driver_compile_probe.c) | 编译驱动调用的最小样例，供检查汇编器和 ABI |
| [kwt_clock_template.sdc](kwt_clock_template.sdc) | 接入时核对时钟和顶层接口预算的模板；v3 本轮 STA 实际用 server_eda/constraints.tcl |
| [check_structure.tcl](check_structure.tcl)、[sram_blackboxes.sv](sram_blackboxes.sv) | Vivado 结构检查与黑盒 SRAM 声明，检查宏数量和锁存器；功能仿真和 ASIC 时序使用各自的真实模型 |

驱动把 magic、format、layer、X/W/b/Y 的字节地址和 reserved 写入 32 字节描述符，将指针放在 rs1。指令编码为 opcode=0x7b、funct7=0x40、funct3=6、rs2=x0。X/W/b/Y 分别占 12672/32768/1024/50688 字节，描述符和四个区须按字对齐、合法且互不重叠。最后的 Y 写应答结束后才返回状态。

正式接入要由平台确认 `KWT_MEM_BASE`、`KWT_MEM_BYTES` 和打包顺序。默认窗口为 0，会拒绝内存访问；`0x10000000` 仅用于现有 TB 的 512 KiB 测试窗口。使用 v3/rtl.f 编译加速器，SoC 中只选择一个同名包装。正式共享 RAM、启动/linker、固件和顶层任务计时仍需整机验证。
