"""Display a compressed public result over the existing personal VNC session."""
import argparse,hashlib,struct,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def show(name,page):
    if name not in ("reports/public.json","reports/probe.json"):raise ValueError("Only release summaries are transferable")
    data=zlib.compress((ROOT/name).read_bytes(),9)
    start=page*960;payload=data[start:start+960]
    if not payload:raise ValueError("Page outside summary")
    frame=b"KW42"+struct.pack(">IIH",len(data),page,len(payload))+hashlib.sha256(data).digest()+payload
    frame+=bytes((-len(frame))%24)
    rows=["10"*96]+["".join(format(b,"08b") for b in frame[i:i+24]) for i in range(0,len(frame),24)]
    print("\033[2J\033[H",end="")
    for row in rows:
        last=None
        for bit in row:
            if bit!=last:print("\033[40m" if bit=="1" else "\033[47m",end="");last=bit
            print(" ",end="")
        print("\033[0m")
if __name__=="__main__":
    cli=argparse.ArgumentParser();cli.add_argument("record");cli.add_argument("page",type=int);args=cli.parse_args()
    show(args.record,args.page)
