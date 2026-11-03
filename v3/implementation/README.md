# 映射实现 · 服务器私有目录

`qualified200/` 对应经过 200 MHz 鉴定的 v3 完整核心。`rebuilt/` 是 `make synth` 成功后从当前源代码产生的实现，用 `NETLIST=rebuilt` 显式选择。版本根 `make timing` 默认检查 qualified200。

每套实现的 manifest.json 记录 RTL 和映射文件的 SHA，synth_kwt_nice_core 下保存映射 Verilog、DDC、面积、鉴定和结构修复记录。修改 RTL 后，固定网表哈希不再对应，日常流程会阻止把旧结果当作新时序。工艺相关产物只留服务器；本地与 GitHub 保存目录解释和可公开的数值摘要。[冻结实现](qualified200/README.md)
