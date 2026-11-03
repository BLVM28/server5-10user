"""Capture training-only Dense1 float input/output pairs from the original unmodified KWT-1."""
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
    samples=json.loads((a.out/"selection.json").read_text())
    assert len(samples)==33
    for s in samples:assert input_data.which_set(s["path"],flags["validation_percentage"],flags["testing_percentage"])=="training"
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

    for n,sample in enumerate(samples):
        path=a.out/"audio"/sample["path"]
        assert sha(path)==sample["sha256"]
        feed={upstream.wav_filename_placeholder_:str(path),upstream.time_shift_padding_placeholder_:[[0,0],[0,0]],
              upstream.time_shift_offset_placeholder_:[0,0],upstream.foreground_resampling_placeholder_:1.,
              upstream.foreground_volume_placeholder_:1.,upstream.background_data_placeholder_:np.zeros([16000,1],dtype=np.float32),
              upstream.background_volume_placeholder_:0.}
        pcm=preprocessing_session.run(upstream.output_,feed_dict=feed).reshape(1,-1)
        logits,frames=replay(tf.constant(pcm));native=model(tf.constant(pcm),training=False)
        if isinstance(native,(list,tuple)):native=native[0]
        assert np.array_equal(native.numpy(),logits.numpy())
        np.savez(a.out/("sample_%02d.npz"%n),x=np.asarray([f[0] for f in frames]),y=np.asarray([f[1] for f in frames]))
    preprocessing_session.close()
    print("TRAIN FLOAT CAPTURE PASS",len(samples)*12,flush=True)
if __name__=="__main__":main()
