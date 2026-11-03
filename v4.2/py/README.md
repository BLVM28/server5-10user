# 参考模型与复现

`select_training.py` 从本地 Speech Commands v0.02 归档选取 33 个训练 WAV。`capture_training.py` 用仓库 KWT-1 最佳 checkpoint 和上游预处理捕获 396 对训练层输入/输出。`calibrate.py` 在训练划分上选择步长和 Y 的 k，产物为 `profile42.json`。已冻结的参数供验证使用。[训练样本](../results/training_samples.json)

`rice.py` 是整数运算和位流的 NumPy 黄金模型。`qualify_speech.py` 在同一组 600 个验证输入上调用原浮点模型，分别比较每层。`make_rice_vectors.py` 从固定 v2 X/W/b 生成 14 套测试。服务器 `scalar_vectors.py` 只依赖 Python 标准库，使用独立的标量点积和编解码重新生成缺失字，并检查 1,400 个新向量、1,190 个旧格式文件及 952 个 v2 源文件的 SHA-256，已有文件内容不符会报错。

`profile_header.py` 导出 C 参数表。`audit_driver.py` 将 C 编码与黄金输入对照，使用实际 RTL RAM 验证解码。`rv32_verify.py` 检查指令字段。`run_xsim.py` 支持顶层、参数及向量路径。`local_evidence.py` 审核日志哈希、12 层周期、样本一致性和误差。`assets.py` 与 `delivery.py` 负责打包、清单及服务器受限安装。复现浮点测量时，从本地协作库根执行 `python -B v2/py/run_model_python.py v4.2/py/qualify_speech.py --data datasets/speech_commands_v0.02 --out v4.2/build/speech --per-class 50`。新克隆首次运行标量向量检查前，应先解开 v4.1 的 vectors.zip，或在 v4.1 中执行 make vectors，提供旧格式对照。`make_fast_vectors.py` 和 `block8.py` 对应历史布局。

[服务器命令](../SERVER_GUIDE.md)
