"""Verify the mapped SoC with actual cell and SRAM models."""
import argparse
import csv
import datetime
import json
from pathlib import Path
import re
import subprocess

from path_config import load_paths
from prepare import FLOW, SOC, digest, verify_mapped_sources
from regression import invoke, MAIN_PASS

parser = argparse.ArgumentParser()
parser.add_argument("--paths", type=Path, default=FLOW / "paths.tcl")
parser.add_argument("--dc-result", type=Path, default=SOC / "work/last_dc.json")
parser.add_argument("--period", type=float, default=6.25, help="functional gate simulation period")
mode = parser.add_mutually_exclusive_group()
mode.add_argument("--functional", type=Path, metavar="MAPPED_RUN",
                  help="run functional gate simulation without SDF")
mode.add_argument("--primary-sdf", action="store_true",
                  help="diagnose the native primary SDF, with timing checks enabled")
args = parser.parse_args()
paths = load_paths(args.paths)
if args.functional:
    run = args.functional.resolve(strict=True)
    period = args.period
else:
    result = json.loads(args.dc_result.read_text())
    if not args.primary_sdf and result["timing_pass"] is not True:
        raise RuntimeError("Complete the full 35-condition STA before running final SDF")
    run = Path(result["run"])
    period = result["period_ns"]
verify_mapped_sources(run)
matrix_path = run / "reports/corner_matrix.tsv"
if not (args.functional or args.primary_sdf):
    with matrix_path.open() as stream:
        matrix = list(csv.DictReader(stream, delimiter="\t"))
    if len(matrix) != 35 or len({(row["pvt"], row["rc_corner"]) for row in matrix}) != 35:
        raise RuntimeError("Incomplete timing matrix")
    if any(float(row[check + "_slack_ns"]) < 0 for row in matrix for check in ("setup", "hold")):
        raise RuntimeError("Timing matrix contains a violation")
plan = json.loads((SOC / "work/design/plan.json").read_text())
for name in plan["models"]:
    if digest(Path(name)) != plan["sha256"][name]:
        raise RuntimeError("Macro/standard cell model changed: " + name)
output = SOC / "work" / ("gate_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
output.mkdir()
netlist = run / "netlist/soc_mapped.v"
tb = SOC / "tb/tb_soc_gate.sv"
firmware = SOC / "firmware/firmware.hex"
inputs = [netlist, tb, firmware]
if not (args.functional or args.primary_sdf):
    inputs.append(matrix_path)
records = {"run": str(run), "period_ns": period, "primary_only": args.primary_sdf,
           "inputs_sha256": {str(path): digest(path) for path in inputs}, "checks": {}}
print("V45_GATE_STARTED", output, flush=True)
for check in (("functional",) if args.functional else ("setup", "hold")):
    folder = output / check
    folder.mkdir()
    sim = folder / "simv"
    defines = "+define+GATE_LEVEL+KWT_PERIOD_NS=" + str(period)
    record = records["checks"][check] = {"passed": False}
    if args.functional:
        defines += "+KWT_GATE_FUNCTIONAL+functional+ARM_UD_MODEL"
    else:
        if args.primary_sdf:
            sdf = run / "netlist/soc_mapped.sdf"
        else:
            row = min(matrix, key=lambda item: float(item[check + "_slack_ns"]))
            sdf = run / "corner_checks" / row["pvt"] / row["rc_corner"] / "netlist/soc_corner.sdf"
            record.update(pvt=row["pvt"], rc=row["rc_corner"])
        sdf_hash = digest(sdf)
        record.update(sdf=str(sdf), sdf_sha256=sdf_hash)
        (folder / "corner.sdf").symlink_to(sdf.resolve())
        if check == "hold":
            defines += "+KWT_SDF_MIN"
    command = [paths["VCS"], "-full64", "-sverilog", "-timescale=1ns/1ps",
               "-top", "tb_soc_gate", "+neg_tchk", "-negdelay", defines,
               "+incdir+" + str(Path(paths["OFFICIAL"]) / "core"),
               str(tb), str(netlist)] + plan["models"] + ["-o", str(sim)]
    try:
        invoke(command, folder, "compile.log", timeout=3600)
        invoke([str(sim), "+sdfverbose", "+FIRMWARE=" + str(firmware),
                "+VEC_DIR=" + paths["VECTOR_PATH"]], folder, "run.log", timeout=14400)
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        record["error"] = str(error)
    log = folder / "run.log"
    if log.is_file():
        text = log.read_text(errors="replace")
        messages = re.findall(r"(?i)timing violation|Warning-\[SDF|Error-\[|Fatal:|\$setuphold.*violat", text)
        record.update(matrix_completed=MAIN_PASS in text, timing_or_error_messages=len(messages),
                      log_sha256=digest(log))
        record["passed"] = MAIN_PASS in text and not messages and "error" not in record
    if not args.functional and digest(sdf) != sdf_hash:
        raise RuntimeError("SDF changed during the simulation: " + str(sdf))
    print("V45_GATE_RESULT", check, json.dumps(record), flush=True)
for path in inputs:
    if digest(path) != records["inputs_sha256"][str(path)]:
        raise RuntimeError("Gate simulation input changed: " + str(path))
(output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
if not all(check["passed"] for check in records["checks"].values()):
    raise SystemExit(1)
