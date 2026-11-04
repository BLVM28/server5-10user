# 四路流数据组

每个子目录包含 12 层，每层 x/w/b/acc/y/wire/decoded/groups 八个文件，另有 matrix_sat/params/reads/writes 四个逐层文件，合计每组 100 个 hex。

- x/w：外部物理槽，分别 4,096/16,384 个 32 位字。
- b：256 个 32 位偏置；acc：25,344 个 40 位独立累加金值。
- y：Rice 输出量化之前的 int16；decoded：最终解码后用于精度对照的 int16，均两元素/字。
- wire：16,384 字输出窗口，未用字保持 0x5a5aa5a5，不能全部覆盖。
- groups：64 个输出子流实际写字数；reads/writes 是真实事务计数预期，不是预留槽大小。
