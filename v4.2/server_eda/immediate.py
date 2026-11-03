"""Same-cycle response tests in a dedicated run directory."""
from qualify import ROOT,load_flow,digest
def main():
    f=load_flow();f.OUT=ROOT/"build/immediate"
    for top,n in (("tb_kwt_stream_dot",64),("tb_kwt_rice_codec",1542),("tb_kwt_fast_return",1),("tb_kwt_block8_immediate",12),("tb_kwt_precision_immediate",12)):
        f.compile_one(top);d=f.OUT/top
        image=f.OUT/"compile"/top/"simv"
        log=f.run([image,"+VEC_DIR="+str(ROOT/"vec/precision/worst" if top=="tb_kwt_precision_immediate" else ROOT.parent/"v4.1/vec/fast/worst")],d,"run","ALL PASS, %d/%d"%(n,n))
        f.save(d/"verified.json",{"rtl":f.source_hashes(),"signature":f.signature(top),"log_sha256":digest(d/"run.log"),"count":n})
        print("IMMEDIATE PASS",top,n,flush=True)
if __name__=="__main__":main()
