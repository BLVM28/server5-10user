"""Verify the mapped SoC with actual cell and SRAM models."""
import argparse
import csv
import datetime
import json
from pathlib import Path
import re

from path_config import load_paths
from prepare import FLOW, SOC, digest, verify_mapped_sources
from regression import invoke, MAIN_PASS

parser = argparse.ArgumentParser()
parser.add_argument("--paths", type=Path, default=FLOW / "paths.tcl")
parser.add_argument("--dc-result", type=Path, default=SOC / "work/last_dc.json")
parser.add_argument("--functional", type=Path, metavar="MAPPED_RUN",
                    help="run functional gate simulation without SDF")
args = parser.parse_args()
paths = load_paths(args.paths)
if args.functional:
    run = args.functional.resolve(strict=True)
else:
    result = json.loads(args.dc_result.read_text())
    if result["timing_pass"] is not True:
        raise RuntimeError("Complete the full 35-condition STA before running final SDF")
    run = Path(result["run"])
verify_mapped_sources(run)
matrix_path = run / "reports/corner_matrix.tsv"
if not args.functional:
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
if not args.functional:
    inputs.append(matrix_path)
records = {"run": str(run), "inputs_sha256": {str(path): digest(path) for path in inputs}}
print("V44_GATE_STARTED", output, flush=True)
for check in (("functional",) if args.functional else ("setup", "hold")):
    folder = output / check
    folder.mkdir()
    sim = folder / "simv"
    defines = "+define+GATE_LEVEL"
    if args.functional:
        defines += "+KWT_GATE_FUNCTIONAL+functional+ARM_UD_MODEL"
    else:
        row = min(matrix, key=lambda item: float(item[check + "_slack_ns"]))
        sdf = run / "corner_checks" / row["pvt"] / row["rc_corner"] / "netlist/soc_corner.sdf"
        sdf_hash = digest(sdf)
        (folder / "corner.sdf").symlink_to(sdf.resolve())
        if check == "hold":
            defines += "+KWT_SDF_MIN"
    command = [paths["VCS"], "-full64", "-sverilog", "-timescale=1ns/1ps",
               "-top", "tb_soc_gate", "+neg_tchk", "-negdelay", defines,
               "+incdir+" + str(Path(paths["OFFICIAL"]) / "core"),
               str(tb), str(netlist)] + plan["models"] + ["-o", str(sim)]
    invoke(command, folder, "compile.log", timeout=3600)
    invoke([str(sim), "+sdfverbose",
            "+FIRMWARE=" + str(firmware),
            "+VEC_DIR=" + paths["VECTOR_PATH"]], folder, "run.log", timeout=14400)
    log = folder / "run.log"
    text = log.read_text(errors="replace")
    if MAIN_PASS not in text or re.search(r"(?i)timing violation|Warning-\[SDF|Error-\[|Fatal:|\$setuphold.*violat", text):
        raise RuntimeError("Gate verification failed: " + str(log))
    if args.functional:
        records[check] = dict(passed=True, log_sha256=digest(log))
        print("V44_GATE_FUNCTIONAL_PASS", MAIN_PASS, flush=True)
        continue
    if digest(sdf) != sdf_hash:
        raise RuntimeError("SDF changed during the simulation: " + str(sdf))
    records[check] = dict(passed=True, pvt=row["pvt"], rc=row["rc_corner"],
                          sdf_sha256=sdf_hash, log_sha256=digest(log))
    print("V44_SDF_PASS", check, records[check], flush=True)
for path in inputs:
    if digest(path) != records["inputs_sha256"][str(path)]:
        raise RuntimeError("Gate simulation input changed: " + str(path))
(output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
