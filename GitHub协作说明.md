# GitHub 协作与本地工作方式

远程仓库：https://github.com/BLVM28/server5-10user 。可公开查看、Fork、提交 PR；直接 push 需要被添加为协作者。团队账号确认后，由仓库 Settings → Collaborators 添加，接受邀请后生效。不要共用仓库所有者的登录凭据。

## 本机以后在哪个目录工作

本轮克隆目录：`C:/Users/lenovo/Desktop/server5-10user`。它是实际 Git checkout，origin 指向上面的仓库。原目录是上传来源；以后编辑、运行脚本和提交从新克隆目录开始。在 Codex/编辑器中选择这个文件夹作为项目。

云端保存已提交并 push 的版本；本地编辑不会自动出现在 GitHub，其他人的变更也需要 pull。

## 第一次获取完整工程

已安装 Git 与 Git LFS 后执行：

```bash
git lfs install
git clone --config core.autocrlf=false --config core.longpaths=true https://github.com/BLVM28/server5-10user.git
cd server5-10user
git lfs pull
git lfs fsck
```

本仓库按要求包含整个工作区：22435 个来源文件、约 1.95 GB（十进制），包括模型、原发布包、归档及 Windows Python/TF 运行环境。4 个大文件使用 LFS，路径见 `.gitattributes`；LFS 指针不能代替实际模型/动态库。优先使用 clone；网页 Download ZIP 的 LFS 内容处理可能不同。

来源逐文件哈希在 `_同步记录/source_manifest.json`；首个导入提交保留所有来源文件的原始字节。后续提交增加协作说明，并修复目录更名后的当前文档链接。后续新增生成缓存按 `.gitignore` 处理，已有跟踪文件仍然受版本管理。

## 有写权限的队友

```bash
git switch main
git pull --ff-only
git switch -c feature/your-change
# 修改与验证；只添加本次需要提交的文件
git status --short
git add v2/rtl/your_module.sv v2/tb/your_test.sv
git commit -m "说明具体改动和原因"
git push -u origin feature/your-change
```

上面的 your_module/your_test 是示例路径，需换为实际文件。然后在 GitHub 发起 PR，写清功能变化、测试命令和通过范围；合并后大家再 pull main。不要用 force push 覆盖队友历史。没有写权限的公众用户先 Fork，再从 Fork 分支发 PR。

## 当前项目的验证入口

- 先读根 README 和 `02_项目导读/`；当前开发主线是 v2，v1 为比较基线，正式 ZIP 在 releases。
- 本机 Windows RTL：`python v2/py/run_xsim.py --tag learn_arith --tops tb_kwt_arithmetic`，默认依赖已安装的 Vivado 2023.2。
- 私有 VM：`cd /home/eda/kwt_vm_20261101`，再 `make -C flow check`；本地 push 不会自动更新 VM 或竞赛服务器，需要按授权目录同步并核对哈希。
- 原项目目录已更名为 `03_过程与分析/`；历史日志/归档内的 `过程与分析/` 是当时路径。当前常用命令应使用新名。
- 被完整复制的 Windows 虚拟环境仍含原机器的绝对路径；clone 不会自动让它适配其他电脑或 Linux。需要模型提取时，用 Python3.8 在本机新建环境，按 `v2/requirements-tf24.txt` 安装；RTL HEX 回归不需要 TensorFlow。不要删除被跟踪的环境文件来“修复”安装，也不要在公共仓库写入访问凭据。

## 版本纪律

改 RTL 前核对 AGENT、implementation_spec 和数值金模；改位宽/舍入/布局/ABI 必须同步验证。保留失败与成功证据的范围，不把独立核 TB 当作真实 CPU/完整语音验收。150 MHz、数值门槛、面积功耗口径按赛题执行。

工作日志：2026-11-02 建立公开 GitHub 协作入口，使用已有 Git 凭据认证，账号密码未写入工程。来源目录完整复制并校验；LFS 处理大文件；推送后在本机实际克隆并核对。最终提交/克隆验证结果见 `_同步记录/` 及原工作区迁移记录。

资料：[GitHub 协作者权限](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/permission-levels-for-a-personal-account-repository)、[Git LFS](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage)。
