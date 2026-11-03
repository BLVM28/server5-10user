# 5 号服务器 · 从 v3.1 根目录跑 EDA

```sh
cd /storage2/2026contest/server5/s5_10usr/v3.1
make check                      # 七套 VCS + 当前完整核的双角 200 MHz 静态时序
make paired                     # 同一组 worst 真实激活，12 层首次任务的总周期
make timing PERIOD=6.666667      # 赛题 150 MHz
```

| 操作 | 用途 | 通过判据 |
|---|---|---|
| make env / make compile / make run | 找工具和库，编译并运行本版 RTL 与实际 SRAM 功能模型 | ENV PASS、COMPILE PASS、FUNCTION ALL PASS: 7 suites |
| make clean | 归档本版 build/manual 下的报告，再清理该日常输出目录 | CLEAN PASS。不清理 DC 结果、实现快照或 v3 |
| make paired | 用 worst、同系统 TB 验证输出并汇总 12 层时间 | PAIRED PASS 和实际总周期。独立验证 14 次输出，其中 2 次恢复任务不计性能 |
| make regress | 七套基础加 class_00…11 和 worst 系统测试 | FUNCTION ALL PASS: 20 suites |
| make timing / make sta | 对本版已安装映射重新做 SS/FF，默认周期 5 ns | 两个 TIMING PASS，setup、hold 非负且报告违例总数为零 |
| make report | 核对功能记录、源指纹、向量、网表、SDF、选定周期并汇总 | BASIC CHECK PASS。单独使用其它周期时 report 也带相同 PERIOD |
| make synth | RTL/映射约束改动后，按 mapping_period.txt 从当前源生成或复用经过指纹校验的本版映射，合格后装入 implementation/rebuilt | MAP_COMPLETE 或复用已有映射，最终 IMPLEMENTATION PASS。新版本的实例命名改变时须按实际报告复核 ECO |
| make sweep | 依次测 150/180/200/210/215/220 MHz，全部检查后列出违例频点 | 逐频点读两个角结果。单点测量可用 make timing PERIOD=… |
| make waves，再 make verdi | 前者运行完整系统 TB 并保存截取的顶层接口 VCD，后者启动 Verdi | 普通 make run 不产生 VCD |
| make probe / make gate JOBS=4 | 先用相同 PERIOD 运行 make timing。做两角 SDF 注释短探针，或各跑 12 个完整门级任务 | 两角 ANNOTATION PROBE PASS 或对应完整门级记录 |
| make acceptance | 核验已有的默认 200 MHz check、regress、waves、probe 记录和公开频率表，逐项对 RTL、向量、SDF 哈希 | EXTENDED ACCEPT PASS。新目录需先运行上述命令 |
| make vectors / make package | 从固定 v2 向量恢复本地副本，生成 RTL、TB、Makefile、流程、向量五包 | 952 个 SHA 正确，五条 PACKAGE PASS |

**定位失败。** 功能看 build/manual/runs/标签/TB/run.log。面板压力覆盖要有 PANEL PASS 2/2、full 和 partial 非零。时序看 build/manual/timing/rebuilt/周期/kwt_nice_core_{ss,ff}/，先读 metrics.txt，再读 violations.rpt 与 setup.rpt。运行 make clean 前当前已通过的报告可在 reports/ 留存。清理后重新运行 make check。若另一终端正在跑本版本命令，锁会拒绝并发改写，请等该作业完成。
