# 软件模型、回归与证据处理

[numeric_model.py](numeric_model.py) 和 [export_weights.py](export_weights.py) 逐字节复用 v2 的整数金模和参数转换脚本。前者从 X/W/b 独立计算 40 位累加、最近偶数舍入后的 Y 与饱和数，后者用 checkpoint 名称、形状和 SHA 校验并导出 12 层 W/b。传给导出器的新输出目录应和冻结 vec 分开。

在装有 NumPy 的本地环境用 `python py/check_numeric.py` 重算 14 组共 168 个完整矩阵。它从物理 HEX 还原输入，逐元素比较累加和、Y，并核对饱和计数。重新生成的仅是结果摘要。[整数对照](../results/numeric.json)

[codec.py](codec.py) 是无损输出存储格式的独立 Python 参考。输入为按行展平的 25,344 个 int16，encode 返回物理槽和模式直方图，decode 恢复原值。[audit_codec.py](audit_codec.py) 用 GCC 编译交付的 C 解码器，对 14 套固定激活的 12 层在两种物理半字序下逐位对照，并把 DUT 导出的 12 张内存直接送入 C 和 Python。[软件证据](../results/codec.json)

[run_xsim.py](run_xsim.py) 默认用 Vivado 2023.2、当前 rtl.f 和固定 v2 向量，检查退出码及 ALL PASS。[baseline.py](baseline.py) 在 build/v31_reference 隔离复跑 v3.1 原始 RTL，只添加 NICE 计时观察。[summarize.py](summarize.py) 验证实际测试文件、RTL、向量和日志 SHA 后汇总 12 层配对周期。[本地复现步骤](../history/README.md)

[assets.py](assets.py) 按已冻结的 vector_manifest.json 恢复 952 个运行文件，并逐成员校验分类包。[delivery.py](delivery.py) 制作只含版本自有材料的上传包，服务器只在个人 home/v4 内写入、核对清单，检测独立改动后拒绝覆盖。
