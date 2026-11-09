"""Guard against synthesizing RTL different from the verified SoC sources."""
import argparse
import json
from pathlib import Path

from prepare import digest

parser = argparse.ArgumentParser()
parser.add_argument("--candidate", type=Path, required=True)
parser.add_argument("--sources", type=Path, required=True)
args = parser.parse_args()
plan_path = args.candidate / "work/design/plan.json"
record = json.loads((args.candidate / "work/verification_pass.json").read_text())
if (record["passed"] is not True or record["soc_tasks"] != 12 or
        record["checked_words"] != 58547 or record["plan_sha256"] != digest(plan_path)):
    raise RuntimeError("A matching full v4.4 RTL regression is required")
plan = json.loads(plan_path.read_text())
if args.sources.read_text().splitlines() != plan["sources"]:
    raise RuntimeError("Synthesis source order differs from the verified SoC filelist")
for name, sha in record["inputs"].items():
    if digest(Path(name)) != sha:
        raise RuntimeError("Verified input changed: " + name)
print("V44_FUNCTIONAL_GATE_PASSED", len(plan["sources"]), record["plan_sha256"])
