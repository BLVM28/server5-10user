"""Generate a single SoC source list for RTL simulation and Design Compiler."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from path_config import load_paths

FLOW = Path(__file__).resolve().parent
ROOT = FLOW.parents[1]
SOC = ROOT / "soc"
PLATFORM_DIRS = ("core", "general", "subsys", "perips", "debug", "mems", "fab")
OVERLAYS = (
    "e203_ifu.v", "e203_ifu_ift2icb.v", "e203_itcm_ctrl.v", "e203_lsu_ctrl.v",
    "e203_subsys_nice_core.v", "e203_subsys_top.v", "kwt44_sram_icb_ctrl.sv",
    "kwt_banked_sram.sv", "kwt_e203_soc_top.v", "kwt_generic_hvt.v",
    "kwt_shared_sram.sv", "sirv_mrom_top.v", "sram_wrap_32KX64.v",
    "sram_wrap_64KX32.v",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_mapped_sources(run):
    """Require identical source bytes before reusing a mapped design."""
    reports = run / "reports"
    mapped_sources = (reports / "simulation_checked_sources.txt").read_text().splitlines()
    current_sources = (SOC / "work/design/sources.txt").read_text().splitlines()
    mapped_hashes = {path: sha for sha, path in
                     (row.split("  ", 1) for row in (reports / "input_sha256.txt").read_text().splitlines())}
    if len(mapped_sources) != len(current_sources):
        raise RuntimeError("Mapped source count differs from the verified RTL")
    for mapped, current in zip(mapped_sources, current_sources):
        if digest(Path(current)) != mapped_hashes.get(mapped):
            raise RuntimeError("Mapped source does not match: " + current)


def keep_tcm_control_clocked(source):
    # The SRAM macro has its own request-driven clock gate. The controller
    # handshake cannot advertise ready while its receive clock is stopped.
    for bank in ("itcm", "dtcm"):
        instance = (
            rf"(?m)^[ \t]*e203_clkgate\s+u_{bank}_clkgate\s*\(\s*"
            rf"\.clk_in\s*\(\s*clk\s*\),\s*\.test_mode\s*\(\s*test_mode\s*\),\s*"
            rf"\.clock_en\s*\(\s*{bank}_clk_en\s*\),\s*\.clk_out\s*\(\s*clk_{bank}\s*\)\s*\);"
        )
        source, count = re.subn(instance, "  assign clk_{} = clk;".format(bank), source)
        if count != 1:
            raise RuntimeError("Expected one E203 controller clock gate for " + bank)
    return source


def create_plan(official, out, portable=False, baseline=None):
    official = official.resolve(strict=True)
    out.mkdir(parents=True, exist_ok=True)
    native_dtcm = official / "core/e203_dtcm_ctrl.v"
    changed, count = re.subn(
        r"(?m)^(\s*)sirv_sram_icb_ctrl(?=\s*#\s*\()",
        r"\1kwt44_sram_icb_ctrl", native_dtcm.read_text(encoding="utf-8")
    )
    if count != 1:
        raise RuntimeError("Expected one DTCM SRAM controller in " + str(native_dtcm))
    generated = out / native_dtcm.name
    generated.write_text(changed, encoding="utf-8")
    native_clock = official / "core/e203_clk_ctrl.v"
    generated_clock = out / native_clock.name
    generated_clock.write_text(keep_tcm_control_clocked(native_clock.read_text(encoding="utf-8")),
                               encoding="utf-8")
    skip = set(OVERLAYS) | {native_dtcm.name, native_clock.name, "GENERIC_RVT_SMIC.v", "GENERIC_RVT_ARM.v"}
    official_sources = []
    for directory in PLATFORM_DIRS:
        subtree = official / directory
        if not subtree.is_dir():
            raise FileNotFoundError(str(subtree))
        official_sources.extend(path for path in sorted(subtree.rglob("*.v")) if path.name not in skip)
    accel = [ROOT / line for line in (ROOT / "rtl.f").read_text().splitlines() if line]
    sources = official_sources + accel + [SOC / "rtl" / name for name in OVERLAYS] + [generated, generated_clock]
    sources = [path.resolve(strict=True) for path in sources]
    includes = sorted({path.parent for path in official_sources}) + [ROOT / "rtl", SOC / "rtl"]
    if portable:
        includes.insert(0, ROOT.parent / "v4.3/integration/upstream")
        models = [ROOT / "tb/kwt_sram_sim.sv", SOC / "tb/portable_sram.sv"]
    else:
        baseline = baseline.resolve(strict=True)
        verified = json.loads((baseline / "verified_inputs.json").read_text())
        # Use the same exact models as the P6 functional baseline.
        models = [Path(name) for name in verified if Path(name).suffix == ".v" and
                  ("scc40" in Path(name).name.lower() or
                   Path(name).name.startswith(("RAMSP", "ROM1KX32", "ROM2KX32")))]
        if len([path for path in models if "scc40" in path.name.lower()]) != 1:
            raise RuntimeError("P6 did not identify a unique HVT simulation library")
        for path in models:
            if digest(path) != verified[str(path)]:
                raise RuntimeError("P6 model changed: " + str(path))
        for path in (native_dtcm, native_clock):
            if digest(path) != verified.get(str(path)):
                raise RuntimeError("P6 source changed: " + str(path))
    models = [path.resolve(strict=True) for path in models]
    (out / "sources.txt").write_text("".join(str(path) + "\n" for path in sources), encoding="utf-8")
    (out / "sim.f").write_text(
        "".join("+incdir+" + str(path) + "\n" for path in includes)
        + "".join(str(path) + "\n" for path in sources + models), encoding="utf-8")
    return {
        "sources": [str(path) for path in sources],
        "includes": [str(path) for path in includes],
        "models": [str(path) for path in models],
        "original_dtcm_sha256": digest(native_dtcm),
        "original_clk_ctrl_sha256": digest(native_clock),
        "sha256": {str(path): digest(path) for path in sources + models},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", type=Path, default=FLOW / "paths.tcl")
    parser.add_argument("--portable-official", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.portable_official:
        out = args.out or ROOT / "build/local/design"
        plan = create_plan(args.portable_official, out, portable=True)
    else:
        paths = load_paths(args.paths)
        out = args.out or SOC / "work/design"
        plan = create_plan(Path(paths["OFFICIAL"]), out, baseline=Path(paths["BASELINE"]))
    (out / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    print("SOURCE_PLAN_READY", out, len(plan["sources"]), len(plan["models"]))


if __name__ == "__main__":
    main()
