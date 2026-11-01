> 2026-11-01 整理更新：本目录原有技术说明保留。最新完成度以工作区根 README 和 fix1 报告为准；本轮只整理本地资料，不自动同步新文档到 VM/服务器。 本目录解决端口/驱动封装，尚不是完整 CPU 固件；正式共享 RAM、异常与一致性仍须联调。赛题不要求布局布线。
> [工作区首页](../../README.md) · [调试导读](../../02_项目导读/03_调试与E203接入.md)

# E203 与 SRAM 接入说明

本接入层按服务器公共 ZIP 的实际 NICE 声明编写。它解决模块端口和指令字段对应关系；题目共享 RAM 的实体、地址译码和完整 CPU 执行仍需正式平台工程落实。默认内存窗口关闭，避免在错误地址上启动搬运。

## 已核对的接口

公共包：`/storage1/admin_public_dir/SOC_RTL_2025/e203_hbirdv2-master_1013_update_sim.zip`，SHA-256 `63f9a4203402ae28721f1333f255fcccaa98a70066293f88b80fb67fd25f7c69`。包内 `rtl/e203/subsys/e203_subsys_nice_core.v:25–60` 声明以下端口，当前配置 XLEN=ADDR_SIZE=32。

已逐字节比较包内 `rtl/e203` 与 `vsim/install/rtl` 两棵树中的 NICE core、config.v、e203_defines.v、e203_cpu.v、e203_soc_top.v，五个对应文件完全相同（取证截图 35）。这五项不存在安装副本与源目录接口不同的问题。

| 方向相对加速器 | 端口 | 位宽 |
|---|---|---:|
| 输入 | nice_clk、nice_rst_n | 各 1 |
| 输出 | nice_active、nice_mem_holdup | 各 1 |
| 输入/输出 | nice_req_valid / nice_req_ready | 各 1 |
| 输入 | nice_req_inst、nice_req_rs1、nice_req_rs2 | 各 32 |
| 输出/输入 | nice_rsp_valid / nice_rsp_ready | 各 1 |
| 输出 | nice_rsp_rdat、nice_rsp_err | 32、1 |
| 输出/输入 | nice_icb_cmd_valid / nice_icb_cmd_ready | 各 1 |
| 输出 | nice_icb_cmd_addr、nice_icb_cmd_wdata | 各 32 |
| 输出 | nice_icb_cmd_read、nice_icb_cmd_size | 1、2 |
| 输入/输出 | nice_icb_rsp_valid / nice_icb_rsp_ready | 各 1 |
| 输入 | nice_icb_rsp_rdata、nice_icb_rsp_err | 32、1 |

外部 NICE 没有 cmd_wmask。本设计只作 32 bit 对齐访问，固定 cmd_size=2'b10，由 E203 原 LSU 路径处理总线字访问。不能擅自给 CPU 实例增加 wmask 端口。

`e203_cpu.v:487–518` 中 NICE 的时钟接 clk_aon、复位接 rst_aon，nice_active 未被上层使用；`e203_clk_ctrl.v:151` 为 `assign clk_aon = clk`。这说明所查源码的 clk_aon 不是凭名称猜测的低速 32 kHz 时钟，不代表正式平台时钟约束已验收。

## 源文件替换和宏选择

1. 在自己的 SoC 工程副本中，从 filelist 移除原 demo `e203_subsys_nice_core.v`，加入本目录同名文件以及 `../rtl.f` 的 10 个源文件。不得同时编译两个同名模块，不修改公共原件。
2. 使用真实 `e203_defines.v` 及其配置头，启用 `E203_HAS_NICE`。本包装对 XLEN/地址宽度不是 32 的配置故意报展开错误，避免静默截断。
3. 在正式平台确定合法窗口后定义 `KWT_MEM_BASE` 和 `KWT_MEM_BYTES`，单位均为字节。不给值时均为 0；描述符请求会返回 0x11，不进行内存访问。
4. 根据实际 32 bit 字的 int16 装配选 `KWT_PACK_LOW_FIRST=1/0`。默认 1；C 驱动的 pack16 参数必须相同。`KWT_W_BANK_AW=7` 默认采用 SP128，10 为 SP1024 回退。
5. 仿真定义 `KWT_USE_FOUNDRY_SRAM`，加入 SP128/SP1024 的 `.v` 与 `_rtl.v` 原模型；普通 RTL 功能检查同时定义厂商 `ARM_UD_MODEL`。纯本地仿真不用该宏，加入 `tb/kwt_sram_sim.sv`。
6. 综合定义 `KWT_USE_FOUNDRY_SRAM` 和 `SYNTHESIS`，直接例化 Liberty 同名 cell `RAMSP128X16` / `RAMSP1024X16`。链接真实 SRAM Liberty/DB，不能把行为 RAM 或厂商时序仿真文件综合成触发器。`sram_blackboxes.sv` 仅供本机结构检查，不是可运行内存。

