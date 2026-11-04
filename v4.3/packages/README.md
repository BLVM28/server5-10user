# 分开交付的五个包

rtl.zip 是正式 15 文件和清单；tb.zip 是当前测试台及 Apache 公共控制器依赖；makefile.zip 是操作入口和服务器手册；flow.zip 是验证脚本、C 接口、README、公开结果和版本说明；vectors.zip 是 1,400 个实际向量及生成所需哈希/参数。

manifest.json 为每包及每个成员提供 SHA-256。所有包按固定成员顺序和时间戳生成并回读核对。使用时在同一 v4.3 根目录解压，先读 SERVER_GUIDE.md。服务器可 make package 重建；本地用 python -B v4.3/py/assets.py。它们不包含商业工具、工艺库、映射网表或音频。
