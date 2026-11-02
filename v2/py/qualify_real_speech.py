"""Reproducible V2 Dense1 validation on real Speech Commands V2 audio.

600 self-selected validation cases (50 per class; silence is repeated zero).
This is NOT the organizer's unreleased evaluation list. No training or tuning.
The frozen numeric_model.py is the independent oracle. A checked vectorized
RNE implementation accelerates aggregate statistics; all exported RTL cases
also go through the original Fraction-based oracle.
"""
import argparse
import hashlib
import json
import os
import random
import sys
import time
import wave
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True
import numpy as np
from numeric_model import encode, linear, quantize

ROOT = Path(__file__).resolve().parents[1]
SEED = 59185


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rne_array(acc):
    floor = acc >> 16
    rem = acc & 65535
    rounded = floor + ((rem > 32768) | ((rem == 32768) & ((floor & 1) != 0)))
    sat = (rounded < -32768) | (rounded > 32767)
    return np.clip(rounded, -32768, 32767).astype(np.int16), sat


def audit_rne():
    # Both parity signs at ties; each low residue; saturation boundaries;
    # 40-bit endpoints and deterministic random accumulators.
    residues = np.arange(65536, dtype=np.int64)
    exhaustive = np.concatenate([q * 65536 + residues for q in (-32769, -32768, -2, -1, 0, 1, 32767, 32768)])
    random_acc = np.random.RandomState(SEED).randint(-(1 << 39), 1 << 39, 10000, dtype=np.int64)
    values = np.concatenate([exhaustive, random_acc, [-(1 << 39), (1 << 39) - 1]])
    actual, actual_sat = rne_array(values)
    expected = [quantize(int(v)) for v in values]
    assert np.array_equal(actual, [p[0] for p in expected])
    assert np.array_equal(actual_sat, [p[1] for p in expected])
    return len(values)


