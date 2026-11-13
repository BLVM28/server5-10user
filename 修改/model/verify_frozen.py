"""Rebuild the 12 frozen matrix references from independent raw inputs."""
import hashlib
import json
from pathlib import Path

import numpy as np

from prepare_layer import hex_bytes, input_files, load_profiles, reference_files


def signed_halfwords(path, shape):
    words = read_words(path)
    pairs = np.column_stack((words & 65535, words >> 16))
    return ((pairs ^ 32768) - 32768).reshape(shape)


def read_words(path):
    return np.array([int(line, 16) for line in path.read_bytes().splitlines()], dtype=np.int64)


def main():
    vectors = Path(__file__).resolve().parents[1] / "verification/vec"
    manifest = json.loads((vectors / "manifest.json").read_text(encoding="utf-8"))
    for group, count in (("raw", 36), ("worst", 100)):
        if len(manifest[group]) != count:
            raise ValueError(f"Unexpected manifest count for {group}")
        for name, digest in manifest[group].items():
            if hashlib.sha256((vectors / group / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f"Frozen vector changed: {group}/{name}")

    rebuilt = {}
    counters = {"matrix_sat": [], "reads": [], "writes": [], "params": []}
    for layer, profile in enumerate(load_profiles()):
        stem = f"layer{layer:02d}_"
        raw = vectors / "raw"
        x = signed_halfwords(raw / f"{stem}x.hex", (99, 64))
        w = signed_halfwords(raw / f"{stem}w.hex", (64, 256))
        b = (read_words(raw / f"{stem}b.hex") ^ 0x80000000) - 0x80000000
        files, stats = reference_files(x, w, b, profile)
        for name, contents in input_files(x, w, b, profile).items():
            if contents != files[name]:
                raise ValueError(f"Input-only encoder differs at layer {layer}: {name}")
        rebuilt.update({stem + name + ".hex": contents for name, contents in files.items()})
        for key, value in stats.items():
            counters[key].append(value)
        sx, sw, sy = profile["shifts"]
        counters["params"].append(sx | (sw << 4) | (sy << 8))

    rebuilt.update({name + ".hex": hex_bytes(values) for name, values in counters.items()})
    if rebuilt.keys() != manifest["worst"].keys():
        raise ValueError("Rebuilt vector names differ from the manifest")
    for name, contents in rebuilt.items():
        if contents != (vectors / "worst" / name).read_bytes():
            raise ValueError(f"Reference mismatch: {name}")
    print("MODEL_FROZEN_PASS layers=12 raw_files=36 hex_files=100")


if __name__ == "__main__":
    main()
