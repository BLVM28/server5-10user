from pathlib import Path
import zipfile,re
H=Path('/storage2/2026contest/server5/s5_10usr');assert Path.cwd().resolve()==H
z=zipfile.ZipFile('/storage1/admin_public_dir/SOC_RTL_2025/e203_hbirdv2-master_1013_update_sim.zip')
names=z.namelist()
for pat in ['e203_subsys_nice_core.v','e203_subsys_sysmem.v','e203_defines.v','e203_cpu_top.v','e203_subsys_main.v']:
 for n in names:
  if n.endswith('/'+pat):
   print('FILE',n)
   s=z.read(n).decode(errors='replace').splitlines()
   for i,line in enumerate(s):
    if re.search(r'assign.*(rdata|ready|valid)|SYS_MEM|SYSMEM|NICE|NICE_REG|MEM_BASE|NICE_MEM|NICE_OPCODE',line):print(str(i+1)+': '+line.strip())
print('FIRMWARE_RELEVANT', [n for n in names if n.endswith(('.ld','.lds','.elf','.hex','.dump'))][:35])
print('PUBLIC2025LAB',sorted(x.name for x in Path('/storage1/admin_public_dir/2025_Lab').iterdir()))