def hexfile(path, values, bits):
    path.write_text(''.join(('%0*x\n' % (bits // 4, int(v) & ((1 << bits) - 1)))
                            for v in np.asarray(values).flat), encoding='ascii')


def pack16(data):
    v = np.asarray(data, dtype=np.int64).ravel() & 65535
    return v[0::2] | (v[1::2] << 16)


def export_layer(out, layer, data, params):
    out.mkdir(parents=True, exist_ok=True)
    xi, reference, yi, acc, sat = data
    wi, bi = params[layer][:2]
    original_y, original_acc, original_sat = linear(xi, wi, bi)
    assert np.array_equal(yi, original_y) and np.array_equal(acc, original_acc)
    assert np.array_equal(sat, original_sat), 'Vectorized model disagrees with frozen oracle'
    for suffix, arr, bits in [('x', pack16(xi), 32), ('w', pack16(wi), 32),
                             ('b', bi, 32), ('y', pack16(yi), 32), ('acc', acc, 40)]:
        hexfile(out / ('layer%02d_%s.hex' % (layer, suffix)), arr, bits)
    return int(sat.sum())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--per-class', type=int, default=50)
    a = p.parse_args()
    assert 1 <= a.per_class <= 50
    a.out.mkdir(parents=True, exist_ok=True)
    repo = ROOT.parent / '01_核心参考/keyword-transformer-master'
    sys.path.insert(0, str(repo))
    import tensorflow as tf
    import tensorflow_addons as tfa
    from kws_streaming.models import models as model_registry
    from kws_streaming.models import kws_transformer
    from kws_streaming.data import input_data
    if not tf.executing_eagerly():
        tf.compat.v1.enable_eager_execution()
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    source = repo / 'models_data_v2_12_labels/kwt1'
    labels = (source / 'labels.txt').read_text().splitlines()
    assert len(labels) == 12 and labels[:2] == ['_silence_', '_unknown_']
    flags = json.loads((source / 'flags.json').read_text())
    assert labels[2:] == flags['wanted_words'].split(',')
    validation = set((a.data / 'validation_list.txt').read_text().splitlines())
    testing = set((a.data / 'testing_list.txt').read_text().splitlines())
    assert validation.isdisjoint(testing)
    pools = {label: [] for label in labels[1:]}
    for rel in sorted(validation):
        assert input_data.which_set(rel, flags['validation_percentage'], flags['testing_percentage']) == 'validation'
        word = Path(rel).parts[0]
        label = word if word in labels[2:] else '_unknown_'
        assert word != '_background_noise_'
        pools[label].append(rel)
    rng = random.Random(SEED)
    for label in labels[1:]:
        rng.shuffle(pools[label])
        assert len(pools[label]) >= a.per_class
    samples = []
    for n in range(a.per_class):
        for class_id, label in enumerate(labels):
            rel = 'generated:zero16000' if class_id == 0 else pools[label][n]
            samples.append(dict(id=len(samples), path=rel, split='validation', label=label,
                                class_id=class_id, silence_copy=n if class_id == 0 else None))
    (a.out / 'manifest.json').write_text(json.dumps(samples, indent=2) + '\n')
    rne_checks = audit_rne()
    print('RNE independent oracle ALL PASS, %d/%d' % (rne_checks, rne_checks), flush=True)
    flags.update(training=False, batch_size=1, train=0, use_spec_augment=0,
                 use_spec_cutout=0, resample=0., sp_resample=0., volume_resample=0.,
                 time_shift_ms=0., sp_time_shift_ms=0., prenorm=False,
                 approximate_gelu=False, distill_teacher_json='')
    model = kws_transformer.model(SimpleNamespace(**flags))
    status = model.load_weights(str(source / 'best_weights'))
    status.assert_existing_objects_matched()
    status.expect_partial()
    transformer = [l for l in model.layers if hasattr(l, 'enc_layers')]
    assert len(transformer) == 1
    transformer = transformer[0]
    assert len(transformer.enc_layers) == 12
    feature = [l for l in model.layers if l.__class__.__name__ == 'SpeechFeatures']
    assert len(feature) == 1
    feature, classifier = feature[0], model.layers[-1]
    # Legacy TF/TFA warns about references to the parameter-free GELU layer.
    # Keras display names omit parent scopes after this restore, so audit the
    # explicit semantic checkpoint paths (never fuzzy names/value searching).
    reader = tf.train.load_checkpoint(str(source / 'best_weights'))
    checkpoint_audit, audited_ids = [], set()
    def audit_var(variable, path):
        key = path + '/.ATTRIBUTES/VARIABLE_VALUE'
        saved = reader.get_tensor(key)
        assert np.array_equal(variable.numpy(), saved), 'Checkpoint tensor mismatch: ' + key
        assert np.isfinite(saved).all()
        audited_ids.add(id(variable))
        checkpoint_audit.append(dict(variable=variable.name, checkpoint_key=key, shape=variable.shape.as_list()))
    def audit_dense(dense, path):
        audit_var(dense.kernel, path + '/kernel')
        if dense.use_bias:
            audit_var(dense.bias, path + '/bias')
    base = 'layer_with_weights-0'
    audit_var(transformer.pos_emb, base + '/pos_emb')
    audit_var(transformer.class_emb, base + '/class_emb')
    audit_dense(transformer.patch_proj, base + '/patch_proj')
    for i, block in enumerate(transformer.enc_layers):
        stem = base + '/enc_layers/%d' % i
        for name in ('query_dense', 'key_dense', 'value_dense', 'combine_heads'):
            audit_dense(getattr(block.att, name), stem + '/att/' + name)
        for j, dense in enumerate([block.ffn.layers[0], block.ffn.layers[2]]):
            audit_dense(dense, stem + '/ffn/layer_with_weights-%d' % j)
        for name in ('layernorm1', 'layernorm2'):
            norm = getattr(block, name)
            audit_var(norm.gamma, stem + '/' + name + '/gamma')
            audit_var(norm.beta, stem + '/' + name + '/beta')
    audit_dense(classifier.layers[0], 'layer_with_weights-1/layer_with_weights-0')
    assert audited_ids == {id(v) for v in model.weights}, 'Unverified or extra learned tensors'
    assert len(checkpoint_audit) == len(model.weights)
    print('Checkpoint tensor equality ALL PASS, %d/%d' % (len(checkpoint_audit), len(checkpoint_audit)), flush=True)
    params = []
    for i, block in enumerate(transformer.enc_layers):
        w, b = block.ffn.layers[0].get_weights()
        exported = np.load(ROOT / 'vec/weights' / ('layer%02d.npz' % i))
        assert np.array_equal(w, exported['w_float']) and np.array_equal(b, exported['b_float'])
        wi, ws = encode(w, 16, 16)
        bi, bs = encode(b, 32, 27)
        params.append((wi, bi, ws, bs))

    # Verify normalization against the *actual upstream processing graph*,
    # not only a separately reimplemented PCM loader. The graph is isolated.
    upstream = input_data.AudioProcessor.__new__(input_data.AudioProcessor)
    preprocessing_graph = tf.Graph()
    with preprocessing_graph.as_default():
        upstream.prepare_processing_graph(SimpleNamespace(**flags))
    preprocessing_session = tf.compat.v1.Session(graph=preprocessing_graph,
        config=tf.compat.v1.ConfigProto(intra_op_parallelism_threads=4, inter_op_parallelism_threads=2))

    def replay(audio):
        net = transformer.patch_proj(feature(audio))
        net = tf.concat([tf.broadcast_to(transformer.class_emb, [1, 1, 64]), net], axis=1) + transformer.pos_emb
        captured = []
        for block in transformer.enc_layers:
            assert not block.prenorm
            attention, _ = block.att(net)
            x = block.layernorm1(net + block.dropout1(attention, training=False))
            y = block.ffn.layers[0](x)
            captured.append((x.numpy()[0], y.numpy()[0]))
            net = block.layernorm2(x + block.dropout2(block.ffn(x), training=False))
        return classifier(net[:, 0]), captured

    totals = [dict(layer=i, error_sum_sq=0., reference_sum_sq=0., elements=0,
                   x_saturated=0, y_saturated=0, w_saturated=params[i][2], b_saturated=params[i][3],
                   max_abs_x=0., max_abs_y=0., max_sample_nrmse=-1., worst_sample=None,
                   samples_over_3_percent=0) for i in range(12)]
    worst = [None] * 12
    confusion = np.zeros((12, 12), dtype=np.int64)
    predictions, suites = [], []
    start = time.monotonic()
    preprocessing_checks = 0
    for n, sample in enumerate(samples):
        if sample['class_id'] == 0:
            audio = np.zeros(16000, dtype=np.float32)
            sample['sha256'] = hashlib.sha256(audio.tobytes()).hexdigest()
            sample['sha256_scope'] = '16000 float32 zero samples'
        else:
            path = a.data / 'validation' / sample['path']
            assert sample['path'] in validation and sample['path'] not in testing
            with wave.open(str(path), 'rb') as wav:
                assert wav.getnchannels() == 1 and wav.getsampwidth() == 2 and wav.getframerate() == 16000
                pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2')
            audio = np.zeros(16000, dtype=np.float32)
            audio[:min(len(pcm), 16000)] = pcm[:16000].astype(np.float32) / 32768.
            sample['sha256'], sample['original_samples'] = sha(path), len(pcm)
            feed = {upstream.wav_filename_placeholder_: str(path),
                    upstream.time_shift_padding_placeholder_: [[0, 0], [0, 0]],
                    upstream.time_shift_offset_placeholder_: [0, 0],
                    upstream.foreground_resampling_placeholder_: 1.,
                    upstream.foreground_volume_placeholder_: 1.,
                    upstream.background_data_placeholder_: np.zeros([16000, 1], dtype=np.float32),
                    upstream.background_volume_placeholder_: 0.}
            official_audio = preprocessing_session.run(upstream.output_, feed_dict=feed)
            assert np.array_equal(audio, official_audio), 'PCM preprocessing differs from pinned upstream'
            preprocessing_checks += 1
        audio_tensor = tf.constant(audio[None, :])
        logits = model(audio_tensor, training=False)
        if isinstance(logits, (list, tuple)):
            logits = logits[0]
        logits, captured = (logits.numpy(), replay(audio_tensor))
        replayed, captured = captured
        assert np.array_equal(logits, replayed.numpy()), 'Dense capture replay changed native model logits'
        assert np.isfinite(logits).all()
        pred = int(np.argmax(logits[0]))
        confusion[sample['class_id'], pred] += 1
        rec = dict(sample_id=n, truth=sample['label'], prediction=labels[pred], layer_nrmse=[])
        suite = a.out / 'rtl' / ('class_%02d' % n) if n < 12 else None
        sats = []
        for i, (x, reference) in enumerate(captured):
            assert x.shape == (99, 64) and reference.shape == (99, 256)
            xi, xs = encode(x, 16, 11)
            wi, bi, _, _ = params[i]
            acc = xi @ wi + bi
            assert np.all(acc >= -(1 << 39)) and np.all(acc < (1 << 39))
            yi, sat = rne_array(acc)
            ref = reference.astype(np.float64)
            decoded = yi.astype(np.float64) / 2048.
            assert np.isfinite(ref).all()
            err_sq = float(np.sum((decoded - ref) ** 2))
            ref_sq = float(np.sum(ref ** 2))
            nrmse = (err_sq / ref.size) ** .5 / max((ref_sq / ref.size) ** .5, 1e-8)
            rec['layer_nrmse'].append(nrmse)
            t = totals[i]
            t['error_sum_sq'] += err_sq
            t['reference_sum_sq'] += ref_sq
            t['elements'] += ref.size
            t['x_saturated'] += xs
            t['y_saturated'] += int(sat.sum())
            t['max_abs_x'] = max(t['max_abs_x'], float(np.max(np.abs(x))))
            t['max_abs_y'] = max(t['max_abs_y'], float(np.max(np.abs(ref))))
            t['samples_over_3_percent'] += int(nrmse > .03)
            data = (xi, reference, yi, acc, sat)
            if nrmse > t['max_sample_nrmse']:
                t['max_sample_nrmse'], t['worst_sample'] = nrmse, n
                worst[i] = data
            if suite is not None:
                sats.append(export_layer(suite, i, data, params))
        if suite is not None:
            hexfile(suite / 'matrix_sat.hex', sats, 32)
            suites.append(dict(name=suite.name, samples=[n] * 12, layers=list(range(12))))
        predictions.append(rec)
        if n < 12 or (n + 1) % 25 == 0:
            print('captured %d/%d truth=%s predicted=%s elapsed=%.1fs' %
                  (n + 1, len(samples), sample['label'], labels[pred], time.monotonic() - start), flush=True)
    preprocessing_session.close()
    worst_dir = a.out / 'rtl/worst'
    worst_sats = [export_layer(worst_dir, i, data, params) for i, data in enumerate(worst)]
    hexfile(worst_dir / 'matrix_sat.hex', worst_sats, 32)
    suites.append(dict(name='worst', samples=[t['worst_sample'] for t in totals], layers=list(range(12))))
    for t in totals:
        t['nrmse'] = (t['error_sum_sq'] / t['elements']) ** .5 / max((t['reference_sum_sq'] / t['elements']) ** .5, 1e-8)
    source_files = list((ROOT / 'rtl').glob('*.sv')) + [Path(__file__).resolve(), ROOT / 'py/numeric_model.py',
        repo / 'kws_streaming/data/input_data.py', repo / 'kws_streaming/models/kws_transformer.py',
        repo / 'kws_streaming/models/transformer_utils.py', source / 'flags.json', source / 'labels.txt']
    source_files += list(source.glob('best_weights*'))
    report = dict(dataset=json.loads((a.data / 'download.json').read_text()),
        qualification='Self-selected validation regression; NOT organizer official 600-sample acceptance',
        seed=SEED, classes=labels, samples=len(samples), real_distinct_wavs=11 * a.per_class,
        zero_silence_cases=a.per_class, per_class=a.per_class,
        testing_audio_used=False, numerical_format_changed=False,
        tensorflow=tf.__version__, tensorflow_addons=tfa.__version__,
        checkpoint_tensor_equality=checkpoint_audit,
        preprocessing_bit_equal_checks=preprocessing_checks,
        native_model_replay_logits_bit_equal_checks=len(samples), rne_oracle_checks=rne_checks,
        rtl_export_oracle_checked_matrices=12 * len(suites),
        layers=totals, max_layer_nrmse=max(t['nrmse'] for t in totals),
        max_single_case_nrmse=max(t['max_sample_nrmse'] for t in totals),
        precision_pass=all(t['nrmse'] <= .03 for t in totals),
        all_individual_cases_pass=all(t['samples_over_3_percent'] == 0 for t in totals),
        float_model_correct=int(np.trace(confusion)), float_model_accuracy=float(np.trace(confusion) / len(samples)),
        float_confusion_matrix=confusion.tolist(),
        classification_scope='Original floating model only; NOT RTL end-to-end classification',
        rtl_suites=suites, source_sha256={str(f.relative_to(ROOT.parent)).replace('\\', '/'): sha(f) for f in source_files},
        elapsed_seconds=time.monotonic() - start)
    for name, obj in [('report.json', report), ('manifest.json', samples), ('predictions.json', predictions)]:
        (a.out / name).write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')
    print('max layer NRMSE %.8f%%; max sample/layer %.8f%%' %
          (100 * report['max_layer_nrmse'], 100 * report['max_single_case_nrmse']), flush=True)
    assert report['precision_pass'] and report['all_individual_cases_pass'], 'Precision gate failed'
    print('ALL PASS, %d/%d sample-layer numeric cases; RTL simulation is separate' %
          (len(samples) * 12, len(samples) * 12), flush=True)


if __name__ == '__main__':
    main()
