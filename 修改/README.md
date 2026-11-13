# r8 合规修订候选 · 2026-11-13

**原 `final` 不能按“全部符合赛题的最终版”直接提交。** 最新答复第 11 问禁止原输出压缩，第 16 问禁止原 P6 装载旁路。本目录已修复加速器输出和配套模型/接口/测试；P6 平台旁路、整机时序、官方任务入口仍待完成。此前把 r8 称为最终提交版的结论不充分，以本次审查为准。

原 `final/` 和桌面 `提交材料（部分）/` 均保留。本目录可单独复制。位于仓库根目录的 `修改/` 是实体目录；外层原工作区中的同名入口指向同一目录。本目录按用户要求作为独立提交同步到 GitHub `main`；服务器未修改。原审查的已修复项和未完成项保持不变。

| 位置 | 内容与使用范围 |
|---|---|
| [reports/01_严格核查与整改.md](reports/01_严格核查与整改.md) | 每项要求、证据、已修复/未完成、责任和提交缺项，先读此文件 |
| [rtl/](rtl/README.md)、`rtl.f` | 14 个活动 RTL 文件，顶层仍是 `kwt_nice_core`；128 MAC、72 SRAM 和输入读取保持 r8 |
| [interface/](interface/README.md) | 新描述符版本 `0x10005`、输出矩阵布局、C 入口与 NICE 插槽包装 |
| [model/](model/README.md) | 原数值规则、新输出布局、输入/参考生成、完整矩阵读取 |
| [verification/](verification/README.md) | 单元、12 层、协议异常、C/Python 一致性测试及 Makefile |
| [reports/02_功能测试与数值边界.md](reports/02_功能测试与数值边界.md) | 本轮真实测试和仍未验证的范围 |
| [reports/03_任务3整改交接.md](reports/03_任务3整改交接.md) | P6 旁路位置、驱动与 TB 更新、综合只列问题 |
| [依据/](依据/README.md) | 赛题/答复、原提交包 PDF 的文字提取、原版身份、历史结果、P6 违规接线证据；**不是活动实现** |

## 运行

安装 Make、GCC/G++、Icarus、Verilator、Python 3 + NumPy。在本目录执行：

```bash
make -C verification check
make -C verification stress
sha256sum --quiet -c SHA256SUMS.txt
```

`check` 覆盖组件、写回、C 编解码、软件参考和矩阵。`stress` 覆盖同拍应答与随机等待/半字交换。也可分别 `make -C verification compile`、`run`、`clean`。工具版本和本机特殊 Python 入口见测试报告。

成功只说明报告所列的 RTL 功能验证通过；没有整机时序/装载合规验收。修改版不得引用原 r8 的 STA、面积、功耗、周期作为自身实测值。旧格式固件需要重新编译，旧 `firmware.hex` 不能使用。

`verification/build/`及Python缓存属于本机编译中间件，已单独放置并由.gitignore排除，不在SHA256SUMS交付清单内。复制提交代码时可不携带这些目录。