宏脚按实际源文件：CLK 上升沿、CEN/GWEN/WEN 低有效；WEN 为逐 bit 的 16 位屏蔽；Q/D 16 位，A 分别 7/10 位；固定 EMA=3'd2、EMAW=2'd0、RET1N=1。普通模式读取在沿后输出，本设计在下一沿消费，不依赖同拍组合读。默认宏时序模型含非零 setup/hold/clock-to-Q；无标准单元延迟的 RTL 不能替代带 SDF 的门级时序验收。

## 指令和描述符 ABI

这是本工程分配的应用 ABI，仍需与正式平台其他自定义指令核对冲突。custom3 opcode=0x7b，funct7=0x40，funct3=3'b110，rs2 指令字段为 x0。E203 `e203_exu_decode.v:313–315` 使用 inst[14]/[13]/[12] 标记写 rd、读 rs1、读 rs2，所以本编码表示写结果、读描述符指针、不读 rs2。

rs1 为 32 字节描述符指针；请求只在空闲接受。任务执行期间 CPU 等待这一长指令的完成；不是中断启动或异步队列。nice_mem_holdup 在搬运和计算期间置位，在完成响应阶段释放。

| 偏移 B | 32 bit 字段 | 值 |
|---:|---|---|
| 0 | magic | 0x3154574b |
| 4 | format | 0x00010000 |
| 8 | layer | 0..11 |
| 12 | X_base | 12,672 B 连续输入 |
| 16 | W_base | 32,768 B 当前层权重 |
| 20 | B_base | 1,024 B 当前层 bias |
| 24 | Y_base | 50,688 B 输出 |
| 28 | reserved | 0 |

五个对象均 4 B 对齐、彼此不重叠，均在一段经过验证的窗口内。描述符 + 单任务数据共 97,184 B；可以逐层搬入参数，不要求 12 层参数常驻。layer 不会在硬件中自动选择 W/b。

`kwt_driver.h` 提供结构体、装配函数和 RV32 `.insn` 调用，前后带 `fence rw,rw` 及编译器 memory 屏障。RV32 GCC 实际生成 `0x8005657b`（本次 rd=rs1=a0）。fence 不等于 cache flush：正式系统若存在缓存，须在平台驱动中执行清理/失效，或者使用已确认的非缓存共享区。

成功响应的数据为 0。错误响应置 nice_rsp_err；它可能转为 E203 异常，正式固件需核对 trap 路径、错误状态读取及失败输出丢弃，不能把所有错误都当作正常 C 返回。

## 尚需正式平台补齐

| 缺项 | 当前处理 | 信息不同后的修改 |
|---|---|---|
| 512 KiB 共享 RAM 实体、窗口和保留区 | MEM_BYTES=0；不默认猜地址 | 接真实 SRAM/互联，再设合法连续范围；若分散窗口则扩展校验器 |
| 正式顶层与允许替换位置 | 提供所查公共版同名 NICE 包装 | 若正式接口变化，仅改适配层并重跑端口和 CPU 回归 |
| 写响应是否代表全局可见及一致性 | 等全部写响应后完成；驱动屏障 | 按互联增加排空/一致性操作 |
| 复位域和在途应答 | 仅支持 CPU/NICE/应答域共同复位 | 局部复位需求须增加排空或应答隔离逻辑 |
| 指令冲突和异常处理 | 候选 custom3 ABI；软件头与 RTL 一致 | 改 opcode/funct 和驱动，并重跑译码/异常用例 |
| 正式库角、I/O 延迟、约束及功耗活动 | 仅提供 150 MHz 时钟模板 | 用真实 ASIC 库和完整约束综合、STA、功耗估算 |

地址障碍来自实际源码：`e203_soc_top.v:135–178` 把 sysper、sysfio、sysmem 接成命令/响应回环，读数据为 0。当前 ITCM=0x80000000、DTCM=0x90000000、各 addr width=18 的配置不足以证明存在题目要求的共享 RAM。应由正式平台补齐或在参赛方被允许修改的工程中实现真实存储路径，再做 CPU 发指令到末次写响应的整机测试。


工作日志：2026-11-01 补充目录导航；功能源码和固定向量未修改。历史原始产物已按哈希归档，正式 ZIP 保持原字节。
