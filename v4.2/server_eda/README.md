# 服务器 EDA

`daily.py` 提供手工编译、RTL 功能、吞吐、波形和常用时序目标。`qualify.py` 对完整 `kwt_nice_core` 映射；`manual_sta.tcl` 对同一网表分别做 SS/FF STA，保存建立/保持、全违例、时序覆盖和 SRAM 宏计数。`prune.py` 对 PT 报出的零负载 min-cap 点进行电气扇出检查；DC 只删除无使用者的单元，Formality 证明清理前后完整网表等价。`snapshot.py` 将通过的实现、证明与脚本哈希关联起来。`gate_sample.py` 在 150 MHz 以两份 SDF 各跑一次完整新格式矩阵。`evidence.py` 从当前日志、网表和输入哈希复核公开结果。

入口是 [服务器指南](../SERVER_GUIDE.md)。`make -C server_eda` 和版本根的 make 进入同一版本。脚本引用个人目录的 v2 工具启动器与公共工艺库；映射、日志和波形均在 v4.2 内生成。
