# 服务器 EDA 入口

[daily.py](daily.py) 实现根 Makefile 的编译、运行、50 套回归、同场计时与 STA 报告。[qualify.py](qualify.py) 在 SMIC40 标准单元与两类 SRAM 宏下映射当前 18 个 RTL 模块，包含原有和 Block8 格式。它校验 v2 工具启动器的 SHA，只复用工具配置和真实库路径，所有新网表在 v4.1 私有目录重建。复位保持修复只在综合优化时使用。PrimeTime 重新从 [constraints.tcl](constraints.tcl) 建立固定约束（0.1 ns 不确定度、1.0/0.1 ns I/O、0.002852 pF 负载）。

[gate_sample.py](gate_sample.py) 在独立目录测真实 SDF 两角。[immediate.py](immediate.py) 测立即返回，另有 [evidence.py](evidence.py) 将 VCS 记录、同网表时序、实际门级日志和数值报告交叉核对。[服务器手册](../SERVER_GUIDE.md)
