# 生成、软件验证与交付

| 文件 | 作用 |
|---|---|
| scalar_vectors.py | Python 3.6 标准库独立重建 1,400 个向量；校验冻结输入哈希，服务器无需 NumPy |
| make_vectors43.py、streams43.py | NumPy 版本四路编码与金值；逐层断言累加和解码值等于 v4.2 |
| vector_manifest.json | 既有 v2 原始输入/参数的冻结哈希清单 |
| stream_manifest.json | 本版 14 组×100 个 hex 的字节哈希清单 |
| rice.py、numeric_model.py | 原有定点/舍入模型；本版保持与 v4.2 相同的数学 |
| block8.py | 为兼容原始数据仅复用其中读 hex/int16 工具；本版不采用 Block8 数据格式 |
| profile42.json、profile_header.py | 33 个训练 WAV 标定得到的冻结参数，生成相同 C profile |
| qualify_speech.py | TF2.4 加载实际 KWT-1，核对 162 个 checkpoint 张量、上游预处理和逐层 Dense1 |
| precision_metrics.py、test_precision_metrics.py | 按原文实现NRMSE参考RMS下限，单样本和聚合共用；13项解析边界测试 |
| run_xsim.py | 本地编译/运行和严格完整 PASS 计数，支持独立目录、参数和四种端点 |
| audit_driver.py | C 与 Python 两种字序编码逐字对照，另解码 12 层真实 RTL RAM 导出 |
| rv32_verify.py | RV32IMAC 交叉编译，检查 custom3 的实际指令字段 |
| check_wrapper.py | 用公共定义文件编译并链接 E203 wrapper，验证实际端口/参数连接；不等同CPU执行 |
| local_evidence.py | 校验完整本地日志、源码和 600 样本后公开结果，不推断服务器通过 |
| assets.py | 五类确定性 ZIP、成员哈希与回读校验 |
| delivery.py | 本地打包与发布清单；服务器受路径和旧版本哈希保护的安装、过时文件归档 |

在克隆库根目录运行 `python -B v4.3/py/scalar_vectors.py` 可重建向量。它需要同库既有 v2/vec 原始数据。语音重测：
```powershell
python -B v2/py/run_model_python.py v4.3/py/qualify_speech.py --data datasets/speech_commands_v0.02 --out v4.3/build/speech
```
这项复测需要本地保留的 Python3.8/TF2.4 和验证音频；训练参数不在测试阶段改变。C/RV32 的实际命令及编译器身份见 [接口说明](../integration/README.md) 与结果 JSON。
