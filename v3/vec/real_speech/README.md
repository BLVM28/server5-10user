# 真实语音导出的 Dense1 激活

每个 class 目录代表一个类别的样例，用固定模型导出其 12 层各自的中间输入。worst 的各层可能来自不同样本。`make regress` 遍历这 13 组；需要快速复测较大误差输入时，直接用系统 TB 选择 worst。此前 v3 已在 worst 上得到 29/29；其它类别是否运行应以相应日志为准。

| 目录 | 类别 |
|---|---|
| [class_00](class_00/README.md) | `_silence_` |
| [class_01](class_01/README.md) | `_unknown_` |
| [class_02](class_02/README.md) | `yes` |
| [class_03](class_03/README.md) | `no` |
| [class_04](class_04/README.md) | `up` |
| [class_05](class_05/README.md) | `down` |
| [class_06](class_06/README.md) | `left` |
| [class_07](class_07/README.md) | `right` |
| [class_08](class_08/README.md) | `on` |
| [class_09](class_09/README.md) | `off` |
| [class_10](class_10/README.md) | `stop` |
| [class_11](class_11/README.md) | `go` |
| [worst](worst/README.md) | 逐层较大误差代表 |
