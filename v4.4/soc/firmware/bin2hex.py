"""Encode the RV32 little-endian boot image for the existing ITCM load port."""
from pathlib import Path
import struct
import sys

raw = Path(sys.argv[1]).read_bytes()
if len(raw) > 4096 * 4:
    raise ValueError("The verification image exceeds the boot loader window")
raw += bytes((-len(raw)) % 4)
Path(sys.argv[2]).write_text("".join("{:08x}\n".format(word[0]) for word in struct.iter_unpack("<I", raw)))
