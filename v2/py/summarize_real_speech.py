"""Verify retained evidence and render the local real-speech report."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--snapshot', action='store_true', help='Record immutable inputs before a new run, or verify an existing snapshot')
    a = p.parse_args()
    out = a.capture.resolve()
    if a.snapshot:
        out.mkdir(parents=True, exist_ok=True)
        snapshot = out / 'protected_before.json'
        current = {str(f.relative_to(ROOT)).replace('\\', '/'): sha(f)
                   for folder in ('v2/rtl', 'v2/tb', 'v1/rtl') for f in (ROOT / folder).glob('*') if f.is_file()}
        if snapshot.exists():
            assert json.loads(snapshot.read_text())['protected_sha256'] == current, 'Baseline changed; refusing to replace it'
        else:
            snapshot.write_text(json.dumps({'protected_sha256': current}, indent=2) + '\n')
        print('Protected baseline recorded/verified: %d files' % len(current))
        return
    r = json.loads((out / 'report.json').read_text())
    h = json.loads((out / 'rtl_results.json').read_text())
    samples = json.loads((out / 'manifest.json').read_text())
    before = json.loads((out / 'protected_before.json').read_text())['protected_sha256']
    assert all(sha(ROOT / path) == expected for path, expected in before.items())
    assert r['precision_pass'] and r['all_individual_cases_pass']
    assert len(samples) == r['samples'] and len(h['suites']) == len(r['rtl_suites'])
    assert len({s['path'] for s in samples if s['class_id'] != 0}) == r['real_distinct_wavs']
    assert h['tests_passed'] == len(h['suites']) * 29
    data = ROOT / 'datasets/speech_commands_v0.02'
    validation = set((data / 'validation_list.txt').read_text().splitlines())
    testing = set((data / 'testing_list.txt').read_text().splitlines())
    audio_checks = 0
    for sample in samples:
        if sample['class_id'] == 0:
            assert sample['path'] == 'generated:zero16000'
            assert sample['sha256'] == hashlib.sha256(bytes(16000 * 4)).hexdigest()
        else:
            assert sample['path'] in validation and sample['path'] not in testing
            assert sha(data / 'validation' / sample['path']) == sample['sha256']
            audio_checks += 1
    for path, expected in r['source_sha256'].items():
        assert sha(ROOT / path) == expected
    distinct_tasks = {(sample, layer) for suite in r['rtl_suites'] for sample, layer in zip(suite['samples'], suite['layers'])}
    rtl_sample_ids = {sample for sample, layer in distinct_tasks}
    rtl_real_wavs = len({samples[i]['path'] for i in rtl_sample_ids if samples[i]['class_id'] != 0})
    vectors_checked = 0
    for suite in r['rtl_suites']:
        evidence = json.loads((out / 'logs' / (suite['name'] + '_results.json')).read_text())
        for name, expected in evidence['vector_sha256'].items():
            assert sha(out / 'rtl' / suite['name'] / name) == expected
            vectors_checked += 1
        for path, expected in evidence['source_sha256'].items():
            assert sha(ROOT / 'v2' / path.replace('\\', '/')) == expected
        (out / 'rtl' / suite['name'] / 'README.md').write_text(
            '# ' + suite['name'] + '：RTL 输入与独立期望\n\n'
            '层号 0—11 对应 manifest 样本 ID：`' + str(suite['samples']) + '`。\n\n'
            '`layerNN_x/w/b.hex` 是 DUT 的实际输入；`y.hex` 是输出比较值，`acc.hex` 是完整 40 位累加比较值，二者不作为 DUT 输出驱动。'
            '`matrix_sat.hex` 是各层预期饱和计数。低索引 int16 放入 32 位字的低半字。所有导出矩阵经过原 numeric_model.py 独立核对。\n\n'
            '每层 X 3168 字、W 8192 字、b 256 字、Y 12672 字、acc 25344 个。上层 report.json 给出浮点误差；rtl_results.json 记录实际仿真。\n', encoding='utf-8')
    (out / 'rtl/README.md').write_text('# RTL 验证向量\n\n十二套 class_XX 分别来自十二类的首个选中样本，每套覆盖全部十二层；worst 为本轮每层误差最大的样本。'
        '它们是软件参考与硬件仿真的共同输入，不是完整模型逐层硬件串接。HEX 的逐文件 SHA 在 ../logs/*_results.json。\n', encoding='utf-8')
    verification = dict(protected_files_unchanged=len(before), vectors_sha256_checked=vectors_checked,
                        full_matrices=h['full_matrix_executions'], distinct_primary_sample_layer_tasks=len(distinct_tasks),
                        distinct_rtl_real_wavs=rtl_real_wavs, audio_sha256_checks=audio_checks,
                        numeric_source_sha256_checks=len(r['source_sha256']), passed=True)
    (out / 'evidence_verification.json').write_text(json.dumps(verification, indent=2) + '\n')
    rows = '\n'.join('| %d | %.8f%% | %.8f%% | %.5f | %.5f | %d / %d |' %
        (t['layer'], 100*t['nrmse'], 100*t['max_sample_nrmse'], t['max_abs_x'], t['max_abs_y'], t['x_saturated'], t['y_saturated']) for t in r['layers'])
    class_rows = '\n'.join('| %s | %d/%d |' % (label, r['float_confusion_matrix'][i][i], r['per_class']) for i, label in enumerate(r['classes']))
    text = f'''# v2 真实语音验证报告（2026-11-02）

**当前 v2 在本轮自选验证集上通过 Dense1 数值精度与选定任务的 RTL 逐位检查。** 最大逐层汇总 NRMSE **{100*r['max_layer_nrmse']:.8f}%**，低于 3%；RTL **{h['tests_passed']}/{h['tests_passed']}** 场景通过。未改 RTL、权重或数值格式。这不是“任意输入都绝对正确”的证明，也不是正式 E203 SoC 或官方最终评测通过声明。

## 1. 数据来源与样本边界

- 从 [赛题指定上游 README](https://github.com/ARM-software/keyword-transformer/blob/237e4097/README.md) 引用的 Google 地址下载 speech_commands_v0.02 原始包，{r['dataset']['bytes']:,} B；只解出 {r['dataset']['validation_wavs']:,} 条验证 WAV，训练和测试音频未解出。
- 原包 SHA-256：`{r['dataset']['sha256']}`；MD5：`{r['dataset']['md5']}`。本地数据在 `../../datasets/speech_commands_v0.02/`，已由 Git 忽略。
- 固定种子 {r['seed']}，每类 {r['per_class']} 例，共 **{r['samples']}** 个用例：**{r['real_distinct_wavs']} 个不同真实 WAV + {r['zero_silence_cases']} 次同样的全零静音**。其他语音从非目标词中选取，未使用 `_background_noise_` 代替静音。
- 所有候选验证路径同时符合原包 validation_list 和指定源码 which_set，且不在 testing_list。无训练、微调、标定或尺度调整。
- 这是自选调试集；组委会的最终 600 条名单尚未公布。它不代表全部 9981 条验证音频都做了模型/RTL 测试。

## 2. 实测检查

| 检查 | 结果与覆盖 |
|---|---|
| 模型权重 | {len(r['checkpoint_tensor_equality'])}/{len(r['checkpoint_tensor_equality'])} 个已加载张量与 checkpoint 明确语义路径的值逐位相等；包含 Attention、LayerNorm、两层 Dense、投影、token 和分类头 |
| 原处理图对照 | {r['preprocessing_bit_equal_checks']}/{r['real_distinct_wavs']} 个真实 WAV 的 PCM 解码/裁剪/补零，与上游 AudioProcessor 原图逐位相等 |
| 截取位置对照 | {r['native_model_replay_logits_bit_equal_checks']}/{r['samples']} 次原层对象重放 logits 与普通原模型调用逐位相等 |
| 数值验证 | {r['samples']*12}/{r['samples']*12} 个样本×层；每层 {r['samples']*99*256:,} 个输出元素，总共 {r['samples']*12*99*256:,} 个 |
| 舍入独立核验 | 数组化 RNE 与原 Fraction oracle {r['rne_oracle_checks']:,}/{r['rne_oracle_checks']:,}；全部 {r['rtl_export_oracle_checked_matrices']} 个导出矩阵再经过原 linear() 全元素核对 |
| 真实输入 RTL | 12 类各一例×12 层 + 每层误差最大的一例，共 13 套；{h['tests_passed']}/{h['tests_passed']} 场景通过 |
| 完整矩阵执行 | {h['full_matrix_executions']} 次，包括每套的 layer 0/11 重启重复检查；16 位输出和 40 位累加各核对 {h['output_int16_elements_checked']:,} 个元素 |
| 基础组件复测 | 算术 260/260；ICB 4/4；重叠/写错恢复 5/5；乘法边界 524288/524288，含空拍/复位总计 527566 次 |
| 证据完整性 | {len(before)} 个受保护 RTL/TB/说明文件未变；{audio_checks} 个 WAV、{vectors_checked} 个仿真向量文件 SHA 再核对通过；数值/仿真实际源码与参数 SHA 一致 |

RTL 使用 **Vivado XSim 2023.2** 和既有 tb_kwt_system，保留忙时拒绝、命令/响应背压、错误注入、复位、输出 guard、事务计数和饱和计数检查。TB 中单次矩阵实际写 12672 个 32 位字，总事务 24296。测试台的内存是行为模型，CPU 请求由激励产生。

**{r['samples']} 个用例都做了软件数值验证；没有声称 {r['samples']}×12 个任务全部跑过 RTL。** RTL 导出任务去重后为 **{len(distinct_tasks)} 个样本×层组合，来源于 {rtl_real_wavs} 个真实 WAV 及全零静音**；worst 中部分任务与 class_00 重复。本次 {h['full_matrix_executions']} 次硬件矩阵执行还包含同一输入的复位/恢复复测，不能称为同等数量的不同语音。

## 3. 十二层误差与动态范围

格式保持 X=int16/F11，W=int16/F16，b=int32/F27，acc=int40/F27，Y=int16/F11；64 项精确累加，最后一次最近偶数舍入和饱和。

| 层号（0 起） | 汇总 NRMSE | 最差单样本 NRMSE | 最大绝对 X | 最大绝对浮点 Y | X/Y 饱和数 |
|---|---:|---:|---:|---:|---:|
{rows}

全部 W/b 编码饱和计数：{sum(t['w_saturated'] for t in r['layers'])}/{sum(t['b_saturated'] for t in r['layers'])}。最差单个样本×层误差 **{100*r['max_single_case_nrmse']:.8f}%**，本轮所有单任务也都 ≤3%。汇总 NRMSE 根据各层误差平方和/参考平方和计算，没有平均样本百分比。

## 4. yes/no 结果意味着什么

原始浮点 KWT 模型分类正确 **{r['float_model_correct']}/{r['samples']}（{100*r['float_model_accuracy']:.2f}%）**。这是当前自选、均衡且包含重复全零静音的验证集结果，不能直接与论文原评估集准确率比较；也不是 RTL 整机分类准确率。逐例预测见 predictions.json。

| 原始浮点模型类别 | 分类正确数 |
|---|---:|
{class_rows}

本科硬件必做输出是 Y[99,256]，之后 GELU、Dense2、其余编码器运算和分类头不在本模块内。只生成 X/golden 文件也不够：需要 RTL 真正计算 Y，再完成 E203 驱动、共享内存交换、SoC 仿真与综合。详见 [本科步骤与数据流](../../02_项目导读/05_本科语音验证到底要做什么.md)。

## 5. 问题记录和仍然缺少的证据

1. 新权重审计初次按 Keras 显示名匹配时，在 dense_5/kernel 名称处停止；日志保留 logs/capture_attempt1_name_audit.log。随后按 checkpoint 的对象语义路径匹配全部 162 个张量，并要求覆盖模型所有权重。第二次在完成样本计算后，报告来源路径的相对/绝对转换报错，记录在 capture_attempt2_report_path.log；修复路径后完整重跑并落盘。没有改权重或降低比较标准。
2. TF2.4.0 / Addons0.12.1 会报告 Dense/GELU 旧对象引用警告。所有带参数对象实际值都已核对；所有样本重放也保持相等。仍保留原始警告。本机采用 TF2.4.0 正式版，非上游当年测试的 rc1 环境；正式评测参考环境需最终复核。
3. 未运行真实 E203 CPU/正式共享 RAM/固件，默认内存窗口仍关闭。NICE BFM 正确不代替任务 3，也不代表整机已从麦克风输出 yes/no。
4. 本轮没有改 RTL，也未新增 STA、门级或功耗测量。已有 fix1 的工艺、约束和覆盖限制仍见 ../../vm_eda/REPORT.md。XSim 功能时钟不是 150 MHz 时序达标证据。
5. 全部结果保存在本地克隆；未自动上传数据集、未推送 Git，也未更新服务器/VM。

## 6. 文件与复现

| 路径 | 用途 |
|---|---|
| report.json / manifest.json / predictions.json | 原始数值统计、音频来源与 SHA、逐样本误差/浮点预测 |
| rtl/ | class_00…class_11 和 worst 的实际 DUT 输入/独立 golden |
| rtl_results.json / evidence_verification.json | HDL 汇总和证据再核验 |
| capture.log / rtl_driver.log / logs/ | 原始执行日志、失败审计记录、各次源/向量哈希和生成 TB |
| protected_before.json | 本轮结束再核对的受保护文件哈希 |

从工作区根执行（Python 启动器适用于本机保留的 Windows 环境）：

```powershell
python v2/py/summarize_real_speech.py --capture v2/validation_real_speech_20261102 --snapshot
python v2/py/download_speech_commands.py --out datasets/speech_commands_v0.02
python v2/py/run_model_python.py v2/py/qualify_real_speech.py --data datasets/speech_commands_v0.02 --out v2/validation_real_speech_20261102
python v2/py/run_real_speech_rtl.py --capture v2/validation_real_speech_20261102 --jobs 3
python v2/py/summarize_real_speech.py --capture v2/validation_real_speech_20261102
```

再次运行会更新本目录当次结果；要保存新实验，换一个 --out / --capture 和 RTL --tag。历史发布 ZIP、v1、固定 vec 和 v2 RTL 未修改。
'''
    (out / 'README.md').write_text(text, encoding='utf-8')
    print('ALL PASS, evidence verified; report written', flush=True)


if __name__ == '__main__':
    main()
