"""Create five deterministic, member-verified v4.2 archives."""
import hashlib,json,tempfile,zipfile
from pathlib import Path
from scalar_vectors import ROOT,verify
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

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
    verify()
    groups={
        "rtl":files_under("rtl","rtl.f"),
        "tb":files_under("tb","server_eda/tb_core_all_gate.sv"),
        "makefile":files_under("Makefile","server_eda/Makefile","SERVER_GUIDE.md"),
        "flow":files_under("server_eda","integration","py","results","README.md","ARCHITECTURE.md","HISTORY.md",
                           "RESULTS.md","SERVER_RESULTS.md","SERVER_GUIDE.md","THIRD_PARTY_NOTICES.txt",
                           "UPSTREAM_LICENSE.txt","releases/verification.json"),
        "vectors":files_under("vec","py/vector_manifest.json","py/fast_manifest.json","py/precision_manifest.json","py/profile42.json","UPSTREAM_LICENSE.txt"),
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



if __name__=="__main__":package()
