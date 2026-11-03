# 服务器 EDA 脚本

[daily.py](daily.py) 负责 VCS 功能、成对计时、波形、日常 STA 与报告。它复用 v2 经 SHA 核对的工具启动和私有库配置，选择本版本 rtl.f、TB、网表与输出目录。原始模式和紧凑模式均从物理总线写回检查，按真实写数记录。

[qualify.py](qualify.py)、manual_synth.tcl 和 mapping_period.txt 负责完整加速器综合和双角资格检查。reset_repair*.tcl 为综合阶段的复位 RDN/SDN 路径留保持余量，正式 STA 在 [constraints.tcl](constraints.tcl) 的原始约束下运行。resize_plan.txt 和 check_resize.py 仅对本轮真实映射做精确实例审计。snapshot.py 记录并核验网表、源与工艺报告的身份。

[gate_sample.py](gate_sample.py) 对完整映射的紧凑第 0 层做两角 SDF 仿真。[evidence.py](evidence.py) 校验硅前工艺数据、35 组 VCS、真实写字数、成对 NICE 测量、波形和实际门级层记录。[完整命令](../SERVER_GUIDE.md)
