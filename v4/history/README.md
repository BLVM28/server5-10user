# 实验次序与本地复现

以 v3.1 的算术链为起点，冻结同一数值格式、参考数据和 ICB BFM。在同一 v4 映射上切换 format，量出数据流/访存和输出压缩各自的收益。v3.1 的软件对照以同 TB 的原始 RTL 重新测量。服务器 history/ 可保存本轮经 SHA 核实的阶段上传包。生产入口为版本根目录，而非阶段 ZIP。

第一轮紧凑模式为 1,601,382 拍，但 PT 发现仿真观测总线留下 320 个无负载驱动，不能计作工艺通过。修订后排除综合观测端口，并把下一行本地取数与当前行外部写应答重叠。最终相同任务为 1,568,392 拍，比首轮再少 32,990 拍。[首轮数据](../results/first_candidate.json) · [冻结对照](../results/functional.json)

在本地 v4 目录运行以下命令。先生成实际 DUT 内存截取，再审核 C 消费端。GCC 可通过 --cc 指定本地路径。
```powershell
python py/baseline.py
python py/run_xsim.py --tag base
python py/run_xsim.py --tag paired --vectors ../v2/vec/real_speech/worst --tops tb_kwt_compact tb_kwt_system
python py/run_xsim.py --tag swap --define KWT_TEST_SWAP --define KWT_TEST_W1024 --vectors ../v2/vec/real_speech/worst --tops tb_kwt_compact tb_kwt_overlap
python py/run_xsim.py --tag export --vectors ../v2/vec/real_speech/worst --tops tb_kwt_export
python py/audit_codec.py --cc gcc
python py/summarize.py
```
