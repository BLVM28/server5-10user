"""Bundle version-owned sources locally, or install the hash-checked bundle in server home."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HOME = Path("/storage2/2026contest/server5/s5_10usr")
TYPES = {".sv",".v",".f",".py",".md",".tcl",".txt",".c",".h",".sdc",".json"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def managed(name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or "__pycache__" in path.parts:
        return False
    if path.name.startswith(".") and path.name!=".gitignore":
        return False
    if path.name == "README.md":
        return True
    if path.parts[0] in ("build","reports","history","implementation","packages","vec"):
        return False
    return path.name in ("Makefile",".gitignore") or path.suffix in TYPES


def source_files():
    for p in sorted(ROOT.iterdir()):
        if p.is_file() and managed(p.name):
            yield p
        elif p.is_dir():
            if p.name in ("build","reports","history","implementation","packages"):
                if (p/"README.md").is_file():
                    yield p/"README.md"
                if p.name=="implementation" and (p/"rebuilt/README.md").is_file():
                    yield p/"rebuilt/README.md"
                continue
            files = p.rglob("README.md") if p.name=="vec" else p.rglob("*")
            for f in sorted(files):
                if f.is_file() and managed(f.relative_to(ROOT).as_posix()):
                    yield f


def pack(target):
    files = {}
    with zipfile.ZipFile(str(target),"w",zipfile.ZIP_DEFLATED) as z:
        for f in source_files():
            name=f.relative_to(ROOT).as_posix()
            data=f.read_bytes()
            files[name]=sha(data)
            z.writestr(name,data)
        z.writestr("FILES.json",json.dumps(files,sort_keys=True))
    print("BUNDLE",len(files),sha(target.read_bytes()))


def index(check):
    target=ROOT/"releases/source_manifest.json"
    files=set(source_files())-{target}
    files.update(f for f in (ROOT/"vec").rglob("*") if f.is_file())
    files.update((ROOT/"packages").glob("*.zip"))
    files.add(ROOT/"packages/manifest.json")
    if len(list((ROOT/"packages").glob("*.zip")))!=5:
        raise ValueError("Run assets.py package first")
    manifest={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sorted(files)}
    # Paths are sorted as POSIX strings at serialization, independent of host OS.
    data=(json.dumps({"files":manifest},indent=2,sort_keys=True)+"\n").encode("utf-8")
    if check:
        if target.read_bytes()!=data:
            raise ValueError("Delivery manifest differs from installed sources or packages")
    else:
        target.write_bytes(data)
    print("DELIVERY PASS",len(manifest),sha(data))


def install(bundle):
    root=HOME/"v4"
    if Path.cwd().resolve()!=HOME or bundle.is_symlink() or bundle.resolve().parent!=HOME/"Desktop":
        raise ValueError("Unexpected server location")
    if root.is_symlink() or root.resolve().parent!=HOME:
        raise ValueError("Unexpected project root")
    receipt=root/"releases/.installed.json"
    if root.exists() and not receipt.is_file():
        raise ValueError("Existing v4 has no installation receipt")
    old=json.loads(receipt.read_text()) if receipt.exists() else {}
    with zipfile.ZipFile(str(bundle)) as z:
        files=json.loads(z.read("FILES.json"))
        if len(z.namelist())!=len(files)+1 or set(z.namelist())!=set(files)|{"FILES.json"}:
            raise ValueError("Bundle membership differs")
        for name,expected in files.items():
            dst=root/name
            if not managed(name) or dst.is_symlink() or root not in dst.resolve().parents or sha(z.read(name))!=expected:
                raise ValueError("Unsafe or changed source "+name)
            if dst.exists() and sha(dst.read_bytes()) not in (old.get(name),expected):
                raise ValueError("Server source was edited independently: "+name)
        for name,expected in files.items():
            dst=root/name
            if dst.is_file() and sha(dst.read_bytes())==expected:
                continue
            dst.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=str(dst.parent),delete=False) as f:
                f.write(z.read(name))
            Path(f.name).replace(dst)
        receipt.parent.mkdir(exist_ok=True)
        receipt.write_text(json.dumps(dict(old,**files),indent=2,sort_keys=True)+"\n")
    print("INSTALL PASS",len(files),flush=True)


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=("pack","install","index","check"))
    ap.add_argument("bundle",nargs="?",type=Path)
    args=ap.parse_args()
    if args.action in ("index","check"):
        index(args.action=="check")
    elif args.bundle is None:
        ap.error("pack and install require a bundle")
    else:
        (pack if args.action=="pack" else install)(args.bundle)
