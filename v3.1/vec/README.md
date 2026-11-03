# 向量 · 分清输入和期望输出

本目录保存运行副本。952 个数据文件在本地和服务器逐个校验，对应的 SHA 清单在 [py/vector_manifest.json](../py/vector_manifest.json)。仓库中的 v2 保存逐文件原件，v3.1 提供可直接解压的 vectors.zip 和恢复命令。新克隆可执行 `python v3.1/py/assets.py vectors`，在服务器 v3.1 根目录用 `make vectors`。

| 数据 | 由谁读取 | 含义 |
|---|---|---|
| quant_*.hex、dot_*.hex | arithmetic TB | 孤立量化和点积测试，覆盖舍入、饱和、偏置与极值 |
| layerNN_x/w/b.hex | system/overlap/negative TB | 输入与权重偏置；X/W/Y 两个 int16 打成一个 32 位字，默认低索引进低半字 |
| layerNN_y/acc.hex、matrix_sat.hex | TB 检查器 | 期望的 Y、40 位累加与饱和计数，只供比对 |
| [weights](weights/README.md) | 参数导出/金模 | 12 层 Dense1 的浮点及定点参数 |
| [activation_smoke](activation_smoke/README.md) | 模型链路调试 | 静音、合成音调的激活及一个导出样例 |
| [real_speech](real_speech/README.md) | 语音激活回归 | 12 类代表集及逐层较大误差集 worst |

单层 X 3168 字，W 8192 字，b 256 字，Y 12672 字，acc 25344 个。单个 RTL 任务的输入来自相应编码器层的第一处 LayerNorm，输出交给后续软件模型步骤。
