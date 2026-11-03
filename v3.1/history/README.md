# 试验记录 · 分开量两项改动

| 试验 | 乘法器 | W 页预取 | 12 层总周期 |
|---|---|---|---:|
| v3 已冻结 | 三级 | 无 | 4,157,612 |
| A | v3 原三级 | 有 | 3,420,525 |
| B，交付 v3.1 | 四级 | 有 | 3,454,643 |

A 对 v3 单独量出预取的贡献。B 对 A 多 34,118 拍，换取乘法关键路径的流水边界。两个版本之间的时序差异最终以 B 和 v3 的各自完整、真实网表为准。A 只作功能和周期对照，未独立报告晶圆库频点。

在本地 v3.1 根目录用 Vivado 2023.2 复现：
```powershell
python py/run_xsim.py --panel-only
python py/run_xsim.py --tag final_base
python py/run_xsim.py --tag final_worst --vectors ../v2/vec/real_speech/worst --tops tb_kwt_system
python py/run_xsim.py --tag panel_stress --tops tb_kwt_overlap
python py/run_xsim.py --tag panel_swap_large --define KWT_TEST_SWAP --define KWT_TEST_W1024 --tops tb_kwt_overlap
python py/compare.py
```
panel-only 在本版 build/prefetch_reference 另建试验目录，只替换那份副本里的乘法器。正式 RTL 不参与写入。[逐层证据](../results/functional.json)

服务器 history/ 保存本轮分阶段上传的源码 ZIP，文件名包含内容哈希前缀。日常使用版本根中的源码与 packages/ 的五个分类包。
