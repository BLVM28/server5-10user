# 验证证据 · 从结论追溯到日志

| 材料 | 能回答的问题 |
|---|---|
| [ppa.json](ppa.json) | 最终整核的面积、宏面积、4 个周期×2 个角的 setup/hold、报告违例数和服务器记录身份 |
| [functional.json](functional.json) | 最终七组基础结果、worst 结果、10 个 RTL 哈希、v2/v3 同一 12 层的周期差 |
| [xsim_base](xsim_base/README.md) | 本地基础自检每个 TB 的原始完成标记和输入指纹 |
| [xsim_worst](xsim_worst/README.md) | 真实语音产生的较大误差激活在 v3 上的逐层核验 |
| [first_mapping](first_mapping/README.md) | 初版功能正确却有电气违例的原因，供追溯 |

判断频率读 setup、hold 和电气约束的组合；判断吞吐读同工作负载周期及可用主频。v3 在 200 MHz 的增益与比赛统一 150 MHz 下的周期代价要分别理解。[实测报告](../RESULTS.md) · [正式目录验收](../SERVER_RESULTS.md)
