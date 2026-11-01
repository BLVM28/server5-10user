"""Bounded repair loop; preserves attempts and never hides a remaining failure."""
from pathlib import Path
import os,argparse,subprocess
from check_timing import inspect
R=Path(os.environ['KWT_VM_ROOT'])
p=argparse.ArgumentParser();p.add_argument('version',choices=['v1','v2']);a=p.parse_args()
for attempt in range(3):
 subprocess.run(['python3',str(R/'flow/run_eco.py'),a.version],check=True)
 if inspect(R/'results'/a.version)['reported_constraints_met']:
  subprocess.run(['python3',str(R/'flow/check_timing.py'),a.version],check=True);break
else:raise SystemExit('Remaining timing/DRV violations after three preserved attempts')
