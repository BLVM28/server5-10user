# 服务器流程 · VCS、DC、PrimeTime、Verdi

[Makefile](../Makefile) 是日常入口，本目录 Makefile 把命令转回版本根。daily.py 调用已核验 SHA 的 v2 工具启动代码，但使用 v3.1 的源、TB、网表和输出目录。复用的是工具配置及工艺文件路径。本版网表一律重新综合。

| 文件 | 职责 |
|---|---|
| daily.py | 编译和运行 VCS、核对七套期望、刷新带网表/向量哈希的报告、调用双角 timing、波形及 SDF 短测 |
| qualify.py、manual_synth.tcl、mapping_period.txt | 读取 rtl.f，从新的完整核心映射 DC 网表、修复复位保持路径。从 area.rpt 核对完整核心与 SRAM 面积 |
| constraints.tcl、manual_sta.tcl | 对相同网表独立施加原约束，报告 SS/FF setup、hold、电气违例、覆盖、宏计数和 SDF |
| reset_repair*.tcl | 在综合优化时给复位路径留保持余量，统计时恢复原约束。PT 独立重建约束 |
| resize_plan.txt、resize.tcl、check_resize.py | 仅执行本版新测得的单元调整，每个实例核对库引脚/函数和其余映射结构 |
| snapshot.py | 仅将通过面积及目标双角的实现装入本版 implementation/rebuilt，保持源指纹和映射文件哈希一致 |
| wave_dump.sv、tb_core_all_gate.sv | 分别生成接口波形、运行 SDF 注释探针或较长门级测试 |

操作和输出判据见[手动操作](../SERVER_GUIDE.md)。原始日志留在个人工作区。
