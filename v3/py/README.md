# Python · 本地仿真、结果审计、资产整理

| 文件 | 输入 | 输出 / 为什么使用 |
|---|---|---|
| [run_xsim.py](run_xsim.py) | v3 RTL/TB、v2 固定整数向量、Vivado XSim | 复用 v2 的 Windows 工具启动器，把实际编译根切换到 v3；每次在 `build/<tag>/` 保存日志和源文件指纹 |
| [summarize.py](summarize.py) | final_base、final_worst 运行目录与 v2 的同名 worst 记录 | 验证完整计数、向量/源文件 SHA 和 14 次矩阵结果，从中取前 12 层配对比较，生成 `results/functional.json` |
| [assets.py](assets.py) | [vector_manifest.json](vector_manifest.json) 固定的 952 个数据指纹 | `vectors` 从 v2 恢复缺少的数据，校验已有文件；`package` 生成五个分类 ZIP 并从归档逐成员复核 |

在 Windows 克隆库根目录执行以下命令。默认 Vivado bin 为 `D:/vivado/Vivado/2023.2/bin`，其它安装位置通过 `--bin` 指定。

```sh
python v3/py/run_xsim.py --tag final_base
python v3/py/run_xsim.py --tag final_worst --tops tb_kwt_system --vectors v2/vec/real_speech/worst
python v3/py/summarize.py
python v3/py/assets.py package
```

v3 的比较依赖 v2 已验证的输入与期望值；若已有 golden 与指纹不符，恢复程序会报出文件名并停止。源码变化后请产生新仿真，再运行 summarize。旧的 PASS 只覆盖对应的源码指纹。
