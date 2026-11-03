"""Full packed task with same-cycle ICB responses, a stress test outside the timing benchmark."""
from qualify import ROOT,load_flow,digest
def main():
    flow=load_flow()
    flow.OUT=ROOT/"build/fast_return";top="tb_kwt_fast_return"
    flow.compile_one(top)
    out=flow.OUT/"run"
    log=flow.run([flow.OUT/"compile"/top/"simv"],out,"run","ALL PASS, 1/1")
    assert "reads=11624" in log
    flow.save(out/"verified.json",{"passed":True,"rtl":flow.source_hashes(),"signature":flow.signature(top),
                                   "log_sha256":digest(out/"run.log")})
    print("FAST RETURN PASS",flush=True)
if __name__=="__main__":main()
