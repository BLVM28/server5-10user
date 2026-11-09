# v4.5 整机 RTL

v4.5 以 v4.4 r9 为基线，按 160 MHz、6.25 ns 优化整机。赛题成绩统一按 150 MHz 计算。修改集中在共享 SRAM、E203 定时器、取指反馈和时钟连接。矩阵核沿用 8 行 × 16 列的 128 路乘累加阵列。

| 位置 | 内容 |
|---|---|
| [架构说明](ARCHITECTURE.md) | 请求经过哪些寄存器、为何增加在途额度，以及修改对时序和功耗的影响 |
| [实测报告](REPORT.md) | 同负载吞吐、功能覆盖、时序与面积，及当前验收状态 |
| [rtl](rtl/README.md) | 加速器、ICB 读写和数值处理 |
| [tb](tb/README.md) | 独立核 golden、总线等待和错误测试 |
| [soc](soc/README.md) | E203、共享 SRAM、启动固件、整机测试、DC 和 VCS |
| `results/` | 结果摘录、工具路径和源文件校验值 |

## 在比赛服务器运行

```bash
cd /storage2/2026contest/server5/s5_10usr/v4.5/r7
make help
make compile
make run PAIRED= V44_REFERENCE=../../v4.4/r9 WFI_FIRMWARE=build/fw/timer_wfi.hex
DC_CORES=4 make timing
make gate
```

`make run` 比较三种装载模式，并执行 ITCM、CLINT、共享 SRAM、算术和总线测试。服务器测试包带独立的 WFI 自检固件。自行生成该固件时先运行 `make firmware-wfi`，其产物为 `build/fw/timer_wfi.hex`。默认性能固件用 v4.4 r9 的原始 hex。各版本的性能对照使用同一测试平台、时钟和计时边界。

`make timing` 先校验 VCS 通过记录与源文件哈希，再用同一份 RTL 做 DC 映射和 35 组 PVT/RC 分析。默认 `PERIOD=6.25`。如需以 150 MHz 重新映射，使用 `PERIOD=6.666666667`。输出位于 `soc/work/`，关键结论见 `execution.log`、`last_dc.json` 和各次运行的 `reports/`。各服务器安装位置集中在 [paths.tcl](soc/flow/paths.tcl)。

`make gate` 使用同一次 DC 结果的最差建立角和保持角原生 SDF。诊断时可用 `make gate-primary` 检查主角原生 SDF，或用 `make gate-functional MAPPED_RUN=映射目录` 验证网表逻辑功能。查看每个阶段的 `result.json` 和 `run.log`。最终以功能逐字核对、STA 及相应回标记录分别判断。

服务器的 `r8` 使用与 `r7` 相同的 RTL。执行 `make period-check MAPPED_RUN=映射目录 PERIOD=6.666666667`，在原网表上检查最差建立角和保持角。若已有主角检查点，可以用 `make period-primary MAPPED_RUN=映射目录 PATHS=../r7/soc/flow/paths.tcl PERIOD=6.666666667` 检查主角。脚本确认变更仅限主时钟周期和波形，并核对原周期逐路径组裕量能否复现。

150 MHz 最终对照使用保存在服务器的保持修整网表。以下命令在 `r7` 目录下复跑无 SDF 功能和两个极值角的原生 SDF。两次原生回放目前均在启动自检超时。

```bash
make gate-functional PERIOD=6.666666667 MAPPED_RUN=soc/work/dc/v45_hold150_probe_20261109_115841_66627
make gate DC_RESULT=soc/work/hold_pad_worst/result.json
```

35 组时序表在 `soc/work/dc/v45_hold150_native_20261109_121331_84487/reports/corner_matrix.tsv`。对应的 150 MHz 综合脚本和保持修整脚本保存在同级 `../hold_guard/flow/`。
