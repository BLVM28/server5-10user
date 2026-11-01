# GitHub 迁移完成记录

日期：2026-11-02。仓库：[BLVM28/server5-10user](https://github.com/BLVM28/server5-10user)，public；按用户选择开放查看、Fork 和 PR，直接协作者稍后添加。

## 本机新工作区

`C:/Users/lenovo/Desktop/server5-10user`。这是从 GitHub 实际 clone 后拉取完整 LFS 的目录，origin 指向上述仓库。以后在 Codex/编辑器里选择这个目录；本地修改需要 commit/push，团队更新需要 pull。

## 完整性和范围

- 来源：22435 个文件，1947408393 B；上传副本逐文件 SHA 一致。
- 首个导入提交：`cd2bdc5bc51f7ea951f681fdc15a9ef9f54f4581`，保存来源全部原始文件；4 个大文件使用 Git LFS。
- 新增协作说明、忽略未来缓存的规则和来源清单；修复 README/AGENT/模型调试命令中当前目录更名后的路径。RTL、TB、数值脚本、固定向量、模型及正式 ZIP 字节未改。
- 推送后从远程新克隆：22442 个已跟踪文件（含新增元数据）逐文件 SHA 一致；4 个 LFS 对象检验通过，工作树干净。详细结果见 `_同步记录/clone_verification.json`；它记录的是加入本完成记录之前的已验证提交。
- 使用 Git 凭据管理器中的现有登录完成，账户密码和令牌未写入项目。
- 本机 Git 的旧代理不可用，已在新仓库本地配置直连覆盖；机器连接设置不属于提交内容。

## 使用入口

新仓库根 [GitHub协作说明.md](GitHub协作说明.md) 给出 clone、分支、PR、同步和验证命令。复制来的 Windows Python 环境仍含原机器路径，在其他机器提取模型需要重建本地 Python3.8 环境；RTL 固定向量回归不需要 TensorFlow。

本轮完成的是 GitHub 发布与克隆，不增加真实 E203 CPU/语音精度/EDA 已通过的范围。当前提交用 `git log -1` 获取。
