"""Map the verified source plan with the P6 electrical and I/O constraints."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess

from path_config import load_paths
from prepare import FLOW, SOC, digest, verify_mapped_sources


def resume_mapping(run, execution, period, retarget):
    """Reopen a mapped checkpoint only when its source bytes match this RTL run."""
    verify_mapped_sources(run)
    original = float((run / "reports/core_period_ns.txt").read_text())
    if abs(original - period) > 0.00002 and not retarget:
        raise RuntimeError("Use --retarget to change the period of a mapped checkpoint")
    primary = run / "reports/primary/path_groups.tsv"
    database = run / "netlist/soc_mapped.ddc"
    inputs = {str(path): digest(path) for path in (primary, database)}
    (execution / "resume_inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    return dict(SOC_RESUME_DDC=str(database), SOC_RESUME_GROUPS=str(primary),
                SOC_RESUME_DDC_SHA=inputs[str(database)])

parser = argparse.ArgumentParser()
parser.add_argument("--paths", type=Path, default=FLOW / "paths.tcl")
parser.add_argument("--period", type=float, default=6.25)
parser.add_argument("--primary-only", action="store_true")
parser.add_argument("--resume", type=Path, help="mapped run directory with matching source bytes")
parser.add_argument("--retarget", action="store_true", help="use --period on the existing mapping without recompiling")
args = parser.parse_args()
if not 2 < args.period < 100:
    parser.error("--period must be in ns and greater than 2")
if args.retarget and not args.resume:
    parser.error("--retarget requires --resume")
paths = load_paths(args.paths)
stage = "primary" if args.primary_only else "full"
execution = SOC / "work" / ("dc_" + stage + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
execution.mkdir(parents=True)
scratch = execution / "scratch"
scratch.mkdir()
env = dict(os.environ)
env.update({key: str(scratch) for key in ("TMPDIR", "TMP", "TEMP")})
env.update(SOC_PATHS=str(args.paths.resolve()), SOC_MODE="synth",
           SOC_PERIOD_NS=str(args.period),
           SOC_PRIMARY_ONLY="1" if args.primary_only else "0",
           SOC_STOP_ON_PRIMARY_FAIL="1")
for key in ("SOC_RESUME_DDC", "SOC_RESUME_GROUPS", "SOC_RESUME_DDC_SHA",
            "SOC_PROBE_PERIOD_NS", "SOC_RETARGET_PERIOD_NS"):
    env.pop(key, None)
if args.resume:
    env.update(resume_mapping(args.resume.resolve(strict=True), execution, args.period, args.retarget))
if args.retarget:
    env["SOC_RETARGET_PERIOD_NS"] = str(args.period)
command = [paths["DC"], "-topographical_mode", "-f", str(FLOW / "dc_synth.tcl")]
log = execution / "dc.log"
print("V44_DC_STARTED", log, flush=True)
with log.open("w") as stream:
    process = subprocess.run(command, cwd=str(execution), env=env, stdin=subprocess.DEVNULL,
                             stdout=stream, stderr=subprocess.STDOUT)
report = log.read_text(errors="replace")
match = re.findall(r"(?m)^V44_PRIMARY_COMPLETED (\S+) setup=(\S+) hold=(\S+)$", report)
if len(match) != 1:
    raise RuntimeError("DC did not finish mapping, see " + str(log))
directory, setup, hold = match[0]
measured_period = float((Path(directory) / "reports/core_period_ns.txt").read_text())
if abs(measured_period - args.period) > 0.00002:
    raise RuntimeError("DC reported a different core period")
record = {
    "run": directory, "log": str(log), "period_ns": args.period,
    "setup_ns": float(setup), "hold_ns": float(hold),
    "primary_pass": float(setup) >= 0 and float(hold) >= 0,
    "mode": stage, "retargeted": args.retarget, "timing_pass": None,
}
if not args.primary_only:
    summary = Path(directory) / "reports/timing_acceptance.txt"
    if summary.is_file():
        text = summary.read_text().splitlines()
        record["timing_pass"] = ("TIMING_PASS=1" in text and "ANALYZED_COMBINATIONS=35" in text)
(execution / "result.json").write_text(json.dumps(record, indent=2) + "\n")
(SOC / "work/last_dc.json").write_text(json.dumps(record, indent=2) + "\n")
print("V44_DC_RESULT", json.dumps(record), flush=True)
if process.returncode or not record["primary_pass"] or (not args.primary_only and record["timing_pass"] is not True):
    raise SystemExit(1)
