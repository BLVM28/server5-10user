# 服务器工具流程

入口统一使用上一级 Makefile；本目录的 Makefile 只转发目标。脚本只在用户的 v4.3 范围内产生输出，公共工艺库仅读。

| 文件 | 职责 |
|---|---|
| daily.py | compile/run/regress/waves/verdi/paired/timing/report/clean 的参数、锁和 PASS 检查 |
| qualify.py | 冻结源码标识，复用已固定哈希的 v2 工具启动器/私有库选择，完整综合并扫两角 |
| manual_synth.tcl、mapping_period.txt | SS 5.2 ns 优化目标，真实局部 SRAM，建立/保持优化及完整面积 |
| constraints.tcl、manual_sta.tcl | 独立重建报告约束；输出建立/保持、全部违例、覆盖和 SDF |
| reset_repair*.tcl | 只在优化阶段处理复位短路径，报告时恢复正常约束 |
| prune.py、prune.tcl、prune_equiv.tcl | 从真实零负载违例定位死逻辑，删除后用 Formality 证明等价；不屏蔽违例 |
| resize*.tcl、resize_plan.txt、check_resize.py | 预留可审计的单元替换功能；本版默认计划为空 |
| snapshot.py | 校验源码/网表/等价证据/面积/150 MHz 两角后，安装 implementation/rebuilt |
| paired43.py | 公共 SRAM 控制器编译；同条件 v4.2 参照；完整任务的 SDF 仿真与 PX 功耗 |
| power.tcl | 从真实任务 VCD 读翻转活动，报告平均功耗、层次和覆盖；明确子系统范围 |
| evidence.py | 校验所有当前结果后生成公开摘要及 acceptance |
| public_frame.py | 只读导出允许的公开测量摘要；不是登录、传输凭证或工艺文件的工具 |

工具包括 VCS、DC、PrimeTime、Formality、Verdi。库选择来自既有 `../shared/library_selection.json`；映射网表、DB、SDF 和 VCD 留在服务器私有目录。脚本中的绝对路径是本账号的使用约束，其他账号迁移需先审查路径和库配置。
