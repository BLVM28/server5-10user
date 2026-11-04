"""Replay the frozen self-selected validation set and compare Precision42 decoded Dense1 against the original float model."""
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
from numeric_model import encode, quantize
from rice import math_layer
from precision_metrics import nrmse_from_sums, REFERENCE_RMS_FLOOR

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
        exported = np.load(ROOT.parent / 'v2/vec/weights' / ('layer%02d.npz' % i))
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
    profiles=json.loads((ROOT/'py/profile42.json').read_text())['profiles']
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
        for i,(x,reference) in enumerate(captured):
            xi,_=encode(x,16,11)
            wi,bi,_,_=params[i]
            sx,sw,sy=profiles[i]["shifts"]
            yc=math_layer(xi,wi,bi,sx,sw,sy)[4]
            decoded=(yc<<sy).astype(np.float64)/2048.
            ref=reference.astype(np.float64)
            assert np.isfinite(decoded).all() and np.isfinite(ref).all()
            err=float(np.sum((decoded-ref)**2)); energy=float(np.sum(ref**2))
            ratio=nrmse_from_sums(err,energy,ref.size)
            t=totals[i];t["error_sum_sq"]+=err;t["reference_sum_sq"]+=energy;t["elements"]+=ref.size
            t["max_sample_nrmse"]=max(t["max_sample_nrmse"],ratio)
            t["samples_over_3_percent"]+=int(ratio>.03)
            rec["layer_nrmse"].append(ratio)
        predictions.append(rec)
        if (n+1)%50==0:print("SPEECH",n+1,flush=True)
    preprocessing_session.close()
    for t in totals:
        t["nrmse"]=nrmse_from_sums(t["error_sum_sq"],t["reference_sum_sq"],t["elements"])
    report={"scope":"self-selected validation only; original float model and per-layer Dense1 decoded comparison",
            "samples":len(samples),"real_distinct_wavs":11*a.per_class,"silence_copies":a.per_class,
            "checkpoint_tensors":len(checkpoint_audit),"native_logits_replays":len(samples),
            "max_layer_nrmse":max(t["nrmse"] for t in totals),"max_single_nrmse":max(t["max_sample_nrmse"] for t in totals),
            "cases_over_3_percent":sum(t["samples_over_3_percent"] for t in totals),
            "layers":[[t["layer"],t["nrmse"],t["max_sample_nrmse"]] for t in totals],
            "rice_sha256":sha(ROOT/"py/rice.py"),"profile_sha256":sha(ROOT/"py/profile42.json"),
            "nrmse_definition":"RMSE(error) / max(RMS(reference), 1e-8)",
            "reference_rms_floor":REFERENCE_RMS_FLOOR,
            "metric_sha256":sha(ROOT/"py/precision_metrics.py"),
            "qualification_script_sha256":sha(Path(__file__)),
            "elements_per_layer":[t["elements"] for t in totals]}
    assert len(predictions)==len(samples)
    (a.out/"cases.json").write_text(json.dumps(predictions,indent=2)+"\n")
    (a.out/"accuracy.json").write_text(json.dumps(report,indent=2)+"\n")
    print("SPEECH RESULT",json.dumps(report),flush=True)
    assert report["max_layer_nrmse"]<=.003 and report["cases_over_3_percent"]==0
if __name__=="__main__":main()
