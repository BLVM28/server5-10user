> 2026-11-01 整理更新：本目录原有技术说明保留。最新完成度以工作区根 README 和 fix1 报告为准；本轮只整理本地资料，不自动同步新文档到 VM/服务器。
> [工作区首页](../../README.md) · [调试导读](../../02_项目导读/03_调试与E203接入.md)

# 2026-11-01 fix1 交付索引

最新报告：`../../vm_eda/REPORT.md`。本次修复作用在映射实现及验证流程，20 个 RTL 文件与原 v1/v2 冻结包相同。新包包含源码、TB、Makefile、双角 STA/门级脚本及私有 VM 的结果；不包含 EDA 软件、许可证或工艺库。

## 本地 / 私有 VM（相同文件）

| 包 | 字节数 | 清单文件数 | SHA-256 |
|---|---:|---:|---|
| v1_fix1.zip | 10537802 | 321 | db414716be369d046b7337c17f58e4c795a024515e8110424e52365817e91321 |
| v2_fix1.zip | 10678698 | 335 | 8c2578b92187728532cd12cbe0a09e1f23f243fa76fb0513a4c260efceb46e30 |

VM 存放位置：`/home/eda/kwt_vm_20261101/releases/20261101_fix1`。实际工作副本和 flow 已就位，不需要重新解压覆盖。每个包根目录的 MANIFEST.json 核对当前包全部文件；work 内旧 manifest/报告是冻结来源的历史记录。

```bash
cd /home/eda/kwt_vm_20261101
make -C flow check       # 检查已完成证据
make -C flow -j2 all     # 重跑两版，旧结果会归档
```

`results/<版本>/sta_slow`、`sta_fast` 是修复前基线，保留其中的违例；最终结果看 `sta_eco_slow`、`sta_eco_fast`、`gate_eco_slow`、`gate_eco_fast` 与 `summary.json`。

## 赛用服务器（留在个人工作目录）

位置：`/storage2/2026contest/server5/s5_10usr/kwt_fixes_20261101/final`。这两个包含服务器侧 SMIC40 实现产物，未下载到本地或 VM。

| 包 | 字节数 | 文件数 | SHA-256 |
|---|---:|---:|---|
| v1_fix1_smic40.zip | 14464378 | 322 | 61874568c08c00057735fd238a9f94364018863778732ecb40972b1600ef9641 |
| v2_fix1_smic40.zip | 15130381 | 324 | 4bd53c7c4b823ee3811569f854f282d59d75964cf6daada40373536ee7dc4e82 |

两类包所含工艺实现不同，哈希不应相同。服务器清单核验见过程目录 `38_server_packages_final.png`。

## 验证边界

服务器完整核心 SS/FF 与 dot64 报告约束无违例，各版本 layer-0 完整核 SDF 通过。VM 完整加速器 RTL 功能回归通过，dot64 双角 STA 和四组 32/32 SDF 通过。VM SDF 仅把负检查限收紧为零以匹配库模型，原 SDF、原 Liberty STA 与差异审计均保留。

未完成完整 E203 CPU/语音模型验收和物理签核；VM 未找到赛用 SRAM timing 库，不能替代服务器完整宏时序。原冻结 `../20261101_v2/v1.zip` 与 `v2.zip` 未改变。


工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。
