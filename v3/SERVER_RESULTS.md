# 正式 v3 目录验收 · 2026-11-03

已在 `/storage2/2026contest/server5/s5_10usr/v3` 通过日常入口验收。源码清单中的 1058 个文件逐个核对，黄金数据共 952 个文件。

| 项目 | 正式目录结果 |
|---|---|
| VCS 功能 | 算术 260/260、进位 7/7、ICB 4/4、系统 29/29、重叠 5/5、异常 58/58、乘法边界 524288/524288 |
| PT 完整核心 200 MHz | SS setup/hold +0.000194/+0.295461 ns，FF +2.539268/+0.125206 ns；两角报告违例均为 0 |
| SDF 短探针 | SS、FF 注释日志均 0 errors、0 warnings；完整 12 层长门级另行运行 |
| 波形 | 系统检查通过，生成顶层 VCD，之后可用 make verdi 查看 |
| 分类包 | RTL 12、TB 9、Makefile 2、流程 33、向量 971 个成员，逐成员核对 SHA |
| 操作入口 | clean、compile、check、waves、probe、package、下级转发 report 通过 |

服务器原始命令、退出状态及各日志保存在 `reports/delivery_checks/`。结构和指标见 [版本首页](README.md)、[工艺实测](RESULTS.md)，机器验收记录在 [verification.json](releases/verification.json)，归档指纹见 [packages/manifest.json](packages/manifest.json)。真实 E203 固件及正式共享 RAM 仍需整机联调。
