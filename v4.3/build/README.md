# 可再生中间文件

本地 XSim 的 public_full 保存公共控制器全回归和 12 层真实输出导出；dot64 保存独立点积测试；speech 保存本轮模型精度复测；software 保存 C/RV32 编译物。session 是本次 VNC 连接和摘要传输的临时脚本/截图，不是使用工程的入口，不含固化登录凭证。

服务器 build/manual 保存日常 VCS 和 STA；ppa 保存综合/修复/等价及扫点；paired 保存同端点 v4.2 参照；power 保存真实宏门级 SDF、VCD 和 PX 报告。生成的工具子目录无需手工逐层阅读。make clean 只清理 manual 并先归档证据，不删除实现或功耗数据。该目录除本说明不提交 Git。
