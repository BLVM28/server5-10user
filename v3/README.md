# v3 · E203 八路 Dense1 加速器

本版本完成 `Y[99,256] = X[99,64] × W[64,256] + b[256]`。E203 发送任务描述符，加速器写回矩阵并返回完成状态。每个编码器层用自己的 X、W 和 b 发一个任务；分类头在完整模型的软件流程中产生语音标签。本科三项必做分别覆盖点积与数值处理、Dense1、E203 集成和综合评估。[架构依据](ARCHITECTURE.md)

## 和 v2 相比，改进在哪里

| 问题 | v2 | v3 | 实际影响 |
|---|---|---|---|
| 点积反馈 | 每个乘积立即并入一个 40 位二进制累加器 | 14、13、13 位三段并行更新，跨段进位留到以后处理 | 最后一项后增加两拍排空；结果、舍入及饱和按同一整数黄金值核对 |
| 八路汇合 | 每路 dot 都提供 busy，父模块只接收握手和结果 | 独立 dot 的 busy 有效，mac8 内部将未使用的 busy 专门化 | 消除首轮映射的八个空载驱动 |
| 工艺实现 | v2 fix1 在 150 MHz 通过，慢角 setup +0.000262 ns | 按 v3 网表报告提高一个反相器的驱动能力，调整四个延迟单元，复查完整核心 | 200 MHz 双角通过，SS setup +0.000194 ns，总面积比 v2 +1.06% |
| 同一批 12 个任务 | 4,081,340 个核心周期 | 4,157,612 个核心周期 | 同频周期 +1.87%；150 MHz 下 441.0 → 432.9 task/s；v3 200 MHz 折算 577.3 task/s |

**八列分组沿用 v2。** 同一拍读一个 X，送给八个乘加器，各乘以一个 W。`64×8` 权重面板装入后服务 99 行，每行的 8 个 int16 结果占四个 32 位写事务。256 列分 32 组，4 路需 64 组，16 路需每拍 256 位权重。8 路是片内带宽、乘加器面积与任务周期之间的工程选择。X/W 精度均为 16 位，与并行度独立。8 个 RTL 源文件与 v2 逐字节相同，两处 RTL 差异在 dot64 和 mac8。[模块说明](rtl/README.md)

## 一个任务怎样完成

1. NICE 顶层接收自定义指令和描述符地址，经 ICB 读回 8 个描述符字，检查头部、层号、地址及重叠。
2. `linear_core` 将 6336 个 X 元素装进 7 个 SP1024×16，将当前 8 列权重装进 8 个 SP128×16。片内物理容量 16 KiB。SoC 共享存储预算另为 512 KiB。
3. 每拍向八路提交同一个 X 和八个 W。每路负责一个输出，接收 64 对操作数，累加偏置，仅在最后舍入、饱和为 int16。
4. 当前行写回时可计算下一行。同一权重面板完成 99 行后换组。最后一笔写应答收回后 NICE 才报告完成。系统 TB 对每个矩阵检查 24,296 个总线事务和 12,672 个写回字。

## 目录入口

| 路径 | 打开后可以解决什么问题 |
|---|---|
| [rtl](rtl/README.md) 和 [rtl.f](rtl.f) | 10 个硬件模块的职责、接口、连接顺序以及两处源代码改动 |
| [tb](tb/README.md) | 七套自检分别查什么，如何定位算术、进位、总线、恢复错误 |
| [vec](vec/README.md) | X/W/b 与 Y/acc 的区别、数据格式、12 类代表激活及 worst 的来源 |
| [py](py/README.md) | Windows 本地仿真、成对周期审计、校验并恢复向量、生成分类包 |
| [integration](integration/README.md) | E203 包装、驱动头、描述符和真正整机接入所需参数 |
| [server_eda](server_eda/README.md) 和 [Makefile](Makefile) | VCS、Verdi、DC、PrimeTime 的入口，固定映射时序与重新综合的区别 |
| [implementation](implementation/README.md) | 服务器保存的合格网表、哈希和应用范围 |
| [results](results/README.md) 和 [RESULTS.md](RESULTS.md) | v3 与 v2 的面积、频率、吞吐、原始日志与失败候选 |
| [reports](reports/README.md)、[build](build/README.md) | 本次服务器命令及清理前保留的证据、当前仿真产物 |
| [packages](packages/README.md)、[history](history/README.md)、[releases](releases/README.md) | 五个可解压的分类包、旧实验追溯、本次交付清单 |

## 开始使用

服务器进入 `/storage2/2026contest/server5/s5_10usr/v3`，执行 `make check` 跑七组基础功能和完整核心双角时序，执行 `make report` 重读结果。比赛 150 MHz 用 `make timing PERIOD=6.666667`。看波形先执行 `make waves`，然后执行 `make verdi`。[服务器操作手册](SERVER_GUIDE.md)

Windows 在克隆库根目录可执行 `python v3/py/assets.py package` 生成五个压缩包。需要本地仿真时执行 `python v3/py/run_xsim.py --tag final_base`，完整复现命令见 [py/README.md](py/README.md)。[本次服务器交付验收](SERVER_RESULTS.md)

**使用边界。** 200 MHz 是当前完整加速器网表的布局前 STA 测试点，SS 的建立余量只有 0.194 ps。180 MHz 有 +0.555749 ns 的慢角建立余量。赛题统一用 150 MHz；共享 SRAM 正式地址、固件及 E203 顶层时序仍需整机联调。

2026-11-03 工作记录：完成分段累加和五单元修复，建立逐目录导读、正式 v3 入口、冻结网表和分类交付包。
