"""Restore pinned golden files and build the five portable v3 source archives."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vectors():
    manifest = json.loads((ROOT / "py/vector_manifest.json").read_text(encoding="utf-8"))
    source = ROOT.parent / "v2/vec"
    dest = ROOT / "vec"
    if dest.is_symlink():
        raise ValueError("vec must be a local project directory")
    for name, expected in manifest.items():
        target = dest / name
        if dest.resolve() not in target.resolve().parents:
            raise ValueError("Unsafe vector path: " + name)
        if target.exists():
            if digest(target) != expected:
                raise ValueError("Existing golden differs from manifest: " + name)
            continue
        original = source / name
        if not original.is_file() or digest(original) != expected:
            raise ValueError("Pinned v2 vector missing or changed: " + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=str(target.parent), delete=False) as temp:
            scratch = Path(temp.name)
            with original.open("rb") as src:
                shutil.copyfileobj(src, temp)
        try:
            if digest(scratch) != expected:
                raise ValueError("Copy verification failed: " + name)
            scratch.replace(target)
        finally:
            if scratch.exists():
                scratch.unlink()
    actual = {p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file() and p.suffix != ".md"}
    if actual != set(manifest):
        raise ValueError("Unexpected files under vec/: " + str(sorted(actual-set(manifest))))
    print("VECTORS PASS: %d pinned data files" % len(manifest), flush=True)


def files_under(*items):
    files = set()
    for name in items:
        path = ROOT / name
        if not path.exists():
            raise FileNotFoundError(name)
        if path.is_dir() and name!="vec":
            candidates = path.iterdir()
        else:
            candidates = path.rglob("*") if path.is_dir() else [path]
        for p in candidates:
            if not p.is_file() or "__pycache__" in p.parts or p.suffix==".pyc":
                continue
            if p.is_symlink() or ROOT not in p.resolve().parents:
                raise ValueError("Invalid source archive member: "+str(p))
            if p.name!="Makefile" and p.suffix not in {".sv",".v",".md",".f",".py",".tcl",".sdc",
                                                      ".c",".h",".json",".txt",".hex",".npz"}:
                raise ValueError("Unexpected file in source package: "+str(p))
            if p.name=="mapped.v":
                raise ValueError("Mapped netlist is not a source package member")
            files.add(p)
    return sorted(files, key=lambda p:p.relative_to(ROOT).as_posix())


def package():
    vectors()
    groups = {
        "rtl":files_under("rtl","rtl.f"), "tb":files_under("tb"),
        "makefile":files_under("Makefile","server_eda/Makefile"),
        "flow":files_under("server_eda","integration","py","README.md","SERVER_GUIDE.md",
                           "ARCHITECTURE.md","RESULTS.md","THIRD_PARTY_NOTICES.txt","results/ppa.json"),
        "vectors":files_under("vec","py/vector_manifest.json"),
    }
    out = ROOT / "packages"
    out.mkdir(exist_ok=True)
    manifest = {}
    with tempfile.TemporaryDirectory(dir=str(out)) as scratch:
        stage = Path(scratch)
        for name, files in groups.items():
            archive = stage / (name+".zip")
            members = {}
            with zipfile.ZipFile(str(archive), "w") as zipped:
                for path in files:
                    rel = path.relative_to(ROOT).as_posix()
                    data = path.read_bytes()
                    entry = zipfile.ZipInfo(rel, (2000,1,1,0,0,0))
                    entry.create_system = 3
                    entry.external_attr = 0o100644 << 16
                    zipped.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED)
                    members[rel] = hashlib.sha256(data).hexdigest()
            with zipfile.ZipFile(str(archive)) as zipped:
                if zipped.namelist() != list(members) or any(
                        hashlib.sha256(zipped.read(n)).hexdigest()!=h for n,h in members.items()):
                    raise ValueError("Archive verification failed: "+name)
            manifest[name] = {"files":len(files),"bytes":archive.stat().st_size,
                              "sha256":digest(archive),"members":members}
            print("PACKAGE PASS %s: %d files" % (name,len(files)), flush=True)
        index = stage / "manifest.json"
        index.write_bytes((json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode("utf-8"))
        for name in groups:
            (stage/(name+".zip")).replace(out/(name+".zip"))
        index.replace(out/"manifest.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=["vectors","package"])
    (package if parser.parse_args().target=="package" else vectors)()
