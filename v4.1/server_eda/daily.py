"""v4.1 VCS/PT entry points. All writes are confined to this version under the team's home."""
import argparse,fcntl,json,math,re,shutil,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from qualify import ROOT,HOME,TOP,digest,load_flow,measure_corner,implementation_sources
from snapshot import validate
sys.path.insert(0,str(ROOT/"py"))
from scalar_vectors import verify,LABELS
COUNTS={"tb_kwt_arithmetic":260,"tb_v3_carries":7,"tb_kwt_icb":4,"tb_kwt_system":29,"tb_kwt_overlap":5,
        "tb_kwt_negative":58,"tb_kwt_mul_pipeline":524288,"tb_kwt_codec":4096,"tb_kwt_compact":29,
        "tb_kwt_block8":29,"tb_kwt_bfp_codec":65536}
RAW=ROOT.parent/"v2/vec"
def vec_for(top,label):
    if top.startswith("tb_kwt_block8"):return ROOT/"vec/fast"/label
    return RAW if label=="base" else RAW/"real_speech"/label
def simulate(flow, top, vec, label, wave=False):
    out=flow.OUT/"runs"/label/top
    proof=out/"verified.json"
    if proof.exists():proof.unlink()
    flow.compile_one(top)
    cmd=[flow.OUT/"compile"/top/"simv","+VEC_DIR="+str(vec.resolve())]
    if wave:cmd.append("+WAVES")
    log=flow.run(cmd,out,"run","ALL PASS,")
    counts=re.findall(r"ALL PASS,\s*(\d+)/(\d+)",log)
    if counts!=[(str(COUNTS[top]),str(COUNTS[top]))]:
        raise ValueError("Unexpected PASS count for "+top)
    extra={"tb_kwt_overlap":"PAGE PASS 2/2","tb_kwt_compact":"COMPACT GUARD PASS 2/2",
           "tb_kwt_mul_pipeline":"total_checked=527566"}
    if top.startswith("tb_kwt_block8"):assert "BLOCK8 GUARD PASS 4/4" in log
    if top in extra and extra[top] not in log:raise ValueError("Missing coverage: "+top)
    matrices=[dict(layer=int(a),core_cycles=int(b),writes=int(c)) for a,b,c in
        re.findall(r"matrix layer (\d+) PASS core_cycles=(\d+) writes=(\d+)",log)]
    timing=[dict(layer=int(a),cycles=int(b),reads=int(c),writes=int(d),compact=int(m)) for a,b,c,d,m in
        re.findall(r"NICE_TIME layer=(\d+) cycles=(\d+) reads=(\d+) writes=(\d+) compact=(\d+)",log)]
    if top in ("tb_kwt_system","tb_kwt_compact","tb_kwt_block8","tb_kwt_block8_immediate"):
        assert len(timing)==len(matrices)==14 and [x["layer"] for x in timing[:12]]==list(range(12))
        for t,m in zip(timing,matrices):
            assert t["layer"]==m["layer"] and t["writes"]==m["writes"] and t["reads"]==(6075 if top.startswith("tb_kwt_block8") else 11624)
            assert t["cycles"]>m["core_cycles"] and t["compact"]==(2 if top.startswith("tb_kwt_block8") else int(top=="tb_kwt_compact"))
            if top.startswith("tb_kwt_block8"):assert t["writes"]==6752
    result={"passed":True,"top":top,"counts":counts,"vector_dir":str(vec),"rtl_sha256":flow.source_hashes(),
            "vectors_sha256":{p.name:digest(p) for p in vec.glob("*.hex")},"log":str(out/"run.log"),
            "log_sha256":digest(out/"run.log"),"matrix_cycles":matrices,"nice_cycles":timing}
    flow.save(proof,result)
    print("FUNCTION PASS %s %s %d/%d"%(label,top,COUNTS[top],COUNTS[top]),flush=True)
    if timing:
        print("MEASURE %s %s 12 tasks NICE=%d core=%d writes=%d"%(label,top,sum(x["cycles"] for x in timing[:12]),
              sum(x["core_cycles"] for x in matrices[:12]),sum(x["writes"] for x in timing[:12])),flush=True)
    return result



def implementation(flow, name):
    core = flow.selected_netlist(name)/"synth_kwt_nice_core"
    q = validate(core,implementation_sources())
    return core/"mapped.v",q


def timing(flow, name, period, require_pass=True):
    stamp = flow.OUT/("timing_"+name+"_"+str(period)+".json")
    if stamp.exists():
        stamp.unlink()
    net,q = implementation(flow,name)
    libs = flow.libs()
    records = []
    for corner in ("ss","ff"):
        d = flow.OUT/"timing"/name/str(period)/(TOP+"_"+corner)
        point = measure_corner(flow,libs,net,d,corner,period)
        point.update({"top":TOP,"passed":point["timing_pass"],"directory":str(d),
                      "slacks_ns":point["setup_hold_ns"],"sdf_sha256":digest(d/"mapped.sdf"),
                      "netlist_sha256":digest(net)})
        records.append(point)
    flow.save(stamp,records)
    print("METRIC area=%.6f macro=%.6f v4_delta=%+.3f%%" %
          (q["v41_area"],q["macro_area"],100*(q["v41_area"]/q["v4_reference_area"]-1)))
    passed=all(p["passed"] for p in records)
    if require_pass and not passed:
        raise ValueError("Timing failed; see "+str(stamp))
    return passed



