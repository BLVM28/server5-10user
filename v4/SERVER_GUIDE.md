# 5 号服务器 · v4 操作

```sh
cd /storage2/2026contest/server5/s5_10usr/v4
make check           # 9 套 RTL 功能 + 完整核 150 MHz SS/FF STA + 本次报告
make paired          # worst 12 层，两种格式的 NICE 周期与 150 MHz 吞吐
make acceptance      # 核验已有扩展记录、网表、软件对照和双角门级样本
```

| 命令 | 工作及判据 |
|---|---|
| make env / clean / compile / run | 找工具和指定库，在清理 manual 前归档报告，编译和运行九套 TB |
| make timing PERIOD=6.666667 | 用冻结的 rebuilt 网表，在实际 SS、FF 角重新构造约束。两个角都要 setup、hold 非负且无报告违例 |
| make report | 检查当前 RTL、TB、向量、执行日志、网表和 SDF 是否属于同一配置。最终为 BASIC CHECK PASS |
| make paired | 原始和紧凑模式分别打印 12 次冷启动任务，不计恢复重复。频率须与对应 STA 一起读 |
| make regress JOBS=2 | 9 套基础，加 13 组真实语音激活×2 种格式，共 35 套。最多同时运行两个 VCS 任务 |
| make waves，之后 make verdi | 运行原格式系统 TB，生成可打开的顶层 VCD，检查 NICE 与 ICB |
| make sweep / make synth | sweep 测当前网表的 150/160/180/200 MHz，任一频点有违例即返回非零。synth 对未变的源先验证冻结网表，改 RTL 后重新综合并跑四个频点。只安装通过 150 MHz 的新映射 |
| make gate_sample | 针对当前 PERIOD 重新 STA，在独立私有目录编译 SDF，实测 SS/FF 的 worst 第 0 层紧凑矩阵。包括标签、写回计数及每个解码输出 |
| make fast_return | 专项压力：整张紧凑矩阵的每笔 ICB 命令都在接受当拍返回应答。逐笔核对数据、地址、标签、无遗漏与无重复；不计入性能成绩 |
| make probe / make gate JOBS=2 | 手动先 make timing，前者为两角 SDF 短探针，后者为原格式两角各 12 层长门级测试 |
| make vectors / make package | 核对 952 个固定向量，重建并逐成员核验五个 ZIP |
| python3 py/delivery.py check | 比较本机交付文件与冻结清单，包括五个分类包字节 |

**读数。** core_cycles 是计算核忙的时长；NICE_TIME 为任务从指令握手到第一次有效完成响应的时长，后者用于本版吞吐。一个任务固定 11,624 个读字（包括描述符），写数取决于 format 和数值。packed_gate 为有 SDF 的完整映射样本，不能与 RTL 仿真或仅注释探针混写。[验收结果](SERVER_RESULTS.md)
