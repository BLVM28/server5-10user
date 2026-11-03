# Block8 向量结构

base 为合成压力集。12 个 class 目录各取一个类别代表样本。worst 是按历史浮点误差逐层选择的调试集。每套有 12 层，每层包含 x、w、b、acc、y、wire、decoded 七个文件，另有一份 12 项饱和计数，共 85 个文件。x/w/b 是实际输入。acc 是 40 位精确累加，y 是转换输出块前保留的 int16，wire 是 6,752 个物理字，decoded 是从输出块恢复的 int16。逐项定义见[软件接口](../../integration/README.md)。

- [class_00](class_00/README.md) · _silence_
- [class_01](class_01/README.md) · _unknown_
- [class_02](class_02/README.md) · yes
- [class_03](class_03/README.md) · no
- [class_04](class_04/README.md) · up
- [class_05](class_05/README.md) · down
- [class_06](class_06/README.md) · left
- [class_07](class_07/README.md) · right
- [class_08](class_08/README.md) · on
- [class_09](class_09/README.md) · off
- [class_10](class_10/README.md) · stop
- [class_11](class_11/README.md) · go
- [base](base/README.md) · 合成矩阵
- [worst](worst/README.md) · v4 配对集
