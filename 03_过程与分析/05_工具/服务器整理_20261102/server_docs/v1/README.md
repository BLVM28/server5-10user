# v1 服务器工程

从本目录执行 `make`。先读 [操作手册](SERVER_GUIDE.md) 和 [本轮实测](SERVER_RESULTS.md)。

- `rtl/`：硬件实现；`tb/`：自检仿真；`vec/`：输入和黄金值。
- `server_eda/`：仿真、综合、STA、门级脚本；根 Makefile 是日常入口。
- `implementation/fix1/`：既有最终映射，`rebuilt/`：重新综合结果。二者均须用哈希匹配当前 RTL。
- `build/manual/`：生成产物；`reports/`：命令记录和清理前留存证据。
- `packages/`：RTL、TB、Makefile、流程、向量分别打包；`history/`：旧版本/旧结果，逐文件校验后归档；`releases/`：原冻结包不改。
- `integration/`：E203 NICE 包装和驱动；正式共享内存与整机运行仍待验收。

模块关系：NICE 描述符控制 → linear_core 调度 → X/W SRAM 缓存 → 8 路 dot64/quantize → ICB 写回。ICB master 只保留一个在途事务，完成响应要等最后一次写应答返回。

本目录源码用于本科 Dense1 矩阵加速，不直接输出 yes/no。阅读 RTL 细节见 [rtl/README.md](rtl/README.md)。
