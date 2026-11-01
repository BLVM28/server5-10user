# v2 固定数据与期望值

这些是回归基准，不能为消除 FAIL 手改。v1/v2 原有 159 个数据文件相同，整理仅增加 README。

| 路径/模式 | 数据含义 | 用法 |
|---|---|---|
| quant_acc/y/sat.hex | 单独量化的输入、舍入/饱和期望 | arithmetic TB |
| dot_x/w/b/acc/y/sat.hex | 64 项点积及完整精度/输出期望 | arithmetic TB |
| layer00…11_x/w/b/y/acc.hex | 十二套完整矩阵，x/w/y 每行 32 位装两个 int16，b32，acc40 | system/overlap TB；不是 12 个编码器完整推理 |
| matrix_sat.hex | 各层预期输出饱和计数 | 检查数值路径一致 |
| vectors.json | 生成配置/尺寸等元数据 | 核对生成身份 |
| [weights](weights/README.md) | checkpoint 第一 Dense 参数与转换记录 | 金模/导出一致性 |
| [activation_smoke](activation_smoke/README.md) | 静音/合成音调的原模型捕获 | 流程检查，不能替代真实验证集 |

低半字优先时，第一个元素放总线字 [15:0]。不要把十六进制字符串直接当 float；输出真实值为 signed int16 /2048。

工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。

[返回工作区首页](../../README.md)