def clean(flow):
    out = flow.OUT
    if not out.exists():
        print("CLEAN PASS; nothing to clean");return
    if out.is_symlink() or out.resolve()!=ROOT/"build/manual":
        raise ValueError("Unexpected build directory")
    archive = ROOT/"reports"/("before_clean_"+str(int(time.time()*1000000)))
    for file in out.rglob("*"):
        if not file.is_symlink() and file.is_file() and file.suffix in (".log",".json",".rpt",".txt"):
            target = archive/file.relative_to(out)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(str(file),str(target))
    shutil.rmtree(str(out))
    print("CLEAN PASS; saved evidence in "+str(archive))



def record(flow,label,top):
    vec=vec_for(top,label);p=flow.OUT/"runs"/label/top
    j=json.loads((p/"verified.json").read_text())
    assert j["passed"] and j["counts"]==[[str(COUNTS[top]),str(COUNTS[top])]]
    assert j["rtl_sha256"]==flow.source_hashes() and j["log_sha256"]==digest(p/"run.log")
    assert json.loads((flow.OUT/"compile"/top/"signature.json").read_text())==flow.signature(top)
    assert Path(j["vector_dir"]).resolve()==vec.resolve()
    assert j["vectors_sha256"]=={f.name:digest(f) for f in vec.glob("*.hex")}
    return j

def report(flow,period):
    for top in COUNTS:
        j=record(flow,"base",top)
        print("FUNCTION PASS",top,j["counts"])
    net,q=implementation(flow,"rebuilt")
    points=json.loads((flow.OUT/("timing_rebuilt_"+str(period)+".json")).read_text())
    assert {p["corner"] for p in points}=={"ss","ff"} and len(points)==2
    for p in points:
        assert p["passed"] and p["netlist_sha256"]==digest(net) and p["sdf_sha256"]==digest(Path(p["directory"])/"mapped.sdf")
        print("TIMING PASS",p["corner"],period,p["setup_hold_ns"])
    print("BASIC CHECK PASS",flush=True)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("target");ap.add_argument("--period",type=float,default=6.666667)
    ap.add_argument("--jobs",type=int,default=2)
    a=ap.parse_args()
    assert ROOT==HOME/"v4.1" and 1<=a.jobs<=8 and math.isfinite(a.period) and a.period>0
    (ROOT/"build").mkdir(exist_ok=True)
    lock=(ROOT/".manual.lock").open("a");fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    f=load_flow()
    if a.target=="env":
        for name in ("python3","make","vcs","dc_shell","pt_shell","verdi"):
            assert shutil.which(name);print(name,shutil.which(name))
        assert all(Path(p).is_file() for p in f.libs()["standard"].values());print("ENV PASS")
    elif a.target=="clean":clean(f)
    elif a.target=="vectors":verify()
    elif a.target=="compile":
        for t in COUNTS:f.compile_one(t)
        print("COMPILE PASS",len(COUNTS))
    elif a.target in ("run","regress","paired","waves","negative"):
        verify()
        if a.target in ("run","regress"):
            for top in COUNTS:simulate(f,top,vec_for(top,"base"),"base")
            if a.target=="regress":
                jobs=[(t,vec_for(t,k),k) for k in LABELS[1:] for t in ("tb_kwt_system","tb_kwt_compact","tb_kwt_block8")]
                with ThreadPoolExecutor(max_workers=min(a.jobs,2)) as pool:
                    futures=[pool.submit(simulate,f,*job) for job in jobs]
                    for fut in futures:fut.result()
            print("FUNCTION ALL PASS",len(COUNTS)+(39 if a.target=="regress" else 0),"suites")
        elif a.target=="paired":
            for top in ("tb_kwt_system","tb_kwt_compact","tb_kwt_block8"):
                rec=simulate(f,top,vec_for(top,"worst"),"worst")
                n=sum(p["cycles"] for p in rec["nice_cycles"][:12])
                print("PAIRED",top,n,"clocks",round(1800000000.0/n,2),"tasks/s at 150 MHz",flush=True)
        elif a.target=="waves":simulate(f,"tb_kwt_system",RAW,"waves",True)
        else:simulate(f,"tb_kwt_negative",RAW,"negative")
    elif a.target=="verdi":
        path=f.OUT/"runs/waves/tb_kwt_system";wave=path/"waves.vcd"
        if not wave.is_file():raise ValueError("Run make waves first")
        with (path/"verdi.log").open("w") as log:
            subprocess.Popen(["verdi","-sv","+define+KWT_USE_FOUNDRY_SRAM","+define+ARM_UD_MODEL",
                              *map(str,f.sources("tb_kwt_system")),"-top","tb_kwt_system","-ssf",str(wave)],
                             cwd=str(path),stdout=log,stderr=subprocess.STDOUT)
    elif a.target=="timing":timing(f,"rebuilt",a.period)
    elif a.target=="report":report(f,a.period)
    elif a.target=="sweep":
        bad=[p for p in (6.666667,5.882353,5.555556,5.405405,5.263158,5.0,4.878049,4.761905)
             if not timing(f,"rebuilt",p,require_pass=False)]
        if bad:raise ValueError("Sweep complete; negative points: "+str(bad))
    elif a.target=="synth":
        core=ROOT/"implementation/rebuilt/synth_kwt_nice_core"
        if (core/"qualification.json").exists() and json.loads((core/"qualification.json").read_text())["sources"]==implementation_sources():
            print("SYNTH PASS",validate(core,implementation_sources())["mapped_sha256"])
        else:subprocess.run([sys.executable,str(ROOT/"server_eda/qualify.py"),"--periods","6.666667","5.882353","5.555556","5.405405","5.263158","5.0","4.878049","4.761905"],check=True)
    elif a.target=="package":
        from assets import package
        package()
    else:raise ValueError("Unknown target "+a.target)
if __name__=="__main__":
    try:main()
    except Exception as exc:print("FAIL",repr(exc),file=sys.stderr);sys.exit(1)
