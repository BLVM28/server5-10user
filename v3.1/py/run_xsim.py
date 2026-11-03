"""Run v3.1 through the project's existing Vivado regression and frozen v2 vectors."""
import importlib.util
from pathlib import Path
import shutil
import sys

V3 = Path(__file__).resolve().parents[1]
V2 = V3.parent / "v2"
spec = importlib.util.spec_from_file_location("kwt_xsim", V2 / "py/run_xsim.py")
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
driver.ROOT = V3

if __name__ == "__main__":
    if "--panel-only" in sys.argv:
        sys.argv.remove("--panel-only")
        # Recreate the single-variable trial without modifying release RTL.
        trial=V3/"build/prefetch_reference"
        (trial/"rtl").mkdir(parents=True,exist_ok=True)
        (trial/"tb").mkdir(exist_ok=True)
        shutil.copyfile(V3/"rtl.f",trial/"rtl.f")
        for src in (V3/"rtl").glob("*.sv"):
            source=V3.parent/"v3/rtl"/src.name if src.name=="kwt_mul16_pipe.sv" else src
            shutil.copyfile(source,trial/"rtl"/src.name)
        for name in ("kwt_sram_sim.sv","tb_kwt_system.sv"):
            shutil.copyfile(V3/"tb"/name,trial/"tb"/name)
        driver.ROOT=trial
        if any(opt in sys.argv for opt in ("--tops","--vectors","--tag")):
            raise SystemExit("The panel-only experiment fixes its top, vectors and tag")
        sys.argv+=["--tops","tb_kwt_system","--vectors",str(V2/"vec/real_speech/worst"),"--tag","panel_only"]
    if "--vectors" not in sys.argv:
        sys.argv.extend(["--vectors", str(V2 / "vec")])
    if "--tops" not in sys.argv:
        sys.argv.extend(["--tops", "tb_kwt_arithmetic", "tb_v3_carries",
                         "tb_kwt_system", "tb_kwt_overlap", "tb_kwt_negative",
                         "tb_kwt_icb", "tb_kwt_mul_pipeline"])
    driver.main()
