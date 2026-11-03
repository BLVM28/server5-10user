"""One complete cold packed Dense1 task per SDF corner, checked at the pins."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
from pathlib import Path
import re
import shutil
from daily import timing,implementation
from qualify import ROOT,TOP,digest,load_flow

def main(period):
    flow=load_flow()
    # Build and annotate under a dedicated private run root so the read-only
    # VCS speech regression can continue in build/manual.
    flow.OUT=ROOT/"build/gate_sample"
    lock=ROOT/"build/gate_sample.lock"
    with lock.open("a") as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        net,_=implementation(flow,"rebuilt")
        timing(flow,"rebuilt",period)
        vec=ROOT/"vec/fast/worst"
        flow.gate(period,"rebuilt",vec,2,True)
        def sample(c):
            d=flow.OUT/"gate/rebuilt"/str(period)/(vec.name+"_"+c)
            out=d/"block8_layer00";out.mkdir(exist_ok=True)
            sdf=flow.OUT/"timing/rebuilt"/str(period)/(TOP+"_"+c)/"mapped.sdf"
            shutil.copy2(str(sdf),str(out/"mapped.sdf"))
            log=flow.run([d/"simv","+sdfverbose","+BLOCK8_OUTPUT","+LAYER=0","+VEC_DIR="+str(vec)],out,
                         "run","ALL PASS, 1/1",timeout=3600)
            if not re.search(r"Doing SDF annotation[^\r\n]*Done",log):raise ValueError("Runtime SDF missing")
            row=re.search(r"matrix gate layer 0 PASS writes=(\d+) transactions=(\d+)",log)
            if not row or int(row[1])!=6752 or int(row[2])!=12827:raise ValueError("Missing matrix evidence")
            rec={"corner":c,"layer":0,"writes":int(row[1]),"transactions":int(row[2]),"sdf_sha256":digest(sdf),
                 "netlist_sha256":digest(net),"log_sha256":digest(out/"run.log")}
            flow.save(out/"verified.json",rec)
            print("BLOCK8 GATE PASS",c,"layer 0",row.groups(),flush=True)
            return rec
        with ThreadPoolExecutor(max_workers=2) as pool:records=list(pool.map(sample,("ss","ff")))
        flow.save(flow.OUT/("sample_"+str(period)+".json"),records)
        if period==6.666667:
            flow.save(flow.OUT/"sample.json",records)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--period",type=float,default=6.666667)
    main(p.parse_args().period)
