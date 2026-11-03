# qualified200 · 已鉴定的 v3 完整核心

源实现为服务器 `v3_trial_20261103_07384bb8170d` 内完成五单元修复的网表。正式目录独立保存实际文件；PT 日常运行读取本目录，核对 `mapped.v`、`qualification.json`、`resize_audit.json` 和当前源码指纹。网表 SHA 和原始鉴定 SHA 见 [ppa.json](../../results/ppa.json)。

要复查该实现，在 v3 根执行 `make timing`。要核对比赛频率，执行 `make timing PERIOD=6.666667`。200 MHz 下 SS setup +0.000194 ns、FF hold +0.125206 ns。这个快照的判断范围是完整加速器的前端映射。
