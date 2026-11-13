# 功能验证与手动命令

从本包根目录执行 `make -C verification help`。依赖 Make、Icarus、Verilator、GCC/G++、Python3+NumPy。

| 命令 | 实际内容 |
|---|---|
| `make -C verification check` | units + writer + codec + model + matrix，遇到失败非零退出 |
| `make -C verification compile` | 编译完整 NICE DUT 与独立 SRAM 功能模型 |
| `make -C verification run` | 编译后跑 12 层、错误/复位/连续任务及输入保护 |
| `make -C verification stress` | MODE=2 同拍应答；MODE=1 随机等待且半字交换，两次完整回归 |
| `make -C verification writer` | 6 个 sy × 全 65,536 个 signed16 输入；真实写回 6 组、同拍应答和反压 |
| `make -C verification codec` | 用 GCC+UBSan 核对 C/Python 的 12 层 X/W 编码、Y 读取及两个字序 |
| `make -C verification model` | 重新计算软件黄金结果并比对固定 SHA/文件 |
| `make -C verification clean` | 仅允许删除本目录默认 build；不会删向量和报告 |

变量：`BUS_MODE=0/1/2`、`PACK=1/0`、`JOBS=4`、`PERIOD=6.666667`、`PYTHON=python3`。`PERIOD` 是功能仿真波形时钟，不代表实际工艺频率能力。通过标记由 TB 内的数值/协议断言支撑，不能只改日志字符串。

本机 WSL 未配置 NumPy，复测使用已安装 NumPy 的 Windows Python：

```bash
make -C verification check PYTHON=/mnt/c/Users/lenovo/AppData/Local/Programs/Python/Python312/python.exe
```

正常 Linux/EDA 环境装好 NumPy 后使用默认 python3 即可。完整结果在 `reports/`，编译中间件在 `verification/build/`。

**测试层级**：TB 直接连接 NICE 顶层和 SRAM 功能模型，用 `$readmemh` 建立输入，只用于组件/加速器功能。这不是 E203 整机加载，更不能把此处 NICE_TIME 作为赛题含装载/CPU调度的吞吐。正式整机需要任务3修复 System Bus 装载路径。
