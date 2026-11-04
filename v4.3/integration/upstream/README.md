# 原封不动的公共 E203 依赖

这些 Apache-2.0 文件从允许只读的公共 ZIP 中复制到本版，用于可复现地验证控制器。原文件未修改；逐文件 SHA-256 和原路径见 provenance.json。ZIP：
`/storage1/admin_public_dir/SOC_RTL_2025/e203_hbirdv2-master_1013_update_sim.zip`
SHA-256：`63f9a4203402ae28721f1333f255fcccaa98a70066293f88b80fb67fd25f7c69`。

sirv_sram_icb_ctrl 为命令旁路缓冲加一拍 SRAM 控制；sirv_1cyc_sram_ctrl 把同步 RAM 读数据对应到响应；sirv_gnrl_bufs/dffs 是原有握手级与寄存器；e203_clkgate 加 GENERIC_RVT_SMIC 提供原有门控时钟结构；config/e203_defines 是该公共配置。GENERIC_RVT_ARM 保留公共分发的可选原始原语文件，当前不编译它。

仿真定义 FPGA，以选择原文件中的通用锁存器门控实现；没有定义 FPGA_SOURCE，因此仍测试门控行为。DISABLE_SV_ASSERTION 只关闭公共 dffs 中未随依赖带入的 xchecker，项目自身计分板和所有 $fatal 检查仍开启。上游寄存器自带 #1 仿真延迟保持不变。

这些文件是测试端点依赖，不属于加速器综合面积和功耗。正式加速器的局部 SRAM 仍使用真实工艺模型。完整许可证在 ../../UPSTREAM_LICENSE.txt，各文件也保留原版权头。
