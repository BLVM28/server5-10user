"""Replay all frozen matrices with the original Fraction-based Dense1 reference; never rewrite golden vectors."""
import hashlib
import json
from pathlib import Path

import numpy as np

from assets import vectors
from numeric_model import linear

ROOT = Path(__file__).resolve().parents[1]


def read_hex(path):
    return np.array([int(x, 16) for x in path.read_bytes().splitlines()], dtype=np.int64)


def signed(values, bits):
    sign_bit = 1 << (bits - 1)
    return (values ^ sign_bit) - sign_bit


def unpack16(words):
    halves = np.column_stack((words & 65535, words >> 16)).reshape(-1)
    return signed(halves, 16)


def main():
    vectors()
    groups = ["base"] + ["class_%02d" % i for i in range(12)] + ["worst"]
    verified = {}
    for name in groups:
        vec = ROOT/"vec" if name == "base" else ROOT/"vec/real_speech"/name
        sat_counts = read_hex(vec/"matrix_sat.hex")
        for layer in range(12):
            stem = "layer%02d_" % layer
            x = unpack16(read_hex(vec/(stem+"x.hex"))).reshape(99,64)
            w = unpack16(read_hex(vec/(stem+"w.hex"))).reshape(64,256)
            b = signed(read_hex(vec/(stem+"b.hex")),32)
            y, acc, saturated = linear(x,w,b)
            np.testing.assert_array_equal(acc.ravel(), signed(read_hex(vec/(stem+"acc.hex")),40))
            np.testing.assert_array_equal(y.ravel(), unpack16(read_hex(vec/(stem+"y.hex"))))
            assert int(saturated.sum()) == sat_counts[layer], (name,layer)
        verified[name] = 12
    count = sum(verified.values())
    result = {"tasks_by_set":verified,"tasks":count,"acc40_elements":count*99*256,
              "int16_elements":count*99*256,"saturation_counters":count,
              "model_sha256":hashlib.sha256((ROOT/"py/numeric_model.py").read_bytes()).hexdigest(),
              "vector_manifest_sha256":hashlib.sha256((ROOT/"py/vector_manifest.json").read_bytes()).hexdigest()}
    (ROOT/"results/numeric.json").write_bytes((json.dumps(result,indent=2)+"\n").encode("utf-8"))
    print("NUMERIC PASS",count,"tasks,",result["int16_elements"],"full accumulators and outputs")


if __name__ == "__main__":
    main()
