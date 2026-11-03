# 历史实现 · 哪个结果可引用

| 阶段 | 路径或材料 | 状态 |
|---|---|---|
| 初版分段累加 | 服务器个人 home 下 v3_trial_20261103_8f99ca2431b4；本地 results/first_mapping | 功能通过，SS 9 条、FF 8 条电气违例，不能作为 200 MHz 通过结果 |
| 关闭无接收者的 busy 后，直接映射 | v3_trial_20261103_07384bb8170d 的 repaired 与 resize 前报告 | 八条空载违例消失；SS 仍有四条约 39 ps 的建立违例及一处最大电容违例 |
| 最终五单元修复 | 同一试验的 resize_4a17da389159cc41；正式工程 implementation/qualified200 | SS/FF 零报告违例，完整核心 200 MHz 通过 |

旧试验目录保留原取证路径。日常从 `v3/` 运行；除非追查某个失败或复核原始路径，无需进入旧目录。[初版摘要](../results/first_mapping/ppa.json) · [正式鉴定](../results/ppa.json)
