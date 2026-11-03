"""Run v3 through the project's existing Vivado regression and frozen v2 vectors."""
import importlib.util
from pathlib import Path
import sys

V3 = Path(__file__).resolve().parents[1]
V2 = V3.parent / "v2"
spec = importlib.util.spec_from_file_location("kwt_xsim", V2 / "py/run_xsim.py")
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
driver.ROOT = V3

if __name__ == "__main__":
    if "--vectors" not in sys.argv:
        sys.argv.extend(["--vectors", str(V2 / "vec")])
    if "--tops" not in sys.argv:
        sys.argv.extend(["--tops", "tb_kwt_arithmetic", "tb_v3_carries",
                         "tb_kwt_system", "tb_kwt_overlap", "tb_kwt_negative",
                         "tb_kwt_icb", "tb_kwt_mul_pipeline"])
    driver.main()
