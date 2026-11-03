# 发布身份

verification.json 记录最终网表身份、实测周期及验证范围。source_manifest.json 记录版本源、向量及五个压缩包的 SHA-256，服务器 `make acceptance` 和 `python3 -B py/delivery.py check` 分别验证实测与交付字节。
