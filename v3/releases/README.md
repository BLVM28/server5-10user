# 交付身份

[source_manifest.json](source_manifest.json) 列出本次 v3 活动工程的文件指纹，供本地与服务器逐项比对。分类包的成员清单和压缩包指纹由 [packages/manifest.json](../packages/manifest.json) 给出。正式安装检查另见 [服务器验收记录](../SERVER_RESULTS.md)。

这里用于追溯团队交付快照。后续改版先改源码并重新验证，再生成新的交付身份，原始鉴定数据仍可通过 Git 提交和服务器固定实现追查。v1/v2 已冻结的 release 使用各自原包。
