# 服务器 EDA 流程入口（2026-11-02）

现在从版本根目录执行 `make`，或在本目录执行转发 Makefile。操作手册：[SERVER_GUIDE.md](../SERVER_GUIDE.md)；本轮结论：[SERVER_RESULTS.md](../SERVER_RESULTS.md)。

- `easy.py`：编译/功能回归、哈希绑定、综合、双角 STA、逐层并行 SDF、波形与结果汇总。
- `manual_synth.tcl`：读当前 RTL 和真实 SRAM 库进行综合。`reset_repair*` 与 `cap_eco5.tcl` 仅用于映射后的最小延迟/驱动修复。
- `manual_sta.tcl` + `constraints.tcl`：独立重建原始约束，输出 setup/hold、约束违例、覆盖与 SDF。不能把优化时的 margin 当作最终约束。
- `tb_core_all_gate.sv`：12 层完整矩阵的外部接口检查；每个进程可用 `+LAYER=N` 独立运行一层，汇总必须覆盖 0–11。
- `wave_dump.sv`：可选、限窗口的顶层接口 VCD，正常回归不产生大波形。

旧脚本仅保留参考；下面是 **2026-11-01 历史记录**，其路径和命令不能代替当前入口。既有正式 ZIP 不改。

---

> 2026-11-01 整理更新：本目录原有技术说明保留。最新完成度以工作区根 README 和 fix1 报告为准；本轮只整理本地资料，不自动同步新文档到 VM/服务器。 RESULTS.md 等是原阶段历史；fix1 最新无报告违例的实现与范围见 vm_eda/REPORT.md。
> [工作区首页](../../README.md) · [调试导读](../../02_项目导读/03_调试与E203接入.md)

# 服务器功能仿真与初步时序检查

本目录补充服务器端 Makefile、独立 150 MHz 测试平台、Design Compiler 综合脚本与 PrimeTime 检查脚本。设计 RTL 保持交付包中的版本，测试预期不因工具结果而修改。

实际运行结论见 [RESULTS.md](RESULTS.md)。功能通过不等于时序通过；本版完整加速器仍有 hold 负余量。

## 服务器工程位置

```text
/storage2/2026contest/server5/s5_10usr/kwt_eda_tmp_20261101/
  kwt_rtl_v1.zip                 原始交付包
  upload_verified.json          压缩包和 236 个文件的校验记录
  library_selection.json        实际 SS TT FF 库路径
  libraries/                    个人目录内选取的标准单元库与编译后的 SRAM DB
  compile_sram.log               Library Compiler 日志
  project/                      原交付包展开的完整工程
    server_eda/                 本目录的 Makefile TB Tcl 与 Python
    build/server_eda/           新增检查的网表 SDF 报告和日志
    build/server_functional/   服务器完整功能回归
    build/server_activation/   原模型静音对应层输入回归
```

FTP 仅用于上传本队文件，暂存位于个人 home 的 `Desktop/kwt_eda_upload_20261101`。解包前核对原交付包 SHA-256：`327edf5c22e8a92b388195178e315a379d8a9998d6c7df4d643ec038d1d7fff9`，并逐文件核对 MANIFEST。公共目录全程只读，脚本将工程输出和临时目录均指定在个人 home 内。

## 执行命令

```bash
cd /storage2/2026contest/server5/s5_10usr/kwt_eda_tmp_20261101/project/server_eda
make all
```

也可单独执行 `make functional`、`make activation`、`make sram150`、`make dot150`、`make synth`、`make sta`、`make gate`、`make summary`。`sta` 和 `gate` 依赖先完成 `synth`，单独目标不会悄悄用行为 RTL 替代综合网表。禁止对该 Makefile 使用并行 `-j`，各阶段有先后依赖。

脚本兼容服务器 Python 3.6.8。进程内根据 `which lc_shell` 的真实路径设置 `SYNOPSYS_LC_ROOT`，解决该服务器 PrimeTime 启动时的 PT-063 环境错误；不修改系统环境配置。

