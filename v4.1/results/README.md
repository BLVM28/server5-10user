# 可公开的实测记录

[functional.json](functional.json) 保存 12 层 XSim 周期、源/日志 SHA、与 v4 的成对基线。[workloads.json](workloads.json) 每行依次为原始、无损差分、Block8 三种格式的 12 任务 NICE 总周期及总写数。[ppa.json](ppa.json) 含同一网表的面积、角、建立保持余量和违例数。[gate.json](gate.json) 含 SS/FF 两次完整矩阵的 SDF、运行日志、网表身份和实际事务数。

[accuracy.json](accuracy.json) 记录新格式相对原模型的 NRMSE。[accuracy_cases.json](accuracy_cases.json) 提供 600×12 个独立值。[accuracy_provenance.json](accuracy_provenance.json) 固定样本、程序和来源。[driver.json](driver.json) 记录 C 编解码与实际内存双方验证。[rv32.json](rv32.json) 固定驱动编译结果。[报告](../RESULTS.md)
