"""Prepare RTL input slots or generate an offline bit-accurate reference."""
import argparse
import json
from pathlib import Path

import numpy as np

from numeric_model import encode
from streams43 import FORMAT, frame, input_words


def load_profiles():
    path = Path(__file__).with_name("profile42.json")
    return json.loads(path.read_text(encoding="utf-8"))["profiles"]


def hex_bytes(values, bits=32):
    mask = (1 << bits) - 1
    return "".join(f"{int(value) & mask:0{bits // 4}x}\n" for value in np.asarray(values).flat).encode("ascii")


def packed_int16(values):
    halfwords = np.asarray(values, dtype=np.int64).ravel() & 65535
    return halfwords[::2] | (halfwords[1::2] << 16)


def input_files(x, w, b, profile):
    return {name: hex_bytes(values) for name, values in zip(("x", "w", "b"), input_words(x, w, b, profile))}


def reference_files(x, w, b, profile):
    xx, ww, bias, acc, y, wire, decoded, sat, reads, groups = frame(x, w, b, profile)
    files = {"x": hex_bytes(xx), "w": hex_bytes(ww), "b": hex_bytes(bias), "acc": hex_bytes(acc, 40),
             "y": hex_bytes(packed_int16(y)), "wire": hex_bytes(wire),
             "decoded": hex_bytes(packed_int16(decoded)), "groups": hex_bytes(groups, 16)}
    return files, {"matrix_sat": sat, "reads": reads, "writes": sum(groups)}


def checked_integer(array, shape, bits, name):
    if array.shape != shape or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{name} must be an integer array with shape {shape}")
    bound = 1 << (bits - 1)
    if int(array.min()) < -bound or int(array.max()) >= bound:
        raise ValueError(f"{name} is out of signed {bits}-bit range")
    return array.astype(np.int64)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inputs", "reference"))
    parser.add_argument("--layer", type=int, choices=range(12), required=True)
    parser.add_argument("--x", type=Path, required=True, help="X matrix in .npy format")
    parser.add_argument("--x-kind", choices=("float", "integer"), default="float")
    parser.add_argument("--parameters", type=Path, required=True, help="Layer .npz from export_weights.py")
    parser.add_argument("--out", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    x = np.load(args.x, allow_pickle=False)
    if x.shape != (99, 64):
        raise ValueError("X must have shape (99, 64)")
    input_saturated = 0
    if args.x_kind == "float":
        if not np.issubdtype(x.dtype, np.floating):
            raise ValueError("Use --x-kind integer for fixed-point X")
        x, input_saturated = encode(x, 16, 11)
    else:
        x = checked_integer(x, (99, 64), 16, "X")
    with np.load(args.parameters, allow_pickle=False) as params:
        w = checked_integer(params["w"], (64, 256), 16, "W")
        b = checked_integer(params["b"], (256,), 32, "bias")
    profile = load_profiles()[args.layer]
    sx, sw, sy = profile["shifts"]
    metadata = {"mode": args.mode, "layer": args.layer, "format_id": f"0x{FORMAT:08x}",
                "shifts": [sx, sw, sy], "scale_word": sx | (sw << 4) | (sy << 8),
                "pack_low_first": 1, "input_saturated": input_saturated}
    if args.mode == "inputs":
        files = input_files(x, w, b, profile)
    else:
        files, stats = reference_files(x, w, b, profile)
        metadata.update(stats)
    args.out.mkdir(parents=True, exist_ok=False)
    for name, contents in files.items():
        (args.out / f"layer{args.layer:02d}_{name}.hex").write_bytes(contents)
    (args.out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"LAYER_{args.mode.upper()}_PASS layer={args.layer} hex_files={len(files)}")


if __name__ == "__main__":
    main()
