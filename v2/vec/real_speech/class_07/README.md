# class_07：RTL 输入与独立期望

层号 0—11 对应 manifest 样本 ID：`[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7]`。

`layerNN_x/w/b.hex` 是 DUT 的实际输入；`y.hex` 是输出比较值，`acc.hex` 是完整 40 位累加比较值，二者不作为 DUT 输出驱动。`matrix_sat.hex` 是各层预期饱和计数。低索引 int16 放入 32 位字的低半字。所有导出矩阵经过原 numeric_model.py 独立核对。

每层 X 3168 字、W 8192 字、b 256 字、Y 12672 字、acc 25344 个。上层 report.json 给出浮点误差；rtl_results.json 记录实际仿真。
