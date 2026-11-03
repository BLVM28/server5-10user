# 5 号服务器 · v4 验收记录（2026-11-03）

工作目录为 `/storage2/2026contest/server5/s5_10usr/v4`。源与分类包在本地和服务器按 SHA 对照。工艺库只读；网表、SDF 和原始工具报告保存在服务器个人目录。

正式入口已实际打印 `BASIC CHECK PASS` 和 `EXTENDED ACCEPT PASS`。验收复核了 35 套回归、两个角的门级层记录及 150 MHz 吞吐。日常结果见 `reports/release_check.log`；首发门级 SDF、原始运行日志、注释摘要及对应哈希另保存在 `reports/published_gate_150.zip`。

| 命令 / 工具 | 范围与已测结果 | 服务器记录 |
|---|---|---|
| `make clean`、`make compile`、`make regress JOBS=2` / VCS | 9 个基础套件，加 13 组语音激活的原始与紧凑两种总线输出，**35/35 通过**。每次系统套件均核对 25,344 个 Y 和量化前的 acc40，另含故障恢复重测 | `reports/final_function.log` 与 `build/manual/runs/` |
| `make fast_return` / VCS | 合成矩阵覆盖四种编码。11,624 个读、9,088 个写都在接受命令的同一拍返回应答；逐笔地址、数据、标签、次数通过 | `reports/fast_return.log` 与 `build/fast_return/run/` |
| `make check` / VCS + PrimeTime | 基础功能、150 MHz 全加速器双角时序和源签名均通过。SS setup/hold +0.866657/+0.421749 ns，FF +4.011108/+0.200006 ns，两个角零报告违例 | `reports/check.log`、`build/manual/timing/` |
| `make paired` / VCS | 同一批 12 次冷任务，紧凑模式 1,568,392 拍，原始模式 2,010,320 拍。与独立本地 XSim 逐层一致 | `reports/check.log` 与 [逐层对照](results/functional.json) |
| `make waves` / VCS | 原始模式 29/29，生成顶层接口 VCD，可用 `make verdi` 打开 | `build/manual/runs/waves/tb_kwt_system/waves.vcd` |
| DC 映射 / PT 扫频 | 修订版改一只反相器，按库比对布尔函数及引脚，再逐语句检查其余映射不变。150/160 MHz 两角通过，180/200 MHz 慢角失败。总面积 0.319784 mm² | `reports/final_map.log`、`reports/final_eco.log`、[八个测量点](results/ppa.json) |
| `make gate_sample` / VCS + SDF | worst 第 0 层在 SS 最大、FF 最小延迟各跑一张完整矩阵。两角都实测 **6,079 写 / 17,703 笔事务**，解码后 **25,344/25,344** 元素分别一致，SDF 注释 0 错误、0 警告 | `reports/gate_final.log`、`build/gate_sample/sample.json` 与[发布记录](results/gate.json) |

冻结实现为 `implementation/rebuilt/synth_kwt_nice_core/`，mapped.v 的 SHA-256 为 `d311ca7bf036707b58de7d5543bd4bfcc9955c72fa3129cf95892eb6ab66fe58`。本地与服务器的实现身份由 [公开工艺数据](results/ppa.json) 固定。门级执行检查引脚处所得的整个 Y，RTL 仿真另可观测未导入生产网表的 40 位中间结果。

## 准确度和性能各在测什么

门级样本覆盖两角各一层。本轮 12 层的完整覆盖来自 RTL 回归。重新执行门级样本后，SDF 和运行日志会含新日期；验收按当前文件校验哈希，并与冻结记录比较角、层、事务、写数和网表身份。

- 单个输入集合有 12 次计分任务，分别使用 layer 0–11 的参数。类别集取自 12 个代表性样本；worst 各层可以来自不同样本。每一任务重新搬全部输入、W、b，并等所有写应答。类别合计 144 次，加权吞吐 1,051.22 tasks/s；无损紧凑输出的合成 base 为 949.56 tasks/s。[类别明细](results/speech.json)
- 本地 XSim 与服务器 VCS 独立核对同一金模。本地用原始整数实现重算 168 个完整矩阵和饱和计数；C/Python 解码结果逐元素一致。交付的 RV32 驱动已交叉编译和反汇编。官方 600 条数值评测、E203 启动与共享 RAM 的固件调度、片上真实消费时间及 SoC 功耗均需要正式平台。[软件整数对照](results/numeric.json) · [解码证据](results/codec.json) · [驱动记录](results/driver.json)

## 怎样在终端复核

```sh
cd /storage2/2026contest/server5/s5_10usr/v4
make report              # 快速查看当前功能与时序的有效记录
make paired              # 重跑同批 12 层，打印两种格式的 tasks/s
make acceptance          # 对现存扩展回归、SDF、波形、网表和发布数据交叉核验
```

如果先运行 `make clean`，基础与扩展仿真的旧记录会被归档。需要重建全面验收时依次运行 `make compile`、`make regress JOBS=2`、`make waves`、`make timing`、`make fast_return`、`make gate_sample`、`make acceptance`。只重新跑基础检查可用 `make check`。[日常手册](SERVER_GUIDE.md)
