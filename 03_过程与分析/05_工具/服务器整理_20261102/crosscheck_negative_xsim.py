"""Use existing runner unchanged; pass its new TB an explicit vector directory."""
from pathlib import Path
import importlib.util,sys
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('kwt_xsim',ROOT/'v2/py/run_xsim.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
original=runner.subprocess.run
def run(command,*args,**kwargs):
    if any(str(x).lower().endswith('xsim.bat') for x in command):
        command=list(command)+['--testplusarg','VEC_DIR=../../vec']
    return original(command,*args,**kwargs)
runner.subprocess.run=run
sys.argv=['run_xsim.py','--tops','tb_kwt_negative','--tag','negative_20261102']
runner.main()
