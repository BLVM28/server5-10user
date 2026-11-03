# 正式服务器验收 · v3.1

正式目录为 `/storage2/2026contest/server5/s5_10usr/v3.1`。数据、RTL 和频率各有独立判据，见[操作手册](SERVER_GUIDE.md)。

| 检查 | 正式目录实测 |
|---|---|
| VCS 七套基础功能 | 算术 260/260、分段进位 7/7、ICB 4/4、系统 29/29、重叠 5/5、错误 58/58、乘法穷举 524288/524288 |
| VCS 语音激活扩展回归 | make regress 打印 FUNCTION ALL PASS: 20 suites。七套基础外，class_00 到 class_11 的 12 个类别代表集和逐层 worst 各跑一次系统 TB，13 组均为 29/29 |
| 面板专项 | 两个复位/读错场景均通过。90 次完整页切换、3 次缺页后缀补读、13,886 次暂停发读、23,331 笔背景读 |
| 同数据成对测量 | worst 12 个首次任务 3,454,643 拍，VCS 与 XSim 逐层一致。每个正常矩阵写回 12,672 个字，系统 TB 会检查所有累加值与最终 Y |
| 正式目录日常验收 | make check 打印 BASIC CHECK PASS，make waves 系统 29/29 并生成约 2 MiB 的顶层 VCD |
| SDF 与扩展验收 | 200 MHz 的 SS 和 FF 各自完成 SDF 注释短探针，均为 0 errors、0 warnings。make acceptance 打印 EXTENDED ACCEPT PASS，并核验 7 套基础、13 组语音、波形、各角 SDF 及匹配的网表 |
| SMIC40 完整加速器 | 最终网表在 150、200、210、215 MHz 两角均零报告违例，220 MHz 慢角 setup −0.071551 ns，有 4 条违例 |
| 网表身份与实现面积 | mapped SHA-256 `00389fe9806504eb83a23cfe47d1ffdae61e09999a72275dc5fdfcf52c1972bb`。整核 155089.240090，宏 85456.079102。公开 PPA 摘要已与服务器私有 qualification.json 逐字段比较 |

正式网表由本版源 RTL 独立综合，目录 `build/ppa/44ae33622389a6fb/resize_406f14554c8eb630/` 保存原始网表、双角报告与单实例结构审计。首轮含复位释放违例的对照仍在同一指纹下的 repaired/。用户可通过 `make check` 重跑日常功能与 200 MHz STA，通过 `make paired` 获取新的 12 任务吞吐对照。[公开时序机器记录](results/ppa.json) · [逐层功能证据](results/functional.json)

完整 12 层门级长仿真、真实 E203 固件/共享 RAM、官方语音集端到端准确率及整机功耗均未计入本版通过项。

公开的[验收记录](releases/verification.json)可在服务器通过 `make acceptance` 与实际记录核对。[交付清单](releases/source_manifest.json) 可通过 `python3 py/delivery.py check` 核对源码、向量与分类包。
