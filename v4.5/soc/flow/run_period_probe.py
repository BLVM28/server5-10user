"""Report selected timing corners at a second period on the same mapped design."""
import argparse
import csv
import datetime
import json
import os
from pathlib import Path
import re
import subprocess

from path_config import load_paths
from prepare import FLOW, SOC, digest, verify_mapped_sources


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", type=Path, default=FLOW / "paths.tcl")
    parser.add_argument("--mapped", type=Path, required=True)
    parser.add_argument("--period", type=float, required=True)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--case", action="append", metavar="PVT/RC")
    selection.add_argument("--primary", action="store_true", help="recheck the mapped primary max/min library pair")
    args = parser.parse_args()
    if not 2 < args.period < 100:
        parser.error("--period must be in ns and greater than 2")
    mapped = args.mapped.resolve(strict=True)
    verify_mapped_sources(mapped)
    if args.primary:
        cases = [("primary", "pair")]
    elif args.case:
        cases = [tuple(case.split("/")) for case in args.case]
    else:
        with (mapped / "reports/corner_matrix.tsv").open() as stream:
            matrix = list(csv.DictReader(stream, delimiter="\t"))
        if len(matrix) != 35:
            raise RuntimeError("Specify --case or complete the full corner matrix")
        worst = [min(matrix, key=lambda row: float(row[check + "_slack_ns"]))
                 for check in ("setup", "hold")]
        cases = [(row["pvt"], row["rc_corner"]) for row in worst]
    if any(len(case) != 2 or not all(re.fullmatch(r"[a-zA-Z0-9_-]+", field) for field in case)
           for case in cases):
        parser.error("Expected --case PVT/RC")
    root = mapped / "corner_checks" / ("period_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    root.mkdir(parents=True)
    paths = load_paths(args.paths)
    records = []
    for pvt, rc in sorted(set(cases)):
        folder = root / "launch" / pvt / rc
        folder.mkdir(parents=True)
        output = root / "cases" / pvt / rc
        env = dict(os.environ, SOC_PATHS=str(args.paths.resolve()), SOC_MODE="corner",
                   SOC_PARENT_OUT=str(mapped), SOC_CASE_OUT=str(output), SOC_CORNER=pvt,
                   SOC_RC=rc, SOC_PROBE_PERIOD_NS=str(args.period), DC_CORES="1")
        if args.primary:
            database = mapped / "netlist/soc_mapped.ddc"
            env.update(SOC_MODE="synth", SOC_RESUME_DDC=str(database),
                       SOC_RESUME_GROUPS=str(mapped / "reports/primary/path_groups.tsv"),
                       SOC_RESUME_DDC_SHA=digest(database))
        else:
            database = mapped / "corner_databases" / pvt / (rc + ".ddc")
        scratch = folder / "scratch"
        scratch.mkdir()
        env.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
        command = [paths["DC"], "-topographical_mode", "-f", str(FLOW / "dc_synth.tcl")]
        log = folder / "probe.log"
        with log.open("w") as stream:
            result = subprocess.run(command, cwd=str(folder), env=env, stdin=subprocess.DEVNULL,
                                    stdout=stream, stderr=subprocess.STDOUT, timeout=1800)
        text = log.read_text(errors="replace")
        match = re.search(r"(?m)^V45_PERIOD_PROBE_COMPLETE period=(\S+) setup=(\S+) hold=(\S+)$", text)
        if result.returncode or not match:
            raise RuntimeError("Alternate-period STA failed: " + str(log))
        period, setup, hold = map(float, match.groups())
        if args.primary:
            location = re.search(r"(?m)^V45_PRIMARY_PROBE_RUN (\S+)$", text)
            if not location:
                raise RuntimeError("No primary probe output directory: " + str(log))
            output = Path(location.group(1))
        row = dict(pvt=pvt, rc=rc, period_ns=period, setup_ns=setup, hold_ns=hold,
                   passed=setup >= 0 and hold >= 0, log=str(log), ddc_sha256=digest(database),
                   reports=str(output / "period_probe/target"))
        records.append(row)
        print("V45_PERIOD_PROBE_RESULT", json.dumps(row), flush=True)
    (root / "result.json").write_text(json.dumps(records, indent=2) + "\n")
    if not all(record["passed"] for record in records):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
