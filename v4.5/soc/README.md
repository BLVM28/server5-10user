# E203 集成与验证

| 目录 | 职责 |
|---|---|
| `rtl/` | E203 平台覆写文件、ROM 与 ITCM/DTCM 包装、三主 ICB 仲裁、共享 SRAM 与 System Bus 启动控制 |
| `firmware/` | RV32 ROM 后启动程序、内存和异常自检、矩阵描述符构造及任务调度。默认 `firmware.hex` 与 v4.4 r9 相同 |
| `tb/` | `tb_soc_boot` 检查真实 E203 启动和 12 个矩阵，`tb_soc_gate` 检查综合网表，另有 ITCM、共享 SRAM 和 CLINT 定向验证 |
| `flow/` | 校验官方输入、生成统一源计划、运行 VCS、执行 DC 约束和工艺角分析、运行原生 SDF 回标 |
| `work/` | 服务器生成的源码清单、临时构建目录、原始报告、网表及活动日志 |

顶层为 `kwt_e203_soc_top`。同一源计划生成 E203 定时器、时钟控制器、DTCM 控制器、取指和分支预测覆写文件。仿真与综合读取相同的 RTL，仿真额外编译测试平台和工艺模型。详见 [操作命令](../README.md) 和 [架构说明](../ARCHITECTURE.md)。

150 MHz 保持修整在已映射网表上完成。[扫描脚本](flow/scan_short_hold.tcl) 在 FF/CMIN 会话导出低于 20 ps 的数据端点。[插入脚本](flow/insert_hold_guard.tcl) 在恢复原约束的网表上读取端点表，检查插入前的建立裕量并加工艺反相器对。服务器 `v4.5/hold_guard/flow/` 保存当次实际 DC 入口，修整网表和复跑路径见 [验证报告](../REPORT.md)。
