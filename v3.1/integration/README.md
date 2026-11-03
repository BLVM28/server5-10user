# E203 集成 · v3.1 的接口边界

[e203_subsys_nice_core.v](e203_subsys_nice_core.v) 与 E203 官方配置头一起编译，保持 32 位 NICE/ICB 接口。用本版 [rtl.f](../rtl.f) 实例化完整加速器。页选择和乘法寄存级都在加速器内，描述符不需要包含页号或流水长度。

[kwt_driver.h](kwt_driver.h) 定义描述符和 custom3 指令，rs1 是描述符字节地址。X/W/b/Y 分别占 12672/32768/1024/50688 字节，任务期间保持输入稳定，成功应答后读 Y。若返回错误，部分 Y 不能作为完整输出。[driver_compile_probe.c](driver_compile_probe.c) 给出最小调用。KWT_MEM_BASE、KWT_MEM_BYTES、打包顺序及 CPU 的合法共享 RAM 需由平台落实。测试窗口 0x10000000 不可直接写入正式平台配置。

[check_structure.tcl](check_structure.tcl)、[sram_blackboxes.sv](sram_blackboxes.sv) 用于 FPGA 结构检查。[kwt_clock_template.sdc](kwt_clock_template.sdc) 供 SoC 对接时核对接口时钟。正式芯片库时序使用 server_eda/constraints.tcl。端到端固件、正式共享 RAM 和关键词分类准确率未由本版核级测试覆盖。
