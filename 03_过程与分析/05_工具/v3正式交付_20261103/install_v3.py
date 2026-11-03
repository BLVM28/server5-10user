"""Install a new v3 strictly within the personal home. Leave existing projects alone."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HOME = Path("/storage2/2026contest/server5/s5_10usr")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(bundle):
    if Path.cwd().resolve()!=HOME or (HOME/"v3").exists() or (HOME/"v3").is_symlink():
        raise ValueError("Expected a new v3 directly inside the authorised home")
    if bundle.resolve().parent!=HOME/"Desktop" or bundle.is_symlink():
        raise ValueError("Unexpected transfer location")
    stage=Path(tempfile.mkdtemp(prefix=".v3_stage_",dir=str(HOME)))
    print("STAGING",stage,flush=True)
    with zipfile.ZipFile(str(bundle)) as z:
        manifest=json.loads(z.read("releases/source_manifest.json").decode("utf-8"))
        for name in z.namelist():
            if name.startswith("_control/"):
                continue
            dest=stage/name
            if stage not in dest.resolve().parents:
                raise ValueError("Invalid path "+name)
            data=z.read(name)
            if name not in ("releases/source_manifest.json","SERVER_RESULTS.md") and (
                    name not in manifest["files"] or hashlib.sha256(data).hexdigest()!=manifest["files"][name]):
                raise ValueError("Unexpected/changed upload "+name)
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(data)
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(stage/"server_eda"))
    from qualify import source_manifest
    from snapshot import install
    proof=json.loads((stage/"results/ppa.json").read_text())
    origin=(HOME/proof["server_relative_directory"]).resolve()
    if HOME not in origin.parents or not origin.is_dir():
        raise ValueError("Invalid qualification origin")
    install(stage,origin,"qualified200",source_manifest())
    for p in sorted(origin.glob("sta_*")):
        output=stage/"reports/original_qualification"/p.name
        output.mkdir(parents=True,exist_ok=True)
        for f in p.iterdir():
            if f.is_file() and not f.is_symlink() and f.suffix in (".txt",".rpt",".log",".json"):
                shutil.copy2(str(f),str(output/f.name))
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable,str(stage/"py/assets.py"),"package"],cwd=str(stage),env=env,check=True)
    for name,expected in manifest["files"].items():
        path=stage/name
        if stage not in path.resolve().parents or not path.is_file() or sha(path)!=expected:
            raise ValueError("Final publication hash mismatch: "+name)
    if (HOME/"v3").exists():
        raise FileExistsError("Another v3 appeared during staging")
    stage.rename(HOME/"v3")
    print("INSTALL PASS v3",len(manifest["files"]),"files",flush=True)


if __name__=="__main__":
    main(Path(sys.argv[1]))
