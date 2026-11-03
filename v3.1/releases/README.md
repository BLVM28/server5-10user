# 版本交付索引

本目录的 [source_manifest.json](source_manifest.json) 登记本地和服务器验收的版本源文件、数据及分类包 SHA。清单不登记自身、私有实现和易变化的运行产物。服务器另有 .installed.json 记每次上传文件的哈希，安装器会发现独立编辑的服务器文件并停止覆盖。使用 [操作手册](../SERVER_GUIDE.md) 验证日常入口。[分类包](../packages/README.md)

[verification.json](verification.json) 记录实际七套基础、13 组语音激活、12 层周期、映射哈希及双角 SDF 短探针。服务器 make acceptance 会把它与本次运行记录逐字段核对。
