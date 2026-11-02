# 本地语音数据

`speech_commands_v0.02/` 保存指定上游仓库引用的 Google 原始压缩包、官方划分清单及验证划分 WAV。该目录忽略 Git；不把约 2.43 GB 数据集重复上传仓库。

下载：`python v2/py/download_speech_commands.py --out datasets/speech_commands_v0.02`

原始包包含训练/验证/测试数据；脚本只解出验证划分，调试不使用测试音频。下载大小、MD5、SHA-256 和解出数量见生成的 `download.json`。比赛静音按要求使用 16000 点全零波形，不从 `_background_noise_` 目录截取。
