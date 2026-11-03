# 软件与生成流程

[block8.py](block8.py) 计算每块指数、八位尾数、新的精确整数乘法和最终输出。[make_fast_vectors.py](make_fast_vectors.py) 在有 NumPy 的本地重建 14 套向量。[scalar_vectors.py](scalar_vectors.py) 用 Python 标准库独立实现标量点积、舍入和编码，5 号服务器日常使用它。每个输出文件逐个比对冻结 SHA，发现手工更改即报错。[fast_manifest.json](fast_manifest.json) 固定 1,190 个新向量，[vector_manifest.json](vector_manifest.json) 固定 v2 的 952 个原件。

[qualify_speech.py](qualify_speech.py) 在原 TensorFlow 2.4 模型的 600 个本地验证样本上截取 12 个 Dense1，校验 checkpoint 并比较浮点参考。运行命令见 [history](../history/README.md)。[audit_driver.py](audit_driver.py) 编译 C 编码和解码器，读回真实 ICB 内存。[local_evidence.py](local_evidence.py) 将 XSim 源签名、成对周期和 550 个不同 WAV 的身份一起核验。原数值金模与参数转换分别保留在 [numeric_model.py](numeric_model.py)、[export_weights.py](export_weights.py)。[assets.py](assets.py) 构建分类包，[delivery.py](delivery.py) 固定和比较发布文件。
