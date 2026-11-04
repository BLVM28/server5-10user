# 测试台与通过条件

| 测试文件 | 用途 |
|---|---|
| tb_kwt_streams.sv | 主计分板，默认 MODE=0，一拍、单项同步 RAM 行为端点 |
| tb_kwt_wait.sv | MODE=1，沿用 v4.2 的随机就绪及 0–7 拍延迟、相同种子；压力吞吐单独统计 |
| tb_kwt_zero.sv | MODE=2，组合立即应答，检查主机同时命令/响应的边界 |
| tb_kwt_public_sram.sv | MODE=3，实例化未经改动的公共 sirv_sram_icb_ctrl、其旁路队列和门控时钟；RAM 用一拍功能数组 |
| tb_kwt_v42_reference.sv | 同公共端点下编译上一版 RTL 或上一版网表，作公平吞吐及功耗参照；不会混编两版同名模块 |
| tb_kwt_stream_dot.sv | 64 组独立 64 位点积金值，对齐输入全范围、连续/有气泡点积、清空、正负饱和与偶数舍入 |
| kwt_sram_sim.sv | 本地 SRAM 功能辅助；服务器使用真实公共宏仿真模型 |

主测试的 29 场景包含 12 层完整矩阵、描述符/层号/地址错误、读写总线错误、在装 X/装 W/计算/写回时复位、响应反压和再次运行。另有 25 个四路字数、缺字/多字、元数据/尾写错误和非法最小步长保护。每个子流都被检查，不能仅凭状态返回 0 判断通过。

RTL 模式逐一对照所有有效 MAC 的 40 位和；内存端逐字核对 Y 码流，独立解码后逐元素核对整张矩阵，还检查未用槽和邻接 canary、读写事务数。门级模式去掉内部探针，保留真实引脚上的整张输出、解码和事务检查。

`+LAYER=0` 只跑该层完整任务；`+DUMP_RAM` 导出真实输出，供 C 解码对照；`+POWER` 从接受指令到 NICE 响应有效期间记录 DUT VCD，不包含预加载。门级额外使用 `KWT_GATE`、`KWT_PERIOD_NS=6.666667` 和 SS/FF 的相应 SDF。SDF 注释必须 warnings=errors=0，矩阵必须通过，不能只测试注释成功。

本地（克隆库根目录）：
```powershell
python -B v4.3/py/run_xsim.py --tops tb_kwt_public_sram --tag public_manual
python -B v4.3/py/run_xsim.py --tops tb_kwt_stream_dot --tag dot_manual
```
默认 Vivado 2023.2 安装于 D:/vivado，可用 `--bin` 覆盖。全回归和 EDA 命令见 [服务器手册](../SERVER_GUIDE.md)。这些测试不是完整 E203 CPU 固件验收。
