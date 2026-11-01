# v1 VM 验证摘要

`summary.json` 把功能计数、RTL SHA、结构审计、时序和 SDF 产物关联在一起，最终 completed=true。范围是行为 SRAM 完整加速器 RTL + GPDK045 dot64 布局前 STA/SDF，不是完整 CPU/语音/物理签核。

| 角 | setup slack ns | min slack ns |
|---|---:|---:|
| slow | 1.132 | 0.213 |
| fast | 4.483 | 0.006 |

functional 看 RTL；eco_dot 看缓冲等价审计；sta_eco_* 看双角约束/覆盖；gate_eco_* 看 32/32、注释完整性及网表/SDF SHA。timing_run/eco_run 只说明阶段执行，不能单独代替约束通过。

修复前失败和完整原始产物在上级说明所列归档；请勿把已归档的 baseline sta_slow/fast 当作最终 STA。

工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。

[返回工作区首页](../../../README.md)
