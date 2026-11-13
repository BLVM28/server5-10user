"""Read row-major 32-bit hex words as a full signed 16/F11 output matrix."""
import argparse
from pathlib import Path
import numpy as np

def decode(words, low_first=True):
    words=np.asarray(words,dtype=np.uint32).reshape(-1)
    if words.size!=12672: raise ValueError('Expected exactly 12672 data words')
    halves=np.column_stack((words & 65535,words >> 16)).astype(np.int64)
    if not low_first: halves=halves[:,::-1]
    return ((halves ^ 32768)-32768).reshape(99,256).astype(np.int16)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hex',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--high-first',action='store_true')
    a=p.parse_args()
    values=[int(line.strip(),16) for line in a.hex.read_text().splitlines() if line.strip() and not line.lstrip().startswith('//')]
    if any(x<0 or x>0xffffffff for x in values): raise ValueError('Not a 32-bit word')
    y=decode(values,not a.high_first)
    np.save(a.out,y.astype(np.float64)/2048.)
    print('RAW_OUTPUT_READ_PASS values=25344 shape=99x256 finite=1')
if __name__=='__main__': main()
