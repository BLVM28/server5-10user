"""Launch the preserved Python 3.8 + TF 2.4 packages after a workspace move.

The copied venv's pyvenv.cfg embeds the old machine path. Use its packages
with the adjacent base interpreter without editing the frozen environment.
"""
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
tool = root / '03_过程与分析/05_工具'
python = tool / 'python_runtimes/cpython-3.8.20-windows-x86_64-none/python.exe'
packages = tool / 'tf24_env/Lib/site-packages'
if not python.is_file() or not packages.is_dir():
    raise SystemExit('Bundled Windows Python 3.8/TF 2.4 missing; create an environment with v2/requirements-tf24.txt')
if len(sys.argv) < 2:
    raise SystemExit('Usage: python v2/py/run_model_python.py SCRIPT [ARGS...]')
env = dict(os.environ, PYTHONPATH=str(packages), PYTHONUTF8='1',
           PYTHONDONTWRITEBYTECODE='1', TF_CPP_MIN_LOG_LEVEL='2')
raise SystemExit(subprocess.call([str(python)] + sys.argv[1:], cwd=str(root), env=env))
