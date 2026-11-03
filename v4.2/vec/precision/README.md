# Precision42 的 14 套验证数据

每组 100 个文件。每层的 `x,w,b` 是物理输入，`acc` 是 40 位原始和，`y` 是首次 int16 量化，`decoded` 是从 Y 有线格式解码后的预期矩阵，`wire` 包括 32 个完整槽和未用字的哨兵，`groups` 是逐组有效字数。组级 `reads,writes,params,matrix_sat` 各含 12 项。所有 1,400 个文件的字节级哈希见 [清单](../../py/precision_manifest.json)。
