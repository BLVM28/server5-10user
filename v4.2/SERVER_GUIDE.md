# 在 5 号服务器运行

打开个人终端，切到版本根。当前服务器目录与 v2/v4.1 并列；VCS、DC、PT、Verdi 和公共库路径由已验证的 v2 启动器设置。

```sh
cd /storage2/2026contest/server5/s5_10usr/v4.2
make env
make precision           # 单测 v4.2 的 12 层，对照黄金矩阵并打印吞吐
make run                 # 12 套基础 RTL 测试，看到 FUNCTION ALL PASS
make paired              # worst 同组比较四种格式；输出 12 次总拍数和 tasks/s
make timing              # 默认 6.666667 ns，检查 SS/FF 建立、保持及全部报告违例
make gate_sample         # SS 和 FF 各跑新格式的第 0 层完整矩阵
make report              # 复核已有基础功能与时序结果
```

`make compile` 只编译。完整功能覆盖用 `make regress JOBS=2`；该命令先验证 14 组向量，首次缺失会用标量算法重建。`make immediate modes` 覆盖立即返回、连续切换与错误恢复。`make waves && make verdi` 打开新格式完整系统测试的 VCD（直接 make verdi 也会先生成缺失波形），`make waves` 默认保留前 200 μs；需要检查新格式的数值时使用 `build/manual/runs/worst/tb_kwt_precision/` 的 run.log 和实际 RAM 导出。

`make synth` 建立或校验本版快照，`make timing PERIOD=6.25` 测 160 MHz。`make sweep` 会对所有设定工作点运行，任一频点失败都会返回非零，150 MHz 单点可以独立通过。`make acceptance` 对照发布摘要、完整回归、SDF 和数值证据；若清理过运行目录，先执行 `make regress`、`make immediate modes`、`make timing gate_sample`。常用 `make clean` 只清理本版本 manual 目录并备份文本证据。

日志中的 `core_cycles` 是内部核心时间，`NICE_TIME cycles` 从指令接受到完成引脚。吞吐用同批成功任务数除以合计 NICE 周期，再乘 150,000,000。时序 PASS 还要求全违例报告为空及 setup/hold 均非负。GDS 布线和 E203 实际调度未计入。[结果](RESULTS.md)
