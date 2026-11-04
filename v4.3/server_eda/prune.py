"""Use physical zero-load reports to remove dead mapped logic, then prove the ECO with Formality."""
import hashlib,json,re
from pathlib import Path
def prune(flow,libs,root,work,mapped,env,measure):
    from qualify import digest
    net=mapped/"mapped.v"
    check=mapped/"sta_6.666667_ss"
    report=check/"violations.rpt"
    if not report.exists():measure(flow,libs,net,check,"ss",6.666667)
    text=report.read_text()
    pins=[];group=""
    for line in text.splitlines():
        t=line.strip()
        if not t:continue
        if t in ("min_capacitance","max_capacitance","min_transition","max_transition","max_delay/setup","min_delay/hold"):
            group=t
        if group=="min_capacitance" and "VIOLATED" in t:
            vals=t.split()
            if len(vals)>=4 and float(vals[-3])==0.0:
                pin=vals[-5] if len(vals)>=5 else prev
                if "/" not in pin:raise ValueError("Ambiguous zero-load pin: "+str((prev,t)))
                pins.append(pin)
        prev=t
    if not pins:
        return mapped,[]
    assert len(pins)==len(set(pins)) and len(pins)<=64
    scripts=[root/"server_eda"/s for s in ("prune.tcl","prune_equiv.tcl","prune.py")]
    identity=hashlib.sha256((digest(net)+"".join(map(digest,scripts))+"\n".join(sorted(pins))).encode()).hexdigest()[:16]
    dest=work/("prune_"+identity);dest.mkdir(parents=True,exist_ok=True)
    plan=dest/"input_pins.txt";plan.write_text("\n".join(sorted(pins))+"\n")
    fixed=dest/"mapped.v";proof=dest/"formal_receipt.json"
    if proof.is_file():
        receipt=json.loads(proof.read_text())
        assert receipt["before"]==digest(net) and receipt["after"]==digest(fixed) and receipt["log"]==digest(dest/"formal/fm.log")
    else:
        flow.run(["dc_shell","-f",scripts[0]],dest,"dc","DEAD_OUTPUT_CLEANUP_PASS",
                 dict(env,KWT_DDC=str(mapped/"mapped.ddc"),KWT_PRUNE_TARGETS=str(plan)))
        flow.run(["fm_shell","-f",scripts[1]],dest/"formal","fm","FORMAL_EQUIVALENCE_PASS",
                 dict(env,KWT_REFERENCE_NET=str(net),KWT_FINAL_NET=str(fixed)))
        receipt={"before":digest(net),"after":digest(fixed),"log":digest(dest/"formal/fm.log"),"input_pins":pins}
        flow.save(proof,receipt)
    changes=[row.split() for row in (dest/"pruned.txt").read_text().splitlines()]
    flow.save(dest/"resize_audit.json",{"original_sha256":digest(net),"final_sha256":digest(fixed),
              "changes":changes,"method":"dead-cell-removal-formality","formal":receipt})
    print("FORMAL ECO PASS",len(pins),"zero-load pins",len(changes),"unused cells",flush=True)
    return dest,changes
