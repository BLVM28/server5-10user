# 发布核验

verification.json 汇总精度、功能、时序、功耗和软件接口的验收范围；source_manifest.json 绑定当前源码、README、向量与五个分发包的逐文件哈希。前者不包含自身/后者哈希，避免循环依赖。

本地生成完五个包后运行 delivery.py index；服务器同样重建包并运行 delivery.py check。必须以相同源码/向量产生相同成员和包哈希。服务器额外的 .installed.json 仅用于安全更新旧文件，不包含登录凭证。
