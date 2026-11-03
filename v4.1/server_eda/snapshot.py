"""Import and verify server-private artifacts for the exact v4 RTL and ECO."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import time

ARTIFACTS = ("mapped.v","mapped.ddc","area.rpt","qualification.json","resize_audit.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(directory, sources):
    q = json.loads((directory/"qualification.json").read_text())
    n = sha(directory/"mapped.v")
    audit = json.loads((directory/"resize_audit.json").read_text())
    if q["sources"] != sources or n != q["mapped_sha256"] or n != audit["final_sha256"]:
        raise ValueError("Source/netlist mismatch; rebuild with make synth")
    if not audit["remaining_statements_identical"] or audit["changes"] != q["resize_changes"]:
        raise ValueError("Missing structural ECO proof")
    points = {p["corner"]:p for p in q["points"] if abs(p["period_ns"]-6.666667)<1e-7}
    if set(points)!={"ss","ff"} or any(not p["timing_pass"] or p["reported_violations"]
                                        or min(p["setup_hold_ns"])<0 for p in points.values()):
        raise ValueError("Missing passing 150 MHz corner results")
    if not q["area_budget_met"] or q["v41_area"]>q["proposed_area_limit"]:
        raise ValueError("Area budget exceeded")
    return q


def install(root, origin, name, sources):
    if name!="rebuilt":
        raise ValueError("Invalid implementation name")
    impl = root/"implementation"
    impl.mkdir(exist_ok=True)
    target = impl/name
    with tempfile.TemporaryDirectory(prefix=".snapshot_",dir=str(impl)) as tmp:
        stage = Path(tmp)/name
        core = stage/"synth_kwt_nice_core"
        core.mkdir(parents=True)
        for f in ARTIFACTS:
            shutil.copy2(str(origin/f),str(core/f))
        validate(core,sources)
        manifest = {"rtl_sha256":{k:h for k,h in sources.items() if k.startswith("rtl/")},
                    "mapped_sha256":{"synth_kwt_nice_core/"+f:sha(core/f) for f in ARTIFACTS}}
        (stage/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        if (target/"README.md").is_file():
            shutil.copy2(str(target/"README.md"),str(stage/"README.md"))
        previous = None
        if target.exists():
            previous = impl/("previous_"+name+"_"+str(int(time.time()*1000000)))
            target.rename(previous)
        try:
            stage.rename(target)
        except BaseException:
            if previous is not None:
                previous.rename(target)
            raise
    print("IMPLEMENTATION PASS "+name+" "+str(target),flush=True)
