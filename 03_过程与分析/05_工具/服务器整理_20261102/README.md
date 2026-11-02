# 2026-11-02 服务器整理过程记录

正式入口是工作区 v2/Makefile、v2/SERVER_GUIDE.md、v2/SERVER_RESULTS.md。本目录不是日常仿真入口。

- install_server.py：旧工程分版迁移；历史 ZIP 逐项校验后收起散文件。
- prepare_source_sync.py、source_sync_manifest.json、finalize_server_delivery.py：本地/服务器源文件清单及最后一次日常命令验收。
- vnc_linux_client.py、ftp_fresh.py：访问已授权个人工作区；凭据只通过 getpass 留在进程内，不写入文件。
- xsim_negative_evidence/：独立 XSim 58/58 异常回归证据。crosscheck_negative_xsim_fixed.py 为成功命令，旧未修正 helper 只记录调试历史。
- run_server_jobs.py、parallel_jobs.py、gate_final_jobs.py、summarize_server.py、patch_*：早期或未执行的扩展实验；不能把计划脚本当成已通过的验证。
- observed_progress.json：收敛范围前的阶段记录；最终状态以 SERVER_RESULTS.md 和服务器 shared/final_daily_verification.json 为准。
- 临时 ZIP 和截图保留本地并由 Git 忽略；它们不属于运行依赖。服务器全层扩展门级未完成，不计 PASS。

最终日常 make check 只包含基础功能与双角 STA；原始 RTL、既有黄金值和受保护 30 个 RTL/TB/说明文件保持原字节。GitHub 保存源码、说明、可复现脚本和导出向量；原始语音数据由 datasets/.gitignore 排除，工艺库和映射网表不公开。
