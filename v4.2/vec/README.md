# 验证数据

`precision/` 有 base、class_00…class_11、worst 共 14 组，每组 12 个独立 Dense1 任务。输入源固定在 [v2 向量](../../v2/vec/README.md)，每个 X/W/b 都先校验哈希。base 是合成压力数据；各 class 是真实语音代表输入；worst 是 v2 逐层选择的代表组，并非 v4.2 所有场景里最慢的数据。原始 hex 通过 [vectors.zip](../packages/vectors.zip) 或 `make vectors` 取得。
