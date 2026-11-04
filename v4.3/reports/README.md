# 服务器过程日志与公开传输摘要

map.log 是综合与两角扫点；regress_final.log 是 30 套最终 VCS 回归；reference_release.log 是同公共 SRAM 端点下的 v4.2 参照；power_v*_*.log、gate_v43_ff.log 是功耗/门级主过程。实际工具细节在 build/。

public.json 由 evidence.py 检查后生成，只包含可公开的测量；probe.json 是临时只读核对摘要。正式结论已提炼到 results/ 和 RESULTS.md。过程日志及临时摘要不提交 Git。
