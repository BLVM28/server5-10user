# 实现快照 · 只在服务器保存工艺网表

本版从 v3.1 的 rtl.f 在实际 SMIC40 库重新映射。服务器 [rebuilt](rebuilt/README.md) 下的 manifest.json 记录 RTL 和每个映射文件的 SHA。快照只在目标 200 MHz 两角及面积门槛通过后安装。如果 RTL、SDC、ECO 配方或文件哈希变化，make timing 会拒绝使用旧证据。[实测摘要](../RESULTS.md)
