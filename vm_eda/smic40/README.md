> 2026-11-01 整理更新：本目录原有技术说明保留。最新完成度以工作区根 README 和 fix1 报告为准；本轮只整理本地资料，不自动同步新文档到 VM/服务器。
> [工作区首页](../../README.md) · [调试导读](../../02_项目导读/03_调试与E203接入.md)

# SMIC40 原工艺修复

此目录只包含自编流程，不包含公共工艺库或从赛用服务器下载的网表。必须在原授权服务器个人目录内运行，使用此前已经核对的 `library_selection.json`。

v1 采用此前同约束下的 `v1_reset` 结果：SS/FF 配对综合、hold 优化、复位路径真实延迟修复。最终 PrimeTime 从头建立 6.666667 ns 时钟、0.1 ns uncertainty、I/O max 1 ns/min 0.1 ns、0.002852 pF 输出负载，无 reset false path。

v2 以 `v2_reset` 的 DDC 为输入，执行 `cap_eco.tcl`：

- `master/U381`：INV2 → INV3，保持反相逻辑，修最大电容。
- `U1770`：BUFV2RD → BUFV3RD，保持缓冲逻辑，修最大电容。
- `core/mac/lane_4__dot/U8`、`core/mac/lane_5__dot/U15`、`.../U17`：DEL4V0 → DEL2V0，保持同相逻辑，平衡前三个复位到数据端点的最大/最小延迟。

所有完整单元名及输入 DDC 断言见 Tcl。新结果标签为 `v2_eco5`；`v2_eco2` 虽然电容通过，但新增 setup 违例，不能交付为通过版。`v1_drc`、`v2_drc` 的全局重映射试验也未采用。

最终检查必须包含 `make sta gate summary TAG=v2_eco5` 和 `python3 full_gate.py --tag v2_eco5`。运行器不能以 make 返回码代替 `timing_slack_met`、`reported_constraints_met`、SDF 回标统计和测试计数。

原始正式预算、CTS、布线寄生、OCV、复位集成仍待后续验证。这里的单元名只适用于已哈希记录的原网表，重新综合后不能盲目按名字套用 ECO。


工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。
