"""Check E203 wrapper with original config headers and real Liberty-named SRAM.

Still a BFM, not a CPU execution test. Writes only into this private project.
"""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
assert ROOT.parent.resolve()==Path('/storage2/2026contest/server5/s5_10usr').resolve()
inc=ROOT/'include';inc.mkdir(exist_ok=True)
with zipfile.ZipFile('/storage1/admin_public_dir/SOC_RTL_2025/e203_hbirdv2-master_1013_update_sim.zip') as z:
    for name in ['e203_defines.v','config.v']:
        found=[n for n in z.namelist() if n.endswith('/rtl/e203/core/'+name)]
        assert len(found)==1
        (inc/name).write_bytes(z.read(found[0]))
tb=(ROOT/'tb/tb_kwt_system.sv').read_text()
old='kwt_nice_core #(.MEM_BASE(BASE),.MEM_BYTES(BYTES),.W_BANK_AW(WAW),.PACK_LOW_FIRST(PACK)) dut(.*);'
assert old in tb
tb=tb.replace(old,'e203_subsys_nice_core dut(.*);')
tb=tb.replace('dut.core.','dut.u_kwt.core.').replace('dut.c_sat','dut.u_kwt.c_sat').replace('dut.c_cycles','dut.u_kwt.c_cycles')
(ROOT/'tb/tb_kwt_binding.sv').write_text(tb)
s=(ROOT/'py/run_foundry_server.py').read_text()
s=s.replace("OUT=ROOT/'build'/'foundry_functional'","OUT=ROOT/'build'/'foundry_binding'")
s=s.replace("ROOT/'tb/tb_kwt_system.sv'","ROOT/'tb/tb_kwt_binding.sv'")
s=s.replace("sources+=macros+", "sources+=[ROOT/'integration/e203_subsys_nice_core.v']+macros+")
s=s.replace("'+define+ARM_UD_MODEL']", "'+define+ARM_UD_MODEL','+define+SYNTHESIS','+incdir+'+str(inc),'+define+KWT_MEM_BASE=268435456','+define+KWT_MEM_BYTES=524288']")
s=s.replace("'qualification':'ARM_UD_MODEL", "'qualification':'Original E203 headers + wrapper + Liberty cell names; ARM_UD_MODEL")
exec(compile(s,str(ROOT/'py/run_foundry_server.py'),'exec'),dict(__file__=__file__,inc=inc))
