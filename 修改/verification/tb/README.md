# 测试平台

`tb_icb_registered` 检查在途/反压/复位/应答；`tb_mul16_pipeline` 检查16位有符号乘法；`tb_kwt_stream_dot` 检查64项点积、偏置、舍入和饱和。以上从 r8 保留。

`tb_raw_writer` 新增完整数值域的 sy 舍入与直接写回检查。`tb_kwt_streams` 已换为新格式，检查 12 层结果、每字恰写一次、未用尾区不写、完整累加、错误退出、响应保持和复位。旧格式0x10004被拒绝；最后一行的四个错误位置包括整矩阵最后一字。`kwt_sram_sim` 是内部 SRAM 功能替身，不能用于工艺 STA。
