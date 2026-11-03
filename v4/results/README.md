# 可公开的证据

| 文件 | 可以核对的结论 |
|---|---|
| [functional.json](functional.json) | v3.1 原始、v4 原始、v4 紧凑在同一批 worst 上的每层 NICE 周期、核心周期、写数，以及 XSim 的源/日志证据 |
| [codec.json](codec.json) | 14 套输入的实际参考输出、各层模式直方图、348 帧 C 解码及 12 张 DUT 内存的 SHA。含已有 600 样本软件浮点评估的来源 |
| [speech.json](speech.json) | 每行四个整数依次为原始 12 任务 NICE 总周期、原始写字总数、紧凑 NICE 总周期、紧凑写字总数。base 是合成测试向量，worst 逐层选样，其余各类取一个代表样本 |
| [ppa.json](ppa.json) | 当前网表和 qualification 哈希、面积和频点，points 每行依次为周期 ns、角、setup ns、hold ns、报告违例数 |
| [driver.json](driver.json) · [first_candidate.json](first_candidate.json) | RV32IMAC 驱动编译和反汇编，以及首轮未达工艺验收的候选对照 |
| [numeric.json](numeric.json) | 独立 Fraction 金模重算 168 个输入矩阵，4,257,792 个累加和、4,257,792 个量化结果和 168 个饱和统计与冻结金值一致 |
| [gate.json](gate.json) | 两个工艺角的实际门级层记录，包括写数、总交易数、网表、SDF 和运行日志的 SHA-256。可在服务器用 make acceptance 与私有记录核对 |

把 12×150,000,000 除以总 NICE 周期得到该组 tasks/s。[对照报告](../RESULTS.md) · [服务器验收](../SERVER_RESULTS.md)
