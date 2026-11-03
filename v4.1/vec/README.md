# 测试数据

[fast](fast/README.md) 包含 14 套 Block8 输入和独立期望输出，软件重新计算而成。原始语音/合成 X、W、b 的字节取自 [v2/vec](../../v2/vec/README.md)。既有格式在 5 号机直接读同一份 v2 金值。

仓库保存五个包中的 vectors.zip、冻结 SHA 和生成脚本。新克隆可从仓库根运行 `python v4.1/py/scalar_vectors.py` 或将 vectors.zip 解压到 v4.1，得到与发布记录同字节的文件。在 5 号机用 `make vectors` 做同样的还原与校验。
