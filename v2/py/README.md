# v2 PC 数值工具与回归入口

| 文件 | 输入 → 输出 | 使用边界 |
|---|---|---|
| numeric_model.py | 编码 X/W/b → int64 软件累加、RNE、int16 Y、饱和计数 | 独立整数金模；RTL 必须逐位相同；不用 TensorFlow |
| export_weights.py | 指定 best_weights → 12 套 Dense1 W/b NPZ + format.json | 检查 checkpoint SHA 和 shape；不训练、不改原权重 |
| make_vectors.py | 现有参数 + 测试数据 → ../vec/*.hex | 会写固定向量目录；平时仿真不需要运行 |
| capture_activations.py | 原模型 + smoke/真实 WAV manifest → report.json、首样本 12 层 RTL HEX | 统计全部样本但只导出首样本；split 合法性需独立确认 |
| run_xsim.py | RTL/TB/HEX → Windows Vivado XSim build 日志 | 退出码及 ALL PASS 双重检查；默认 Vivado 2023.2 |
| run_linux.py | 相同材料 → VCS 或 Xcelium 日志 | --sim vcs/xrun；完整核功能，不是 CPU 或 STA |
| run_foundry_server.py / run_binding_server.py | 服务器真实宏/公共头 + 本方核 → 特定验证 | 有固定工作目录断言，属于早期专用入口；不用来自动改正式平台 |
| package_release.py | 源码和指定历史 build → dist ZIP | 历史打包器依赖旧 build，归档后需先恢复；当前正式包见 releases |

常用命令和真实音频注意事项见 [调试导读](../../02_项目导读/03_调试与E203接入.md)。只读已有 HEX 的 RTL 回归无需 TensorFlow；模型截取使用保留的 tf24_env，不能随意移动该环境。run_linux.py 首部“Xcelium 未本地验证”是初建时注释，当前 VM 实测结果以 fix1 报告为准；本轮保持发布源码字节，不据旧注释否认新证据。

工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。

[返回工作区首页](../../README.md)
