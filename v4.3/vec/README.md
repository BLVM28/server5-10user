# 向量

`streams/` 是本版唯一格式；1,400 个 hex 由固定原始 v2 输入生成，不是从待测 RTL 反向生成。各文件哈希在 ../py/stream_manifest.json，分发包为 ../packages/vectors.zip，散装 hex 不重复提交到 Git。可执行 `make vectors` 或 scalar_vectors.py 校验/补齐。

base 是旧确定性合成输入；class_00–class_11 是实际语音各类代表的逐层中间矩阵；worst 是原版选出的较难语音输入，名称不代表已经穷尽所有最坏情况。每组都是 12 个不同 Dense1 任务。base 的高熵压力成绩必须与语音成绩分开看。
