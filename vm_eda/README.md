> 2026-11-01 整理更新：本目录原有技术说明保留。最新完成度以工作区根 README 和 fix1 报告为准；本轮只整理本地资料，不自动同步新文档到 VM/服务器。 results 中保留摘要与关键 STA，完整原始网表/SDF/日志归档到 99_归档；VM 实际运行目录不受本地整理影响。
> [工作区首页](../README.md) · [调试导读](../02_项目导读/03_调试与E203接入.md)

# RHEL7 虚拟机独立验证流程

工作目录固定为 `/home/eda/kwt_vm_20261101`，用户 `eda`。所有输出仅写此目录；`/opt/eda2` 的工具、库和许可证文件只读。密码不放进脚本。

原始包保存在 `baseline/v1`、`baseline/v2`，验证工作副本在 `work/v1`、`work/v2`。原包逐文件 SHA-256 已核对。脚本位于 `flow`，结果位于 `results`，失败尝试保留在 `results/<version>/history`。

工具以实际 banner 为准：Xcelium 20.03-s001、Genus 21.10-p002_1、Tempus 21.12-s107_1。Genus 安装目录虽然叫 GENUS212，不能据此写成版本 21.2。

```bash
cd /home/eda/kwt_vm_20261101
source flow/env.sh
python3 flow/run_regression.py v1
python3 flow/run_regression.py v2
python3 flow/run_timing.py v1
python3 flow/run_timing.py v2
python3 flow/close_timing.py v1
python3 flow/close_timing.py v2
python3 flow/audit_sdf.py v1
python3 flow/audit_sdf.py v2
```

从头跑全部检查用 `make -C flow -j2 all`；只核对现有结果用 `make -C flow check`。脚本在再运行时归档旧结果。VM 门级仿真使用将负 timing limit 收紧为零的兼容 SDF，原始 SDF 和 Liberty STA 保留，差异由 `audit_sdf.py` 核查，详见报告。

功能仿真覆盖完整 NICE 加速器 RTL，使用已有的独立 golden 向量和行为 SRAM。虚拟机的映射时序实验使用 GPDK045 basicCells 的 slow（0.9 V / 125 °C）及 fast（1.1 V / 0 °C）库，只针对没有 SRAM 宏依赖的 `kwt_dot64`。SMIC40 与 GPDK045 的面积和频率不能直接横向对比。

在已检查的虚拟机安装目录中没有发现赛用 RAMSP128X16/RAMSP1024X16 timing 库。因此此流程没有把存储器换成无时序黑盒后声称完整核心通过。完整核心的真实 SRAM 时序修复仍由服务器原库验证。

`execution_completed` 只表示命令执行完成；setup、hold/removal、transition、capacitance、覆盖情况和 SDF 注释必须分别检查。没有 false path、multicycle path、禁用 timing check 或修改 golden 期望值。

最终数值、修复入口和未解决事项见同目录 `REPORT.md`。


工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。
