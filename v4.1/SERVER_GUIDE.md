# 5 号服务器手动复测

```sh
cd /storage2/2026contest/server5/s5_10usr/v4.1
make report       # 读已有九套旧格式/算术和两套新格式证据，以及 150 MHz 双角记录
make paired       # 相同 12 个冷任务，打印三种格式的 NICE 周期、150 MHz tasks/s
make acceptance   # 对照发布材料核验功能、吞吐、高频、精度和门级结果
```

| 命令 | 结果与使用条件 |
|---|---|
| make clean / compile / run | clean 仅清 v4.1/build/manual，已有日志归档到本版 reports。compile 编译 11 个基础 TB。run 跑 11 套 |
| make check | env、run、150 MHz timing、report，最后必须 BASIC CHECK PASS |
| make regress JOBS=2 | 11 套基础加 13 组激活的三种格式，共 50 套。自动检查独立黄金向量 |
| make modes | 同一核连续执行三种格式和错误恢复，全部五次任务逐项核对 |
| make immediate / make gate_sample | 同拍应答专项和独立的实际 SDF 双角完整 Block8 第 0 层 |
| make timing PERIOD=5.555556 | 以 180 MHz 为例，重新分析冻结网表，两角、所有报告约束均通过才返回成功 |
| make sweep / make synth | sweep 测 150–210 MHz 八个频点，任一点失败就返回非零并保留所有结果。synth 检查完整网表与当前源签名，变更后会执行 DC/PT |
| make waves / make verdi | 先生成 VCD，再打开波形。观察 nice_req_valid/ready、ICB 命令及应答和 nice_rsp_valid |
| make vectors / make package | 用 Python 标准库重建并校验 1,190 个 Block8 文件，或按成员核验五个 ZIP |
| python3 -B py/delivery.py check | 核验完整发布清单，包括五个 ZIP 的字节 |

从清空的 manual 恢复全部记录时，依次运行 compile、regress、waves、timing、immediate、modes、gate_sample、acceptance。计时指标从指令接收至第一次有效完成，core_cycles 只代表核内时间。用 PERIOD 改 STA 周期不会改变比赛吞吐的 150 MHz 口径。[服务器验收](SERVER_RESULTS.md)
