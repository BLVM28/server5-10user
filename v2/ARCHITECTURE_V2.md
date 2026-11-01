# v2 改良方案与证据

本版保持 E203 NICE 端口、指令 ABI、32 bit 单笔 ICB、8 lane、15 个 SRAM、12 层第一 Dense 运算和全部定点语义。赛题规定统一 150 MHz，正式性能比较必须同频。200 MHz 仅作余量探索，不作为比赛加速依据。

## 修改与理论依据

1. **操作数寄存器**：将 v1 的 SRAM Q→bank mux→16×16 乘法→结果寄存器拆开，在 `kwt_mul16_pipe` 的入口寄存 x/w。SRAM 读出和乘法不再占同一周期。
2. **部分积流水**：对 signed16 的 w 使用精确恒等式 `w = unsigned(w[7:0]) + signed(w[15:8]) * 256`。并行计算 signed16×unsigned8（25 bit 容器）和 signed16×signed8（24 bit），下一级符号扩展、移位后在 32 bit 合并。不裁剪、不近似，不改 40 bit 累加和最终一次 RNE 饱和。乘法管线由 1 级改为 3 级，II 仍为 1。
3. **数据与控制同行**：valid/last 经过同样三级。原 dot64 按返回 valid/last 收尾，因此不硬编码旧延迟。复位清所有流水有效位，防止中止任务后的旧结果泄漏。
4. **hold 修复属于实现**：使用 SS/FF 配对库和真实缓冲单元做 min-delay 修复；不写 `#delay` 到可综合 RTL，不以降频代替 hold 修复。保持 v1 的输入/输出预算、uncertainty、负载和复位检查。布局前改善仍须 CTS/布线后复验。
5. **计算/写回重叠**：上一行的 8 个输出已经进入 `y_hold` 后，立即在 MAC 侧计算下一行。独立的 prefetch_state 与 prefetch_row 驱动已有 X/W SRAM，ICB 仍只有一个 writer 和一笔在途。MAC 原有结果寄存器提供第二个结果槽；写回慢时，下一行结果保持，直到前一行所有写应答成功。W/b 只在整组 99 行完成后更换，不跨组覆盖参数。该做法采用 Gemmini 文档中的 access/execute 解耦原则，但不增加乱序、DMA 多在途或额外 SRAM。
6. **错误排空**：若写回错误发生在下一行预计算期间，同步 compute_clear 清空乘法有效位、dot 状态和预取状态；停止新 SRAM 读取。当前任务按原 ABI 报错，下一项合法任务无需全局复位即可恢复。新增长背压/错误后立即重启 TB 检查这一行为。

```mermaid
flowchart LR
  RAM[7×SP1024 X + 8×SP128 W] --> OP[操作数寄存]
  OP --> PP[8 lane 并行部分积]
  PP --> SUM[完整 32 bit 乘积合并]
  SUM --> ACC[40 bit 累加]
  ACC --> RNE[最终 RNE + 饱和]
  RNE --> Y[结果保持 / ICB 写回]
```

代价：增加操作数和部分积寄存器，每个 64 项向量多 2 个填充/排空周期；通过重叠原来串行的写回来抵消，并以固定延迟 BFM 的同频周期数实际验证。原接口、金模和事务数不变；总线等待和单笔在途仍限制系统加速，不用 MAC 峰值替代实际任务吞吐。

## 可核查的一手来源（2026-11-01 查阅）

- [Gemmini 官方 README](https://github.com/ucb-bar/gemmini/blob/master/README.md)，Generator Parameters / Systolic Array：mesh tile 之间插入流水寄存器，输入需要延迟对齐；支持根据计算延迟配置 PE 内部寄存器。本版采用相同的流水分隔与控制对齐原则，并未复制其完整 systolic array 或宣称它验证过本版实现。
- [Ibex 官方乘除法文档](https://ibex-core.readthedocs.io/en/latest/03_reference/instruction_decode_execute.html#multiplier-divider-block-mult-div)及 [ibex_multdiv_fast.sv](https://github.com/lowRISC/ibex/blob/master/rtl/ibex_multdiv_fast.sv)：用较小乘法单元组合完整乘法，明确区分吞吐/延迟/面积取舍，并提醒 `*`/`+` 的 ASIC 结果依赖综合。本版为自主编写的 16×16 全吞吐三级实现，不是直接移植 Ibex 的状态机。
- [OpenROAD 官方 Gate Resizer 文档](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html#repair-timing)：setup/hold 分别修复，hold 插缓冲应避免破坏 setup，正式检查在 CTS 后执行。本次使用服务器 Synopsys 工具完成相同类别的布局前优化，不把它当后端签核。

这些来源支持方法的工程合理性，不能代替本工程的功能与时序实测。最终是否采用目标频率、面积和任务时间的进步，以 v2 对比报告为准。
