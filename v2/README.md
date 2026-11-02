# v2：当前开发主线

固定任务 `X[99,64] × W[64,256] + b[256] → Y[99,256]`。这是本科第一 Dense 加速器，不是完整语音识别硬件。先读 [项目导读](../02_项目导读/README.md)。

| 目录/文件 | 功能 | 建议阅读顺序 |
|---|---|---|
| [rtl](rtl/README.md) | 10 个可综合模块，8 lane、15 个内部 SRAM 宏 | 先 linear_core，再 dot64/mac8，最后 NICE/ICB |
| [integration](integration/README.md) | E203 同名包装、RV32 驱动头、宏/时钟模板 | SoC 联调前必读，默认内存窗口关闭 |
| [tb](tb/README.md) | 算术、总线、矩阵/错误/复位测试 | 根据症状选层级，不用分类结果猜硬件错误 |
| [py](py/README.md) | 整数金模、转换、运行脚本 | 先 numeric_model，再 capture_activations |
| [vec](vec/README.md) | 固定 golden/权重/模型 smoke | 可以直接仿真，不必重生成 |
| [validation_real_speech_20261102](validation_real_speech_20261102/README.md) | 自选 600 例真实验证数值、批量 RTL 对照与原始日志 | 查看本轮真实语音覆盖、数值误差及完成范围 |
| [server_eda](server_eda/README.md) | 竞赛服务器专用综合/仿真流程 | 须使用实际服务器工具和库，勿在本地直接套跑 |
| [build](build/README.md) | 结果摘要/新的运行输出 | 历史完整构建已归档 |
| [dist](dist/README.md) | 历史打包脚本输出位置 | 正式交付以 ../releases 为准 |
| implementation_spec.md | 数值、状态、地址、错误的实现规格 | 精确契约 |
| rtl.f / sim.f / run.sh | 源文件顺序及 Linux 回归入口 | 加入正式平台 filelist 时核对路径 |
| REVISION_FIX1.md | 本轮实现修复说明 | fix1 没改 RTL 算法 |

当前时序/VM 结论以 [fix1 报告](../vm_eda/REPORT.md) 为准；validation.md、旧 server_eda/RESULTS.md 与 v2 阶段报告保留其历史日期，不代表最新完成度。2026-11-02 自选 600 例数值最大层汇总 NRMSE 0.03891237%，13 套真实输入 RTL 回归 377/377，通过范围见本轮报告；正式 CPU/共享 RAM 和组委会最终评测仍待验收。

v2 相对 v1 使用三级精确乘法及相邻行计算/写回重叠，数值和外部 ABI 保持相同；固定等待 TB 的 12 次 NICE 周期减少 20.2065%，不能写成完整语音或 CPU 性能。

本地快速检查：`python v2/py/run_xsim.py --tag learn --tops tb_kwt_arithmetic`（从工作区根执行）。私有 VM 用 `make -C flow v2`，不是在 Windows 本目录执行。

工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。

[返回工作区首页](../README.md)

2026-11-02 服务器整理：根目录新增 Makefile，见 [服务器手动操作](SERVER_GUIDE.md) 与 [服务器本轮报告](SERVER_RESULTS.md)。新增 58 场景异常 TB，原 RTL/数值格式不变。
