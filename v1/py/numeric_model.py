"""Bit-accurate S1 v0.1 integer model. No TensorFlow dependency."""
from fractions import Fraction
import numpy as np

FORMAT_ID = 0x00010000

def encode(values, bits, frac):
    values = np.asarray(values, dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError('Non-finite input')
    rounded = np.rint(np.ldexp(values, frac))
    low, high = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    saturated = int(np.count_nonzero((rounded < low) | (rounded > high)))
    return np.clip(rounded, low, high).astype(np.int64), saturated

def quantize(acc):
    """Independent mathematical oracle: Fraction rounding handles signed ties."""
    rounded = round(Fraction(int(acc), 1 << 16))
    return min(32767, max(-32768, rounded)), not -32768 <= rounded <= 32767

def linear(x, w, b):
    x, w, b = (np.asarray(v, dtype=np.int64) for v in (x, w, b))
    if x.shape != (99, 64) or w.shape != (64, 256) or b.shape != (256,):
        raise ValueError('Expected X(99,64), W(64,256), b(256,)')
    for data, bits in ((x,16),(w,16),(b,32)):
        if np.any(data < -(1 << (bits-1))) or np.any(data >= (1 << (bits-1))):
            raise ValueError('Integer input out of signed range')
    acc = x @ w + b
    pairs = [quantize(a) for a in acc.flat]
    y = np.array([p[0] for p in pairs], dtype=np.int16).reshape(99,256)
    sat = np.array([p[1] for p in pairs], dtype=bool).reshape(99,256)
    return y, acc, sat

def layer_nrmse(decoded, reference):
    """Inputs include every sample of ONE layer; do not average sample NRMSE."""
    a,b=np.asarray(decoded,dtype=np.float64),np.asarray(reference,dtype=np.float64)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Invalid shapes or non-finite values')
    return float(np.sqrt(np.mean((a-b)**2))/max(np.sqrt(np.mean(b*b)),1e-8))
