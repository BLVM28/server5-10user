# 软件数值模型与参数转换

任务 1、2 的数值参考使用 `rice.py` 的 `math_layer` 和 `streams43.py`。`profile42.json` 冻结 12 层的 `sx/sw/sy` 与 Y Rice 参数。`numeric_model.py` 提供浮点转定点和独立舍入参考，`precision_metrics.py` 实现赛题 NRMSE。码流约定见 [接口与数据格式](../interface/README.md)。

## 权重和偏置

`export_weights.py` 沿用已核验的上游 checkpoint 导出脚本。它先核对 `best_weights.index` 和数据分片 SHA256，再按明确的层与变量名读取 12 层 Dense1 `kernel`、`bias`，输出各层 `layerNN.npz`。其中 `w` 是 W16/F16，`b` 是 bias32/F27，`w_float` 和 `b_float` 用于精度复核。需要 NumPy 和 TensorFlow checkpoint API，或原项目已验证的 `--reader-deps` 可选环境。

从 `final/` 在完整克隆库内运行。`--checkpoint` 接收不带扩展名的前缀。

```bash
python3 -B model/export_weights.py \
  --checkpoint ../01_核心参考/keyword-transformer-master/models_data_v2_12_labels/kwt1/best_weights \
  --output build/weights
```

## 生成 RTL 输入与软件对照

给定指定模型在对应层提取的 `X(99,64)` 浮点 `.npy`，下面命令产生 X/W/bias 的 32 位 hex 与描述符所需的层号、格式和缩放字段。已经定点化的 `X16/F11` 数组使用 `--x-kind integer`。输出目录由命令新建。

```bash
python3 -B model/prepare_layer.py inputs --layer 0 --x /path/to/layer00_x.npy \
  --parameters build/weights/layer00.npz --out build/layer00_inputs
python3 -B model/prepare_layer.py reference --layer 0 --x /path/to/layer00_x.npy \
  --parameters build/weights/layer00.npz --out build/layer00_reference
python3 -B model/verify_frozen.py
```

`inputs` 只进行量化和 X/W 编码，并写出偏置。`reference` 为独立软件对照生成 40 位累加、舍入后的 Y、写回码流及解码矩阵，供测试平台或离线比较使用。正式运行由驱动分配共享 SRAM 地址，构造描述符，发 NICE 指令并读取 RTL 写回。`verify_frozen.py` 从 36 个定点原文件重建全套 100 个验证 hex，并检查仅输入转换的字节一致性。

## 精度复核

`qualify_speech.py` 需要指定提交的 KWT-1 模型、兼容的 TensorFlow 2.4 环境与 Speech Commands V2 验证划分。`--model-repo` 指定上游目录，`--weights-dir` 指向上方导出的权重。默认沿用完整克隆库的上游目录和 `v2/vec/weights/`。脚本读取数据根目录的 `validation_list.txt`、`testing_list.txt` 与 `validation/` 下的 WAV。

```bash
python3 -B model/qualify_speech.py --data /path/to/speech_commands_v0.02 \
  --weights-dir build/weights --out build/validation_accuracy
```

精度入口保留旧脚本的抽样、权重核对与数学，仅调整路径参数以适应 `final/`。历史 600 样本报告的来源和本次复测范围见 [精度报告](../reports/03_数值精度.md)。
