"""One version-owned CLI for functional regression, timing and release evidence."""
import argparse,fcntl,json,math,os,re,shutil,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from qualify import ROOT,HOME,TOP,digest,load_flow,measure_corner,implementation_sources
from snapshot import validate
sys.path.insert(0,str(ROOT/"py"))
from scalar_vectors import verify,LABELS
TOPS={"tb_kwt_streams":29,"tb_kwt_wait":29,"tb_kwt_zero":29,"tb_kwt_public_sram":29}
def vec_for(label):return ROOT/"vec/streams"/label
def simulate(flow,top,label,wave=False):
    vec=vec_for(label);out=flow.OUT/"runs"/label/top
    flow.compile_one(top);proof=out/"verified.json"
    if proof.exists():proof.unlink()
    args=[flow.OUT/"compile"/top/"simv","+VEC_DIR="+str(vec)]
    if wave:args.append("+POWER")
    log=flow.run(args,out,"run","ALL PASS, 29/29")
    assert "STREAM GUARD PASS 25/25" in log
    assert re.findall(r"ALL PASS,\s*(\d+)/(\d+)",log)==[("29","29")]
    rows=[dict(layer=int(l),cycles=int(c),reads=int(r),writes=int(w),mode=int(m)) for l,c,r,w,m in
          re.findall(r"NICE_TIME layer=(\d+) cycles=(\d+) reads=(\d+) writes=(\d+) mode=(\d+)",log)]
    assert len(rows)==14 and [v["layer"] for v in rows[:12]]==list(range(12))
    nr=[int(v,16) for v in (vec/"reads.hex").read_text().split()]
    nw=[int(v,16) for v in (vec/"writes.hex").read_text().split()]
    mode={"tb_kwt_streams":0,"tb_kwt_wait":1,"tb_kwt_zero":2,"tb_kwt_public_sram":3}[top]
    assert all(v["reads"]==nr[v["layer"]] and v["writes"]==nw[v["layer"]] and v["mode"]==mode for v in rows)
    result={"passed":True,"top":top,"label":label,"rtl_sha256":flow.source_hashes(),"signature":flow.signature(top),
        "vectors_sha256":{p.name:digest(p) for p in vec.glob("*.hex")},"log_sha256":digest(out/"run.log"),"nice_cycles":rows}
    flow.save(proof,result)
    clocks=sum(v["cycles"] for v in rows[:12])
    print("FUNCTION PASS",label,top,"29/29 plus guards25/25",flush=True)
    print("MEASURE",label,top,clocks,"cycles, %.2f tasks/s at 150 MHz"%(1800000000./clocks),flush=True)
    return result
def record(flow,top,label):
    path=flow.OUT/"runs"/label/top;result=json.loads((path/"verified.json").read_text())
    assert result["passed"] and result["rtl_sha256"]==flow.source_hashes() and result["signature"]==flow.signature(top)
    assert result["log_sha256"]==digest(path/"run.log")
    assert result["vectors_sha256"]=={p.name:digest(p) for p in vec_for(label).glob("*.hex")}
    return result
def implementation(flow):
    core=flow.selected_netlist("rebuilt")/"synth_kwt_nice_core"
    return core/"mapped.v",validate(core,implementation_sources())
def timing(flow,period,require=True):
    net,q=implementation(flow);libs=flow.libs();records=[]
    for corner in ("ss","ff"):
        d=flow.OUT/"timing/rebuilt"/str(period)/(TOP+"_"+corner)
        point=measure_corner(flow,libs,net,d,corner,period)
        point.update({"passed":point["timing_pass"],"directory":str(d),"netlist_sha256":digest(net),
            "sdf_sha256":digest(d/"mapped.sdf")})
        records.append(point)
    flow.save(flow.OUT/("timing_rebuilt_"+str(period)+".json"),records)
    if require and not all(p["passed"] for p in records):raise ValueError("Timing failed")
    return records
