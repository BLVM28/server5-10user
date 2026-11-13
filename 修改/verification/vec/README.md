# 固定回归数据

`raw/` 保留原 r8 的36个X/W/b文件；`worst/` 为12层各8个文件加4个公共计数/参数文件，总100个。目录名称 worst 仅表示原数据组名称，不证明覆盖所有最差输入。

本次只有各层 wire/groups 以及公共 writes 的布局/计数发生变化；原 X/W/b、40位acc、sy前y、最终decoded、sat/reads/params保持原值。`manifest.json` 固定当前向量校验值。再生成需 `model/rebuild_vectors.py`；常规验收只运行 `verify_frozen.py`。
