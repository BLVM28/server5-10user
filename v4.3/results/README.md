# 公开结果

本目录保存可复查的 JSON，不包含工艺模型、映射网表或音频。完整解读见 [RESULTS.md](../RESULTS.md)。

| 文件 | 数据来源与解释 |
|---|---|
| functional.json | 本地 XSim 的公共 E203 SRAM 控制器全 12 层、29 场景和 25 保护；列出周期/事务/源码哈希 |
| workloads.json | 服务器 VCS 的 14 组输入，两种延迟条件；逐层和整组吞吐 |
| extra.json | 零延迟应答及真实公共控制器的服务器逐层证据 |
| paired_v42.json | 上一版在完全相同公共端点下的 12 冷任务参照 |
| ppa.json | 当前完整网表的面积、真实 SRAM 数量、两角频率扫点、源码和网表身份 |
| gate.json | 完整矩阵的门级 SDF、零注释违例、实际活动窗口和哈希 |
| power_summary.json | 明确单位后的mW、名义活动窗口、每任务μJ及相对变化 |
| power.json | 平均功耗工具原始数字、单位、活动覆盖和明确的加速器范围 |
| accuracy.json | 本轮重新执行 600 样本的浮点 Dense1 对照结果 |
| accuracy_provenance.json、accuracy_cases.json | 验证样本清单、逐样本 12 层误差；550 个不同 WAV 加 50 次同一零静音 |
| accuracy_audit.json | 冻结数学/参数与本版真实接口测试如何构成精度证据 |
| metric_fix.json | 本次NRMSE边界修正、13项解析测试、600样本重测与RTL未变证据 |
| driver.json、rv32.json | 336 组软件帧+12 组实际 RTL 输出的 C 对照，RV32 目标指令检查 |
| conformance.json | 独立点积边界测试和 wrapper 结构检查等补充证据 |

NRMSE 0.001418 是比值，即 0.1418%；不能误读成 0.001418%。吞吐用任务总数除以总时间，不把各层 tasks/s 作算术平均。功耗乘以实际活动时间才是能量，功率和能量不能混为同一指标。
