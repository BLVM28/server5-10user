# 服务器手动测试：从这里开始

在 VNC 中打开 Terminal，进入 `/storage2/2026contest/server5/s5_10usr/v2`。根目录的 Makefile 是统一入口；不要进入旧 kwt_* 路径。Windows 本地使用同一份源码，但服务器 EDA 命令需要在 Linux 服务器执行。

## 日常只需这些命令

```sh
cd /storage2/2026contest/server5/s5_10usr/v2
make env
make clean
make compile
make run
make timing
make report
```

也可以直接 `make check`，顺序执行环境检查、基础功能、双角时序、结果汇总。正常约 1–2 分钟（取决于许可证和服务器负载），首次编译略慢。`make compile` 只说明编译成功；`make run` 才验证功能。失败返回非零，终端给出日志路径。`make clean` 先保存日志/报告到 reports，再删除 build/manual；不会删除 RTL、向量或最终网表。

| 命令 | 做什么 | 成功判据/指标 |
|---|---|---|
| `make run` | 算术、总线、完整矩阵；v2 还含重叠和乘法流水线 | 每项完整 `ALL PASS, N/N`；打印 core_cycles 范围、每矩阵 12672 次 32 位写回 |
| `make timing` | 固定网表，dot64/完整核心 × SS/FF | 四项 `TIMING PASS`；setup/hold slack 非负、无报告约束违例 |
| `make report` | 汇总当前源码对应的已有结果 | 功能计数、矩阵周期、MHz、setup/hold；缺失或源码改变显示 INCOMPLETE/STALE |
| `make timing PERIOD=8.0` | 检查 125 MHz | 其它约束不变；随后用 `make report PERIOD=8.0` 查看 |
| `make sweep` | 同一网表扫描 150/140/125 MHz | 每周期四个角/模块组合 |
| `make waves` / `make verdi` | 生成 VCD / 打开 Verdi | 波形只辅助调试；不以界面打开代替 PASS |
| `make regress` | 基础功能 + v2 的 13 组真实语音激活 | v2 18 组；约 10 分钟，可按需要运行 |
| `make negative` | v2 新增 58 个非法描述符/地址/错误/恢复场景 | `ALL PASS, 58/58`；v1 不适用 |
| `make synth` | 从当前 RTL 重新综合并做已验证修复 | 产生 implementation/rebuilt；还要做 timing |
| `make package` | 刷新分类 ZIP 并校验每个成员 | rtl/tb/makefile/flow/vectors 各自 PASS |

`core_cycles` 是该测试激励下的硬件周期数，受总线反压影响；乘以目标周期可估算相同激励下的硬件时间，不能当作 E203 整机实测延时。

## 看波形

```sh
make waves
make verdi
```

默认保存前 200,000 ns 的顶层接口，功能检查仍完整执行。Verdi 打开后在 nWave 中 Add Signals，优先加入 nice_req_valid/ready、nice_rsp_valid/ready/err/rdat、nice_icb_cmd_valid/ready/addr/read/wdata、nice_icb_rsp_valid/ready/err/rdata。valid 与 ready 同时为 1 才完成握手；反压期间载荷必须保持，最后一笔写响应收回后才能报告完成。无需先研究所有内部波形。

## 改过 RTL 后

```sh
make run
make synth
make timing NETLIST=rebuilt
make report NETLIST=rebuilt
```

默认 NETLIST=fix1 对应已有修复网表。源码 SHA 改变时，脚本拒绝用旧网表冒充当前时序结果。综合完成不等于 timing 通过。固定实例的 ECO 若因结构变化失配会明确报错，需要按新违例调整，不能删断言继续。建议重要改动后追加 `make regress` 和 v2 的 `make negative`。

## 可选的门级测试

`make probe` 只验证 SS/FF 的 SDF 与模型能否正确注释，不运行矩阵；`make gate JOBS=4` 才做两角各 12 层完整矩阵，可能耗时较长，不放进日常 make check。本轮扩展全层门级测试没有完成，不写成通过；此前 fix1 的单矩阵门级结果保留在历史记录。

导出使用 PrimeTime 原生命令 `write_sdf -context verilog -exclude {clock_tree_path_models}`：条件表达式与提供的 Verilog 模型匹配，省去模型没有对应路径的内部 CLK→CLK 表示；完整 STA 不排除这些库信息。VCS 保留 `-sdfretain +neg_tchk`。没有修改黄金值、SRAM 模型、时序检查数值或设置 mask_violations。SDF 编译注释日志必须 errors=warnings=0，逐层运行同一角已核验的程序；日志副本明确标注来源。

## 目录与模块关系

| 路径 | 用途 |
|---|---|
| rtl/、rtl.f | 10 个硬件模块与编译顺序 |
| tb/ | 自检平台；不是 E203 CPU |
| vec/ | 定点输入/权重/偏置/黄金值；v2/vec/real_speech 含 13 组真实激活 |
| py/ | 数值金模、生成器及本地仿真入口 |
| integration/ | NICE 包装和 C 驱动模板 |
| server_eda/ | 当前 Makefile 调用的 Python/Tcl/门级 TB |
| implementation/ | 服务器的 fix1/rebuilt 网表、SDF、DDC、哈希；本地只有说明 |
| build/manual/、reports/ | 当前产物、日志和 clean 前证据 |
| packages/ | RTL/TB/Makefile/流程/向量分开打包 |
| history/、releases/ | 历史工程归档、原冻结包；不作为当前活动源码 |
| ../shared/ | 服务器库配置/私有库/迁移记录；公共库只读 |

数据流：E203 NICE 发描述符 → nice_core 检查任务/地址 → linear_core 调度搬运 → X/W SRAM 缓存 → mac8 的 8 路 dot64 → quantize 舍入/饱和 → ICB 写回 Y → 等写响应后通知完成。详见 rtl/README.md。

本科硬件输出 `Y[99,256] = X[99,64] × W[64,256] + b[256]`，不是 yes/no。真实语音经原模型的前处理、attention、LayerNorm 得到 X；Dense1 之后还需要 GELU、Dense2、后续层及分类头。12 层是 12 个独立的 Dense1 任务，不能把上一层 256 列 Y 直接当下一层 64 列 X。

当前功能/时序通过范围与频率见 SERVER_RESULTS.md。真实 E203、正式共享 SRAM 地址/实现、固件和顶层约束仍需整机联调，测试窗口 0x10000000/512 KiB 不代表官方地址。

## 工作日志

2026-11-02：历史 v1/v2 分别归档并逐项校验；源码不改，补充 Makefile、异常 TB、STA 扫描与操作说明。按用户要求收敛验证范围：基础回归和 STA 为日常验收，全层门级为可选。源码、TB、向量和流程目录在本地/服务器同步；工艺库、工具二进制和生成网表保留在服务器。失败探针及未完成实验保留记录，不计入 PASS。
