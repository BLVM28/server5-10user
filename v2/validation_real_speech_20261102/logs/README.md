# 验证原始日志

`capture_attempt1_name_audit.log` 是新增权重审计器首次失败记录：Keras 的变量显示名 `dense_5/kernel` 没有 checkpoint 中的完整父作用域。检查尚未进入语音测试。后续改为源码对象与 checkpoint 语义路径的明确映射，并核对所有模型权重，不改权重、不放宽逐位比较。

`checkpoint_tensors.txt` 和 `inspect_checkpoint.py` 记录公开 checkpoint 的实际键名/形状，解释旧版 TF/TFA 的 GELU 对象引用告警。最终是否全部权重匹配看上层 `capture.log` 和 `report.json`。

`capture_attempt2_report_path.log` 记录第二次在完成 600 例计算后，报告源码 SHA 的路径转换报错。Python3.8 将相对启动脚本保留为相对 `__file__`；将它先 resolve 后完整重跑，不从失败日志猜测最终数值。

`real_speech_components*` / `real_speech_mul*` 是基础算术、ICB、重叠调度和乘法流水回归。`class_XX_*` / `worst_*` 是每套真实输入的 XSim 编译、展开、运行和 JSON 清单；生成的 TB 仅替换默认向量路径，保留所有原始检查。

这里保留机器核对所需细节，初次阅读只需上层 README 和汇总 JSON。
