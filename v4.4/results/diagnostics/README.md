# 加速器门级定位

`direct_gate_probe.py` 复用整机测试的向量、输出判据和两次 E203 ROM 启动。测试通过外部装载口写描述符和 `0xA0080000`，经过真实共享 SRAM、仲裁和加速器综合网表。它使用 VCS 功能模型，计数只用于验证覆盖。

在已执行 `make run` 或 `make compile` 的服务器 v4.4 根目录启动，把脚本路径和映射目录换成服务器中的实际绝对路径。

```bash
python3 -B /实际路径/direct_gate_probe.py /实际路径/映射运行目录
```

脚本在映射目录新建 `v44_mapped_direct_engine`。本轮原始日志保存在 r8 的 `soc/work/dc/v44_r1_20261109_034711_298259/v44_mapped_direct_engine/run.log`。通过标记为 `V44_CORE_GATE_DIRECT_PASS tasks=12 checked_words=58547 boots=2`。E203 固件调度的功能与 SDF 结果见 [验证记录](../README.md)。
