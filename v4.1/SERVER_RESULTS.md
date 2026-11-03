# 5 号服务器实测记录

正式目录的 `make check`、`make paired`、`make acceptance` 均已实际通过。最后一项打印 `EXTENDED ACCEPT PASS`，重新核验了 50 套回归、两个完整 SDF 矩阵、7,200 项浮点误差和更高频点的同网表记录。

个人目录 `/storage2/2026contest/server5/s5_10usr/v4.1`。VCS 使用服务器真实 SRAM 功能模型。DC/PT 使用同一套 SMIC40 工艺库。正式网表、SDF 和原始报告保存在个人目录中。不同格式共用完整网表。

50/50 套 VCS 回归通过，14 个输入组实际逐层 NICE 周期与 XSim 一致。最终网表 SHA-256 为 `be5d3632f30685ad612099c5896ca56d1d27f4448430c03f7733233240437d36`。150/170/180/185/190/200/205 MHz 双角零报告违例，210 MHz 慢角失败。1,500 tasks/s 目标按独立的 150 MHz 成绩验收。[八点记录](results/ppa.json)

| 工具 / 位置 | 记录的内容 |
|---|---|
| VCS · reports/regress.log | 11 个基础套件，再对 class_00…class_11 和 worst 逐组运行原始、无损和 Block8 三种输出，共 50 套。系统 TB 比较全部 acc40、按格式解析的 Y、物理写数和错误恢复 |
| VCS · reports/immediate.log、reports/modes.log | 同拍 ICB 下旧模式和 Block8 完整矩阵，另在同一实例无复位切换原始、坏 Block8 头、无损、有效 Block8、原始 |
| PT / DC · reports/mapping.log | 完整三模式加速器，以慢角映射，再分别做慢快角 STA，保留负余量及全部报告的电气约束 |
| VCS + SDF · reports/gate.log | 两角各用实际 SDF 检查 worst 第 0 层 Block8 完整矩阵。探针要求零注释错误/警告，运行比较 6,752 个写字和全部解码输出 |
| 正式发布 · reports/release.log | `make report`、`make acceptance`、发布源哈希、成对计时与冻结工艺身份 |

`make report` 用当前 RTL、TB、向量、运行日志和网表身份检查基础结果。`make paired` 重跑三种格式并打印 150 MHz 下的吞吐。`make acceptance` 交叉核验已保留的扩展记录。软件浮点评估与 RV32 驱动证据另见[精度及性能报告](RESULTS.md)。如果真实共享 RAM 等待条件不同，应重新实测完整 E203。

150 MHz 回标实测的两角均打印 `BLOCK8 GATE PASS`，SS 最大延迟和 FF 最小延迟各 6,752 写、12,827 笔事务。注释探针各 0 错误、0 警告，完整矩阵在引脚解码后全部 25,344 个值匹配。发布时的原始 SDF、运行日志与注释摘要留在 `reports/published_gate_150.zip`。再跑 gate_sample 会产生含新日期的日志和 SDF；验收按当次文件校验哈希，并与发布时的同一网表和结果计数比较。[原始身份](results/gate.json)
