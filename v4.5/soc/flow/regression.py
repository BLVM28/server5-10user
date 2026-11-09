"""SMIC40 VCS functional regression and identical-port paired measurements."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from path_config import load_paths
from prepare import create_plan, digest, ROOT, SOC, FLOW

MAIN_PASS = "SOC_EXECUTION_ALL_PASS tasks=12 checked_words=58547 boots=2"
COMMON_DEFINES = "+define+functional+KWT_USE_FOUNDRY_SRAM+ARM_UD_MODEL+DISABLE_SV_ASSERTION"
TIMEOUT = 7200


def invoke(command, folder, log, timeout=TIMEOUT):
    scratch = folder / "scratch"
    scratch.mkdir(exist_ok=True)
    env = dict(os.environ)
    env.update({key: str(scratch) for key in ("TMPDIR", "TMP", "TEMP")})
    with (folder / log).open("w") as stream:
        process = subprocess.run(command, cwd=str(folder), stdout=stream, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, env=env, timeout=timeout)
    if process.returncode:
        raise RuntimeError("Tool exited with code {}. See {}".format(process.returncode, folder / log))


def compile_vcs(paths, root, label, top, sources, includes, defines=()):
    folder = root / label
    folder.mkdir()
    command = [paths["VCS"], "-full64", "-sverilog", "-timescale=1ns/1ps",
               "-top", top, COMMON_DEFINES]
    command += ["+define+" + d for d in defines]
    command += ["+incdir+" + str(path) for path in includes]
    command += list(map(str, sources)) + ["-o", str(folder / "simv")]
    (folder / "compile_command.json").write_text(json.dumps(command, indent=2))
    invoke(command, folder, "compile.log", timeout=2400)
    print("V44_COMPILED", label, flush=True)
    return folder


def simulate(folder, label, args, markers):
    log = "run_" + label + ".log"
    invoke([str(folder / "simv")] + list(args), folder, log)
    report = (folder / log).read_text(errors="replace")
    if any(marker not in report for marker in markers) or re.search(r"(?im)^\s*(fatal|error)[:\[]", report):
        raise RuntimeError("Verification failed: " + str(folder / log))
    print("V44_FUNCTION_PASS", label, str(folder / log), flush=True)
    return report


def stats(report):
    lines = [line for line in report.splitlines() if line.startswith("SOC_PERFORMANCE_TOTAL ")]
    if len(lines) != 1 or report.count("SOC_MATRIX_PASS layer=") != 12:
        raise RuntimeError("Missing 12 end-to-end matrix timings")
    row = {k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", lines[0])}
    if row["tasks"] != 12 or row["checked_words"] != 58547:
        raise RuntimeError("Invalid performance window coverage")
    if row["workload_cycles"] != row["load_cycles"]+row["dispatch_cycles"]+row["engine_to_last_write"]:
        raise RuntimeError("Cycle accounting mismatch")
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", type=Path, default=FLOW / "paths.tcl")
    parser.add_argument("--period", type=float, default=6.25)
    parser.add_argument("--paired", action="store_true")
    parser.add_argument("--v44-reference", type=Path, help="v4.4 source tree with a verified source plan")
    parser.add_argument("--wfi-firmware", type=Path, help="isolated firmware built by make firmware-wfi")
    args = parser.parse_args()
    if not 2 < args.period < 100:
        parser.error("--period must be in ns and greater than 2")
    paths = load_paths(args.paths)
    baseline = Path(paths["BASELINE"])
    vectors = Path(paths["VECTOR_PATH"])
    firmware = SOC / "firmware/firmware.hex"
    plan_dir = SOC / "work/design"
    run_root = SOC / "work" / ("rtl_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    run_root.mkdir(parents=True)
    plan = create_plan(Path(paths["OFFICIAL"]), plan_dir, baseline=baseline)
    plan_file = plan_dir / "plan.json"
    plan_file.write_text(json.dumps(plan, indent=2) + "\n")
    plan_digest = digest(plan_file)
    models = plan["models"]
    sources = plan["sources"] + models
    testbench = SOC / "tb/tb_soc_boot.sv"
    inputs = dict(plan["sha256"])
    for path in [firmware] + sorted((SOC / "tb").glob("tb_*.sv")) + sorted(vectors.glob("*.hex")):
        inputs[str(path)] = digest(path)

    def test_soc(folder, binary, label, *load_args):
        report = simulate(folder, label,
                          ["+FIRMWARE=" + str(binary), "+VEC_DIR=" + str(vectors)] + list(load_args),
                          (MAIN_PASS, "FETCH_REQUEST_STAGE_PASS", "LSU_REQUEST_STAGE_PASS"))
        return stats(report)

    def build_soc(label, file_list, includes, *defines):
        return compile_vcs(paths, run_root, label, "tb_soc_boot", file_list + [testbench], includes,
                           ("KWT_LSU_REQUEST_STAGE", "KWT_PERIOD_NS=" + str(args.period)) + defines)

    measures = {}
    cand = build_soc("v45", sources, plan["includes"])
    measures["v45_batch_padded"] = test_soc(cand, firmware, "v45_batch_padded", "+BATCH_LOAD")
    measures["v45_serial_padded"] = test_soc(cand, firmware, "v45_serial_padded")
    measures["v45_batch_active"] = test_soc(cand, firmware, "v45_batch_active", "+BATCH_LOAD", "+ACTIVE_LOAD")
    if measures["v45_batch_padded"]["max_inflight"] < 2:
        raise RuntimeError("The direct ICB path never used more than one outstanding request")
    if args.wfi_firmware:
        wfi_firmware = args.wfi_firmware.resolve(strict=True)
        inputs[str(wfi_firmware)] = digest(wfi_firmware)
        simulate(cand, "timer_wfi", ["+FIRMWARE=" + str(wfi_firmware), "+VEC_DIR=" + str(vectors),
                                    "+BOOT_WFI_ONLY"], ("SOC_TIMER_WFI_PASS",))

    if args.v44_reference:
        previous_root = args.v44_reference.resolve(strict=True)
        previous = json.loads((previous_root / "soc/work/design/plan.json").read_text())
        for name, sha in previous["sha256"].items():
            if digest(Path(name)) != sha:
                raise RuntimeError("v4.4 paired input changed: " + name)
        previous_firmware = previous_root / "soc/firmware/firmware.hex"
        inputs.update(previous["sha256"])
        inputs[str(previous_firmware)] = digest(previous_firmware)
        old = build_soc("v44", previous["sources"] + previous["models"], previous["includes"],
                        "KWT44_SOC_REFERENCE")
        measures["v44_batch_padded"] = test_soc(old, previous_firmware, "v44_batch_padded", "+BATCH_LOAD")
        measures["v44_serial_padded"] = test_soc(old, previous_firmware, "v44_serial_padded")
        measures["v44_batch_active"] = test_soc(old, previous_firmware, "v44_batch_active", "+BATCH_LOAD", "+ACTIVE_LOAD")

    if args.paired:
        previous = json.loads((baseline / "verification/tb_soc_boot/source_manifest.json").read_text())
        for name, sha in previous.items():
            if digest(Path(name)) != sha:
                raise RuntimeError("P6 paired input changed: " + name)
        old_sources = [name for name in previous if Path(name).name != "tb_soc_boot.sv"]
        old = build_soc("p6", old_sources, plan["includes"], "KWT44_P6_COMPARE",
                        "KWT_MEM_BASE=32'hA0000000", "KWT_MEM_BYTES=524288")
        p6_firmware = baseline / "firmware/firmware.hex"
        measures["p6_serial_padded"] = test_soc(old, p6_firmware, "p6_serial_padded")
        measures["p6_batch_padded"] = test_soc(old, p6_firmware, "p6_batch_padded", "+BATCH_LOAD")
        if abs(args.period - 6.666666667) < 0.00001 and measures["p6_serial_padded"]["workload_cycles"] != 1617436:
            raise RuntimeError("P6 original timing window did not reproduce")
    for name, row in measures.items():
        if name.endswith("_padded") and row["loaded_words"] != 12*(4096+16384+256):
            raise RuntimeError("Padded workload changed: " + name)
        if row["read_commands"] != 76181 or row["write_commands"] != 58547:
            raise RuntimeError("Accelerator transaction count changed: " + name)
    (run_root / "performance.json").write_text(json.dumps(measures, indent=2) + "\n")
    print("V44_SOC_MEASUREMENTS", json.dumps(measures), flush=True)

    itcm = compile_vcs(paths, run_root, "itcm", "tb_itcm_pipeline",
                       sources + [SOC / "tb/tb_itcm_pipeline.sv"], plan["includes"])
    for seed in (20304007, 7919, 65537, 104729):
        simulate(itcm, "itcm_" + str(seed), ["+SEED=" + str(seed)], ("ITCM_PIPELINE_PASS",))

    for top, marker in (("tb_shared_sram_pipeline", "SHARED_SRAM_PIPELINE_PASS"),
                        ("tb_clint_pipeline", "CLINT_PIPELINE_PASS")):
        suite = compile_vcs(paths, run_root, top, top, sources + [SOC / ("tb/" + top + ".sv")],
                            plan["includes"])
        simulate(suite, top, [], (marker,))

    wrappers = sorted((ROOT / "tb").glob("tb_kwt_*.sv"))
    inputs.update({str(path): digest(path) for path in wrappers})
    for top in ("tb_kwt_stream_dot", "tb_kwt_streams", "tb_kwt_wait", "tb_kwt_zero", "tb_kwt_public_sram"):
        suite = compile_vcs(paths, run_root, top, top, sources + wrappers, plan["includes"],
                            ("KWT_PERIOD_NS=" + str(args.period),))
        markers = ("ALL PASS, 64/64",) if top == "tb_kwt_stream_dot" else ("ALL PASS, 29/29", "STREAM GUARD PASS 25/25")
        simulate(suite, top, ["+VEC_DIR=" + str(vectors)], markers)

    if digest(plan_file) != plan_digest or any(digest(Path(name)) != sha for name, sha in inputs.items()):
        raise RuntimeError("An input changed during regression")
    stamp = {
        "passed": True, "run": str(run_root), "plan_sha256": plan_digest,
        "core_period_ns": args.period,
        "inputs": inputs, "soc_tasks": 12, "checked_words": 58547,
        "functional_checks": ["soc_three_load_modes", "itcm_four_seeds", "shared_sram",
                              "clint", "dot", "four_bus_modes"] + (["cpu_wfi"] if args.wfi_firmware else []),
        "performance": measures,
    }
    (run_root / "input_sha256.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (SOC / "work/verification_pass.json").write_text(json.dumps(stamp, indent=2) + "\n")
    print("V44_RTL_REGRESSION_COMPLETE", run_root, flush=True)


if __name__ == "__main__":
    main()
