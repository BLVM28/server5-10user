# 指定 checkpoint 的第一 Dense 参数

`layer00.npz` … `layer11.npz` 每个对应一个编码器的第一 Dense：w(64,256)、b(256)，同时保存浮点原值与定点编码。`format.json` 保存源 checkpoint SHA、参数名、饱和计数和幅值范围。

W 为 signed16/F16，b 为 signed32/F27。不是 Q/K/V 参数，也不是 Dense2。由 export_weights.py 精确命名导出；capture_activations.py 会与 TensorFlow 原层参数逐元素核对。layer 编号仅标识来源，硬件不会读本目录文件。

工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。

[返回工作区首页](../../../README.md)