def main():
    p=argparse.ArgumentParser();p.add_argument("target");p.add_argument("--period",type=float,default=6.666667);p.add_argument("--jobs",type=int,default=2)
    a=p.parse_args();assert ROOT==HOME/"v4.3" and 1<=a.jobs<=4 and a.period>0 and math.isfinite(a.period)
    (ROOT/"build").mkdir(exist_ok=True);lock=(ROOT/".manual.lock").open("a");fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    f=load_flow()
    if a.target=="env":
        for name in ("python3","make","vcs","dc_shell","pt_shell","fm_shell","verdi"):
            assert shutil.which(name);print(name,shutil.which(name))
        f.libs();print("ENV PASS")
    elif a.target=="vectors":verify()
    elif a.target=="compile":
        for top in TOPS:f.compile_one(top)
        print("COMPILE PASS",len(TOPS))
    elif a.target in ("run","regress","precision","paired"):
        verify()
        if a.target=="regress":
            jobs=[(t,k) for k in LABELS for t in ("tb_kwt_streams","tb_kwt_wait")]
            jobs.append(("tb_kwt_zero","worst"))
            jobs.append(("tb_kwt_public_sram","worst"))
            with ThreadPoolExecutor(max_workers=a.jobs) as pool:
                for future in [pool.submit(simulate,f,*job) for job in jobs]:future.result()
            print("FUNCTION ALL PASS",len(jobs),"suites")
        elif a.target=="paired":
            from paired43 import run_reference
            run_reference();simulate(f,"tb_kwt_public_sram","worst")
        else:
            tops=TOPS if a.target in ("run","paired") else ("tb_kwt_streams",)
            for top in tops:simulate(f,top,"worst")
    elif a.target=="waves":
        top="tb_kwt_streams";f.compile_one(top)
        d=f.OUT/"waves";d.mkdir(parents=True,exist_ok=True)
        f.run([f.OUT/"compile"/top/"simv","+POWER","+LAYER=0","+VEC_DIR="+str(vec_for("worst"))],d,"run","ALL PASS, 1/1")
        wave=d/"task.vcd";assert wave.stat().st_size>100000
        f.save(d/"wave.json",{"rtl":f.source_hashes(),"vcd":digest(wave)})
        print("WAVES PASS",wave)
    elif a.target=="verdi":
        d=f.OUT/"waves";wave=d/"task.vcd"
        assert wave.is_file(),"Run make waves first"
        q=json.loads((d/"wave.json").read_text());assert q["rtl"]==f.source_hashes() and q["vcd"]==digest(wave),"Stale wave; run make waves"
        temporary=d/"tmp";temporary.mkdir(exist_ok=True)
        env=dict(os.environ,**{k:str(temporary) for k in ("TMP","TEMP","TMPDIR")})
        with (d/"verdi.log").open("w") as stream:
            subprocess.Popen(["verdi","-ssf",str(wave)],cwd=str(d),env=env,stdout=stream,stderr=subprocess.STDOUT)
        print("VERDI STARTED",wave)
    elif a.target=="sweep":
        for period in (6.666667,6.25,5.882353,5.555556):timing(f,period,False)
    elif a.target=="synth":subprocess.run([sys.executable,"-B",str(ROOT/"server_eda/qualify.py")],check=True)
    elif a.target in ("timing","sta"):timing(f,a.period)
    elif a.target=="report":
        for top in TOPS:record(f,top,"worst");print("FUNCTION PASS",top)
        net,_=implementation(f)
        points=json.loads((f.OUT/("timing_rebuilt_"+str(a.period)+".json")).read_text())
        assert len(points)==2 and all(v["passed"] and v["netlist_sha256"]==digest(net) for v in points)
        q=json.loads((net.parent/"qualification.json").read_text())
        print("AREA um2",q["v43_area"],"macro um2",q["macro_area"])
        print("REPORT PASS: 150 MHz pre-layout, accelerator scope")
    elif a.target=="clean":
        out=f.OUT
        if out.exists():
            assert not out.is_symlink() and out.resolve()==ROOT/"build/manual"
            target=ROOT/"reports"/("before_clean_"+str(int(time.time()*1e6)))
            for path in out.rglob("*"):
                if path.is_file() and path.suffix in (".json",".log",".txt",".rpt"):
                    dest=target/path.relative_to(out);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(str(path),str(dest))
            shutil.rmtree(str(out))
        print("CLEAN PASS")
    elif a.target=="package":
        from assets import package
        package()
    else:raise ValueError("Unknown target "+a.target)
if __name__=="__main__":
    try:main()
    except Exception as e:print("FAIL",repr(e),file=sys.stderr);sys.exit(1)
