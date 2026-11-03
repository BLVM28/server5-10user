# 本地回归、数据与发布脚本

- [run_xsim.py](run_xsim.py) 读取本版 rtl.f、七套 TB 和 v2 固定输入，调用 Vivado 2023.2。默认 bin 位于 D:/vivado/Vivado/2023.2/bin，可传 --bin。从版本根目录运行 `python py/run_xsim.py --tag final_base`。
- [compare.py](compare.py) 核对基线、两种 v3.1 试验的 SHA、实际 PASS 标记、12 层计数及写回数，生成 results/functional.json。试验名称、激励与复现步骤在 [试验记录](../history/README.md)。
- [assets.py](assets.py) 用 vector_manifest.json 从同仓 v2 恢复并核验 952 个固定数据文件。package 生成五个确定性 ZIP，并逐成员复检。命令为 `python py/assets.py vectors` 或 `python py/assets.py package`。
- [delivery.py](delivery.py) 将版本自身可公开文件打成小上传包，服务器仅在个人 home/v3.1 内逐文件核验和更新。服务器已有独立改动会被拒绝覆盖。
