# 软件数值模型与参数转换

本目录为本候选唯一活动软件参考。`rice.py::math_layer` 与 r8 相同；X/W 编码继续复用 `streams43.py`，但 `frame` 的 Y 为完整行优先 signed16/F11。`profile42.json` 的 sx/sw/sy 不改，历史 y_k 仅为输入头兼容保留，不再影响输出。

| 文件 | 功能 |
|---|---|
| `numeric_model.py`、`rice.py` | 量化、舍入、饱和、整数矩阵运算；后者的历史 `memory()` 不是当前布局，当前统一通过 `streams43.frame` |
| `streams43.py` | 只转换输入的 `input_words`；独立计算参考的 `frame`；格式 0x10005 |
| `export_weights.py` | 校验指定 best_weights 两个文件 SHA256，按明确变量名导出 12 层 W/b；`numeric_format_id` 不等于描述符格式号 |
| `prepare_layer.py` | `inputs` 只产生 X/W/b，**不计算矩阵答案**；`reference` 另产生黄金累加和/数值/实际写回文件 |
| `read_output.py` | 从硬件实际写回的 12,672 个 hex 字读取完整矩阵，输出浮点 `.npy` |
| `verify_frozen.py` | 36 个原始输入重建并检查 100 个固定向量；先验校验值固定 |
| `rebuild_vectors.py` | 本次格式变更的可复现生成器；断言 72 个原输入/数值结果文件与原 r8 SHA 一致，输出 wire 必须等于原 decoded |
| `precision_metrics.py` | 分层汇总平方误差/参考能量/元素数；NRMSE 的参考 RMS 下限 1e-8 |
| `qualify_speech.py` | 自选验证集的软件精度回放；显式指定仓库和权重目录，支持原始数据根或旧 validation 子目录；通过门槛纠正为 3% |

## 对已提取浮点层输入的可运行入口

以下路径都相对于本包根目录，尖括号内容需换为实际路径：

```bash
python3 model/export_weights.py --checkpoint <指定kwt1/best_weights前缀> --output build/weights
python3 model/prepare_layer.py inputs --layer 0 --x <99x64浮点X.npy> --parameters build/weights/layer00.npz --out build/input00
python3 model/prepare_layer.py reference --layer 0 --x <同一个X.npy> --parameters build/weights/layer00.npz --out build/ref00
python3 model/read_output.py --hex <实际Y的12672行十六进制字文件> --out build/actual_Y.npy
python3 model/verify_frozen.py
```

`inputs/reference --out` 必须是不存在的新目录；整数输入使用 `--x-kind integer`。reference 中 `wire.hex` 与 `decoded.hex` 内容相同，都是完整矩阵；`y.hex` 是 sy 舍入前的中间结果，**不能误作最终比较对象**。

基本转换依赖 NumPy；checkpoint 导出默认依赖 TensorFlow checkpoint API，或显式 `--reader-deps` 指定已有兼容 reader；音频回放依赖指定上游 KWT-1 237e4097 和兼容 TensorFlow 2.4/TensorFlow Addons 的环境。

```bash
python3 model/qualify_speech.py --data <SpeechCommandsV2根> --model-repo <ARM指定提交根> --weights-dir build/weights --out build/self_validation
```

**尚缺通用正式样本入口**：qualify_speech 仍按自选验证清单抽样，未接受评委指定 WAV/12 任务清单并连到硬件运行。prepare_layer 仍要求外部已提取的逐层 X.npy。已有捕获实现可复用，但本轮未虚构一个未经端到端验证的正式入口。正式清单未公布不妨碍现在补通用适配器；这项应由任务1/2的软件适配人员与任务3联调人员共同完成。
