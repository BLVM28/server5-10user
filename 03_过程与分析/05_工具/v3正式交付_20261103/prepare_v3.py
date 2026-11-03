"""Create a hash manifest and a small upload, reusing the installed v2 vectors."""
from pathlib import Path
import hashlib
import json
import zipfile

TOOLS=Path(__file__).resolve().parent
ROOT=TOOLS.parents[2]/"v3"


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    files=[p for p in ROOT.iterdir() if p.is_file() and p.name!="SERVER_RESULTS.md"]
    for directory in ("rtl","tb","py","server_eda","integration","results","vec","packages"):
        files.extend(p for p in (ROOT/directory).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix!=".pyc")
    files.extend(ROOT/n/"README.md" for n in ("build","reports","history","implementation",
                                              "implementation/qualified200","releases"))
    assert all(ROOT in p.resolve().parents and not p.is_symlink() for p in files)
    manifest={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}
    info={"format":1,"version":"v3","files":manifest,
          "scope":"Portable project files, physical vector copies and the five public ZIPs. Excludes self, post-install receipt/report, generated builds and private mapped artifacts."}
    target=ROOT/"releases/source_manifest.json"
    target.write_bytes((json.dumps(info,indent=2,ensure_ascii=False,sort_keys=True)+"\n").encode("utf-8"))
    payload=ROOT/"build/publish_session/v3_delivery.zip";payload.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(str(payload),"w",zipfile.ZIP_DEFLATED) as z:
        for n in manifest:
            if (n.startswith("vec/") and not n.endswith(".md")) or (n.startswith("packages/") and not n.endswith(".md")):
                continue
            z.write(str(ROOT/n),n)
        z.write(str(target),"releases/source_manifest.json")
        for n in ("install_v3.py","accept_v3.py"):
            z.write(str(TOOLS/n),"_control/"+n)
    print("DELIVERY",len(manifest),"files;",payload.stat().st_size,"upload bytes; SHA",sha(payload))
    print("SOURCE MANIFEST SHA",sha(target))


if __name__=="__main__":main()
