from pathlib import Path
import zipfile,sys
H=Path('/storage2/2026contest/server5/s5_10usr');assert Path.cwd().resolve()==H
z=zipfile.ZipFile('/storage1/admin_public_dir/SOC_RTL_2025/e203_hbirdv2-master_1013_update_sim.zip')
mode=sys.argv[1]
if mode=='list':
 for n in z.namelist():
  if '/vsim/' in n and n.endswith(('.v','.f','.mk','Makefile','.sh')) and '/install/rtl/' not in n and '/install/testcase/' not in n:print(n)
elif mode=='soc':
 n='e203_hbirdv2-master/rtl/e203/soc/e203_soc_top.v'
 s=z.read(n).decode(errors='replace').splitlines()
 for i in range(125,181):print(str(i+1)+': '+s[i])
else:
 n=mode;start=int(sys.argv[2]) if len(sys.argv)>2 else 0
 s=z.read(n).decode(errors='replace').splitlines()
 for i in range(start,min(start+48,len(s))):print(str(i+1)+': '+s[i])
