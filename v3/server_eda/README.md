# EDA 流程 · 仿真、映射与验收

版本根 Makefile 是统一入口，本目录的 [Makefile](Makefile) 将同名命令转回上级。日常使用见 [服务器手册](../SERVER_GUIDE.md)。

| 文件 | 职责和复用关系 |
|---|---|
| [daily.py](daily.py) | 运行七个 VCS 自检、波形、冻结网表 STA 和状态报告。对同一版本加互斥锁，以免 clean 与仿真/时序同时写文件 |
| [qualify.py](qualify.py) | 按 5 ns 从 v3 源码映射完整 kwt_nice_core，按源码/Tcl 指纹复用有效构建；构建与日常 timing 共用相同的双角测量函数。复用经 SHA 固定的 v2 工具启动器和 shared 库配置 |
| [manual_synth.tcl](manual_synth.tcl)、[constraints.tcl](constraints.tcl) | DC 读 10 个 RTL、标准单元与 SRAM 库；测试内存参数显式给定。约束沿用 v2 的时钟不确定度、I/O 延迟和负载 |
| [reset_repair_run.tcl](reset_repair_run.tcl)、[reset_repair.tcl](reset_repair.tcl) | 从已映射 DDC 做通用复位短路径修复，优化用的额外要求在最终 STA 前移除 |
| [resize_plan.txt](resize_plan.txt)、[resize.tcl](resize.tcl) | v3 专属的 5 个映射改单元，分别改善 1 条负载及 4 条慢角建立路径；核对实例原类型、引脚、布尔函数和驱动条件 |
| [check_resize.py](check_resize.py) | 比较修复前后结构网表，逐模块核对更换清单以外的语句一致 |
| [manual_sta.tcl](manual_sta.tcl) | PT 对 SS/FF 独立读取相同网表，重新建立约束，输出 setup/hold、违规、覆盖、宏数量和 SDF |
| [snapshot.py](snapshot.py) | 核对源文件、网表、鉴定记录和结构证明，将服务器私有映射导入 qualified200 或 rebuilt |
| [wave_dump.sv](wave_dump.sv)、[tb_core_all_gate.sv](tb_core_all_gate.sv) | 限窗口采集顶层波形，以及按层运行完整矩阵的可选门级测试，沿用 v2 的接口检查 |

默认 200 MHz 检查完整 NICE 核，含八个点积和十五个实际 SRAM 宏。SS 为 0.99 V/125°C，FF 为 1.21 V/−40°C。时钟不确定度 0.100 ns，输入/输出延迟 max/min 1.000/0.100 ns，输入转换 0.100 ns，输出负载 0.002852 pF。报告不施加 false path、multicycle 或 reset 豁免。

独立重现 v3 频率研究可执行 `python3 -u server_eda/qualify.py --periods 5.0 5.555556 6.25 6.666667`。`--before-resize` 保留直接映射的对照。完整试验结果在 build/ppa 下按源码与修复指纹区分；日常命令只在 build/manual 内更新运行记录。`make check` 的 SS/FF 时序来自新的 PT 运行。
