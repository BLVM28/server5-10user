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


def use_common_cpu_clock(source):
    # The IFU halt handshake remains in the CPU. Remove the unbalanced gated
    # branches between the IFU, EXU, LSU, BIU and both TCM controllers.
    for bank in ("ifu", "exu", "lsu", "biu", "itcm", "dtcm"):
        output = "clk_" + (bank if bank.endswith("tcm") else "core_" + bank)
        instance = (
            rf"(?m)^[ \t]*e203_clkgate\s+u_{bank}_clkgate\s*\(\s*"
            rf"\.clk_in\s*\(\s*clk\s*\),\s*\.test_mode\s*\(\s*test_mode\s*\),\s*"
            rf"\.clock_en\s*\(\s*{bank}_clk_en\s*\),\s*\.clk_out\s*\(\s*{output}\s*\)\s*\);"
        )
        source, count = re.subn(instance, "  assign {} = clk;".format(output), source)
        if count != 1:
            raise RuntimeError("Expected one E203 controller clock gate for " + bank)
    return source


def pipeline_timer(source):
    # Store a lexicographic relation per 16-bit slice. Timer register reads,
    # writes and the RTC tick retain their original clock and cycle semantics.
    comparison = """  reg [3:0] kwt_time_gt, kwt_time_eq;
  genvar kwt_slice;
  generate for (kwt_slice = 0; kwt_slice < 4; kwt_slice = kwt_slice + 1) begin : kwt_timer_compare
    always @(posedge clock or posedge reset) begin
      if (reset) begin
        kwt_time_gt[kwt_slice] <= 1'b0;
        kwt_time_eq[kwt_slice] <= 1'b0;
      end else begin
        kwt_time_gt[kwt_slice] <= T_904[16*kwt_slice+:16] > T_915[16*kwt_slice+:16];
        kwt_time_eq[kwt_slice] <= T_904[16*kwt_slice+:16] == T_915[16*kwt_slice+:16];
      end
    end
  end endgenerate
  assign T_916 = kwt_time_gt[3]
               | (kwt_time_eq[3] & kwt_time_gt[2])
               | ((&kwt_time_eq[3:2]) & kwt_time_gt[1])
               | ((&kwt_time_eq[3:1]) & (kwt_time_gt[0] | kwt_time_eq[0]));"""
    increment = """  assign T_906[15:0]  = T_904[15:0]  + 16'd1;
  assign T_906[31:16] = T_904[31:16] + {15'd0, &T_904[15:0]};
  assign T_906[47:32] = T_904[47:32] + {15'd0, &T_904[31:0]};
  assign T_906[63:48] = T_904[63:48] + {15'd0, &T_904[47:0]};
  assign T_906[64]    = &T_904;"""
    for old, new in (("  assign T_916 = T_904 >= T_915;", comparison),
                     ("  assign T_906 = T_904 + 64'h1;", increment)):
        if source.count(old) != 1:
            raise RuntimeError("Unexpected upstream CLINT expression: " + old)
        source = source.replace(old, new)
    return source


def cut_fetch_dispatch_feedback(source):
    # A response may fill an empty IR. Stop looking through the old IR to
    # the EXU decoder and dispatch decision in the same clock cycle.
    old = "  assign ifu_ir_i_ready   = (~ir_valid_r) | ir_valid_clr;"
    if source.count(old) != 1:
        raise RuntimeError("Unexpected upstream IFU response admission")
    return source.replace(old, "  assign ifu_ir_i_ready   = ~ir_valid_r;")


def wait_for_retired_jalr_operands(source):
    # The read port and predecessor write are free once the IR and OITF
    # are empty. In particular do not speculate on same-cycle EXU dispatch.
    dependency = """  wire jalr_predecessor_pending = !oitf_empty || !ir_empty;
  wire jalr_rs1x1_dep = dec_i_valid && dec_jalr && dec_jalr_rs1x1 && jalr_predecessor_pending;
  wire jalr_rs1xn_dep = dec_i_valid && dec_jalr && dec_jalr_rs1xn && jalr_predecessor_pending;

  wire rs1xn_rdrf_r;"""
    source, count = re.subn(r"(?ms)^  wire jalr_rs1x1_dep = .*?^  wire rs1xn_rdrf_r;",
                            dependency, source)
    old = "((~jalr_rs1xn_dep) | jalr_rs1xn_dep_ir_clr)"
    if count != 1 or source.count(old) != 1:
        raise RuntimeError("Unexpected upstream IFU JALR dependency check")
    return source.replace(old, "(~jalr_rs1xn_dep)")


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
    generated_clock.write_text(use_common_cpu_clock(native_clock.read_text(encoding="utf-8")),
                               encoding="utf-8")
    native_timer = official / "perips/sirv_clint.v"
    generated_timer = out / native_timer.name
    generated_timer.write_text(pipeline_timer(native_timer.read_text(encoding="utf-8")), encoding="utf-8")
    native_fetch = official / "core/e203_ifu_ifetch.v"
    native_bpu = official / "core/e203_ifu_litebpu.v"
    generated_fetch = out / native_fetch.name
    generated_bpu = out / native_bpu.name
    generated_fetch.write_text(cut_fetch_dispatch_feedback(native_fetch.read_text(encoding="utf-8")),
                               encoding="utf-8")
    generated_bpu.write_text(wait_for_retired_jalr_operands(native_bpu.read_text(encoding="utf-8")),
                             encoding="utf-8")
    skip = set(OVERLAYS) | {native_dtcm.name, native_clock.name, native_timer.name, native_fetch.name, native_bpu.name,
                           "GENERIC_RVT_SMIC.v", "GENERIC_RVT_ARM.v"}
    official_sources = []
    for directory in PLATFORM_DIRS:
        subtree = official / directory
        if not subtree.is_dir():
            raise FileNotFoundError(str(subtree))
        official_sources.extend(path for path in sorted(subtree.rglob("*.v")) if path.name not in skip)
    accel = [ROOT / line for line in (ROOT / "rtl.f").read_text().splitlines() if line]
    sources = (official_sources + accel + [SOC / "rtl" / name for name in OVERLAYS]
               + [generated, generated_clock, generated_timer, generated_fetch, generated_bpu])
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
        for path in (native_dtcm, native_clock, native_timer, native_fetch, native_bpu):
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
        "original_clint_sha256": digest(native_timer),
        "original_ifetch_sha256": digest(native_fetch),
        "original_litebpu_sha256": digest(native_bpu),
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
