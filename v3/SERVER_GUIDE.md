# 5 号服务器 · 从 v3 根目录手动运行

```sh
cd /storage2/2026contest/server5/s5_10usr/v3
make                 # 命令帮助
make check           # 环境、七套基础功能、完整核心双角 STA、汇总
```

也可以依次运行 `make clean`、`make compile`、`make run`、`make timing`、`make report`。每步检查工具退出码和完整结果。最终 `BASIC CHECK PASS` 表示所选网表与当前源码相符，七套基础功能与两角时序同时通过。失败时终端显示相应目录；先查看具体 log，再定位模块。

| 命令 | 做什么 | 正常结果或读数 |
|---|---|---|
| `make env` | 检查工具、库配置和所选映射身份 | `ENV PASS` |
| `make clean` | 先保留 build/manual 下日志、报告、JSON，再清理该目录 | `CLEAN PASS`；冻结网表、黄金值、分类包仍可使用 |
| `make compile`、`make run` | 编译七个 TB、运行默认固定输入 | 每组 `ALL PASS, N/N`；矩阵打印 core_cycles 范围 |
| `make negative` | 单独跑 58 个非法输入、访存错误和恢复场景 | `58/58` |
| `make regress` | 七个基础 TB，另跑 class_00…11 与 worst 的系统 TB | 全部执行后为 20 组；比日常回归耗时长 |
| `make timing`、`make sta` | 对已核验的 v3 完整核心网表在 SS/FF 重新跑 PT | 分别打印 MHz、setup/hold ns、违例数及宏/整核面积 |
| `make timing PERIOD=6.666667` | 赛题统一约 150 MHz；后续 report 带同一 PERIOD | SS/FF 均 PASS 才通过 |
| `make sweep` | 同一网表检查约 200/180/160/150 MHz | 4 个周期、8 个组合，独立存档 |
| `make report` | 检查现有记录是否对应当前 RTL、TB、向量、网表和 SDF | 缺结果或哈希改变显示 INCOMPLETE/STALE，并返回非零 |
| `make waves`、`make verdi` | 完整运行系统 TB，同时保存前 200000 ns 接口 VCD；再打开 Verdi | 普通 `make run` 默认不生成波形 |
| `make vectors`、`make package` | 恢复缺少的固定数据，校验五个分类包 | 输出已核验文件数量，清单见 packages/manifest.json |
| `make synth` | 按当前 RTL 指纹构建或复用合成结果，核验 v3 的单元修复、200 MHz 双角及面积预算，发布 rebuilt | 随后运行 `make timing NETLIST=rebuilt`、`make report NETLIST=rebuilt` |
| `make probe`、`make gate JOBS=4` | 先对同 PERIOD/NETLIST 执行 make timing；probe 为 SDF 短探针，gate 再对两角各跑 12 个完整矩阵 | gate 属于较长的可选验证，有完整矩阵记录才能计入门级通过 |

**选向量。** 整套 `make run` 包含需要 dot/quant 向量的组件 TB，应使用默认 vec。13 组真实激活使用 `make regress`；只看某组的完整系统波形可用 `make waves VEC=$PWD/vec/real_speech/worst`。看波形优先加入 nice_req_*、nice_rsp_*、nice_icb_cmd_*、nice_icb_rsp_*。valid 与 ready 同时为 1 才是一次握手。

**选网表。** 默认 `NETLIST=qualified200`，指从此前已通过 200 MHz 的 v3 实现导入的冻结网表，原始鉴定报告和映射哈希见 [results/ppa.json](results/ppa.json)。普通 timing 重新分析这个网表，不重新综合。改动 RTL 或映射 Tcl 后旧快照会拒绝运行，使用 `make synth` 并根据新报告检查修复清单。不得改指纹来绕过过期检查。

**读数范围。** `core_cycles` 包含当前 TB 的总线等待。200 MHz 通过是加速器的布局前 STA 结论。正式 E203 的时钟、共享 RAM 和固件另需整机验证。[本轮工艺结果](RESULTS.md) · [日常日志位置](reports/README.md)
