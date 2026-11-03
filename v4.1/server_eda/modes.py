from qualify import ROOT,load_flow,digest
if __name__=="__main__":
    f=load_flow();f.OUT=ROOT/"build/modes";top="tb_kwt_modes"
    f.compile_one(top);d=f.OUT/"run"
    f.run([f.OUT/"compile"/top/"simv"],d,"run","ALL PASS, 5/5")
    f.save(d/"verified.json",{"rtl":f.source_hashes(),"signature":f.signature(top),"log_sha256":digest(d/"run.log")})
    print("MODES PASS 5/5",flush=True)