库配置可通过 `make LIB_CONFIG=/绝对路径/library_selection.json ...` 指定。脚本限制生成目录必须处于指定个人 home 内；TMPDIR/TMP/TEMP 均指向当前检查子目录。没有提供递归清理目标，保留已有测试和失败记录。

## 每个目标验证什么

| 目标 | 输入和判断 |
|---|---|
| functional | VCS 与厂商 ARM_UD_MODEL；量化、点积、ICB、12 层矩阵及错误/复位场景 |
| activation | 指定 checkpoint 与原模型静音对应层 X；完整 12 层矩阵回归 |
| sram150 | 新 TB 使用默认厂商时序模型，遍历 1024/128 地址、16 种 bit mask、使能关闭保持；1186 次比较 |
| dot150 | 新 TB 从公开端口验证 32 个点积向量、气泡和结果背压；约 150 MHz 的 RTL 基线 |
| synth | SMIC40 HVT SS 0.99 V 125°C 标准单元；对 dot64 与完整 NICE 加速器分别综合，真实 SRAM DB 链接 |
| sta | PrimeTime 读取上述网表，在 SS 0.99 V 125°C 和 FF 1.21 V -40°C 分别报告 max/min 路径 |
| gate | VCS 运行 dot64 综合网表和标准单元 Verilog，回标 SS SDF，复用同一 32 向量 TB；启用负时序检查 |
| summary | 汇总各阶段 JSON；工具运行成功与 slack 是否满足分别判断 |

`run_checks.py` 检查进程退出码、实际 PASS 标记、fatal、工具 Error 和 timing violation。VCS 的 fatal 可能仍返回退出码 0，所以退出码不是唯一标准。STA 的 `completed=true` 表示完成分析，不表示 slack 非负；必须同时阅读 metrics/setup/hold/violations 报告。

## 时序约束和边界

目标周期 6.666667 ns，时钟不确定度 0.100 ns。输入/输出最大外部延迟各 1.000 ns、最小各 0.100 ns，输入转换时间 0.100 ns；输出负载取实际库中一个反相器输入电容的 4 倍。实际负载参考引脚和库单位均打印到日志，没有设置 false path 或 multicycle path。复位也没有用时序例外隐藏。

DC 实测负载为 0.002852 pF，PrimeTime 的 SS/FF 均复用这一数值。点积 TB 在上升沿后 1 ns 改变输入，与这项输入预算一致；不能换成下降沿送数后仍声称采用同一预算。时钟用 1 ps 仿真精度表示，实际周期为 6.666 ns（约 150.015 MHz）。门级目标把实际 DC SDF 复制到其运行目录，记录 SHA-256，并要求回标完成且错误、警告均为零。未关闭 timing checks 或 notifier。

这些是本次独立模块检查的明确假设，正式 SoC 的 I/O 预算仍须替换成平台约束。完整核心综合使用测试专用内存窗口以避免默认拒绝逻辑被常量优化，不代表正式共享 SRAM 地址已经确定。

标准单元来自公共 `SMIC40_2025/S40.tar.gz` 的 SCC40NLL VHSC40 HVT 库；SRAM 来自公共 RAMSP128X16/RAMSP1024X16 Liberty。库在个人目录内选择/编译，公共原件不变。Library Compiler 对部分宏电源/保持属性有警告，因此本次不提供功耗验收结论。

这是布局前检查：没有实际布线 SPEF、时钟树偏斜、OCV 或全模式全角签核。SRAM 独立 TB 使用默认 Verilog 时序参数，不能代替 Liberty 角的完整 STA；带 SDF 的门级动态测试目前覆盖 dot64，完整加速器由 RTL 功能回归和静态时序分别覆盖。E203 CPU 整机、正式共享内存映射和真实语音验证集精度仍不在这些结果的证明范围内。


工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。
