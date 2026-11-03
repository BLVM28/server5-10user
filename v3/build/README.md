# 生成产物 · 当前运行结果从哪里找

| 路径 | 内容和用途 |
|---|---|
| `manual/compile`、`manual/runs` | 服务器 VCS 编译程序、自检输出、verified.json 和 waves 的 VCD |
| `manual/timing`、`manual/gate` | 所选网表的当前 PT 报告、SDF、可选注释/门级结果 |
| `ppa/<源码指纹>` | 重新综合的原始映射、复位修复、单元替换、逐角记录 |
| `final_base`、`final_worst` | Windows 上最终 RTL 的两个 XSim 运行目录；可阅读的结果已整理进 ../results |
| `base`、`worst` | 首轮候选运行目录，供回溯；最终结果使用带 final 的目录 |
| `transport`、`publish_session` | 本地个人工作区传输和安装过程的临时文件，不参与编译 |

`make clean` 只清服务器 build/manual，先保存其记录。其它目录是可重建的工具输出；不要修改 simv、SDF 或仿真缓存来修复源码问题。本目录的说明随 Git 保存，原始工具生成物留在生成机器。
