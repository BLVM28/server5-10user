# 共用服务器资料

`libraries/` 是个人工作区已有库的副本，供 DC/PT/VCS 使用；原公共库没有修改。`library_selection.json` 指向本目录库和只读 SRAM 源。原始工艺库/标准单元模型/映射网表只留服务器，不放入本地公开仓库。

`migration_20261102.json`：旧路径→新路径及上传包校验。`verification_20261102.json`：最终功能/时序/门级证据复核。`jobs_20261102.json`、`parallel_jobs_20261102.json`：实际命令、返回码、耗时。`serial_gate_superseded.txt`：最初串行门级运行未计入最终 PASS 的说明。`rebuild_comparison.json`：重新综合的网表代码是否与 fix1 相同；只去除空行、行首尾空白和整行注释，保留代码内容。

通过标准：功能要求完整计数，门级还要求 SDF 错误/警告零；时序要求 SS/FF 的 max/min 非负且 reported constraint 无违例。SoC/官方评测缺口单独列出，不会随这几个 PASS 自动消失。
