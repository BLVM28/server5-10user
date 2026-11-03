# 版本复现顺序

先读 [HISTORY](../HISTORY.md) 的格式选择依据。本地从仓库根运行下列命令。vectors 的输入始终来自冻结 v2。5 号机的滚动原始过程和阶段上传包只在个人 v4.1 目录。

```powershell
python v4.1/py/make_fast_vectors.py
python v2/py/run_model_python.py v4.1/py/qualify_speech.py --data datasets/speech_commands_v0.02 --out v4.1/build/speech --per-class 50
python v4.1/py/run_xsim.py --tag legacy
python v4.1/py/run_xsim.py --tag trial --vectors v4.1/vec/fast/worst --tops tb_kwt_block8
python v4.1/py/run_xsim.py --tag alt --vectors v4.1/vec/fast/worst --define KWT_TEST_SWAP --define KWT_TEST_W1024 --tops tb_kwt_block8
python v4.1/py/run_xsim.py --tag bfpunit --tops tb_kwt_bfp_codec
python v4.1/py/run_xsim.py --tag immediate --vectors v4.1/vec/fast/worst --tops tb_kwt_block8_immediate
python v4.1/py/audit_driver.py --cc gcc
python v4.1/py/local_evidence.py
```
