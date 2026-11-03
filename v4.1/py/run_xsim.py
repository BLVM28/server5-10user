"""Local reproducible HDL regression; fail on exit errors OR missing PASS marker."""
import argparse,hashlib,json,os,re,subprocess,time,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser()
    p.add_argument('--bin',type=Path,default=Path('D:/vivado/Vivado/2023.2/bin'))
    p.add_argument('--tops',nargs='+',default=['tb_kwt_arithmetic','tb_v3_carries','tb_kwt_icb','tb_kwt_system','tb_kwt_compact','tb_kwt_overlap','tb_kwt_negative','tb_kwt_mul_pipeline','tb_kwt_codec'])
    p.add_argument('--define',action='append',default=[])
    p.add_argument('--tag',default='xsim')
    p.add_argument('--vectors',type=Path,default=ROOT/'vec')
    args=p.parse_args()
    if not any(x=='--vectors' or x.startswith('--vectors=') for x in sys.argv[1:]):args.vectors=ROOT.parent/'v2/vec'
    sources=[ROOT/s.strip() for s in (ROOT/'rtl.f').read_text().splitlines() if s.strip()]
    sources += [ROOT/'tb/kwt_sram_sim.sv']+[ROOT/'tb'/f'{top}.sv' for top in args.tops]
    if {'tb_kwt_compact','tb_kwt_export','tb_kwt_block8','tb_kwt_block8_immediate'}.intersection(args.tops) and 'tb_kwt_system' not in args.tops:sources.append(ROOT/'tb/tb_kwt_system.sv')
    out=ROOT/'build'/args.tag
    out.mkdir(parents=True,exist_ok=True)
    if args.vectors.resolve()!=(ROOT/'vec').resolve():
        # Avoid cmd.exe/.bat plusarg quoting ambiguity. Only replace the TB's
        # default data directory in an explicitly retained generated copy.
        new_sources=[]
        for source in sources:
            if source.name.startswith('tb_kwt_'):
                data=source.read_text()
                relative=os.path.relpath(args.vectors.resolve(),out).replace('\\','/')
                data=data.replace('dir="../../vec"','dir="'+relative+'"')
                target=out/source.name;target.write_text(data,encoding='utf-8');new_sources.append(target)
            else:new_sources.append(source)
        sources=new_sources
    filelist=out/'sources.f'
    # Vivado's .f parser on Windows is not reliably UTF-8; relative paths avoid
    # dependence on the Chinese workspace name without moving user files.
    filelist.write_text('\n'.join('"'+os.path.relpath(s,out).replace('\\','/')+'"' for s in sources)+'\n',encoding='utf-8')
    results={'tool':'Vivado Simulator 2023.2','defines':args.define,'tests':[],
      'source_sha256':{str(s.relative_to(ROOT)):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},
      'vector_directory':str(args.vectors.resolve()),
      'vector_sha256':{s.name:hashlib.sha256(s.read_bytes()).hexdigest() for s in args.vectors.glob('*.hex')}}
    def run(tool,params,label):
        started=time.monotonic()
        command=['cmd.exe','/d','/c',str(args.bin/(tool+'.bat'))]+params
        r=subprocess.run(command,cwd=out,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600)
        (out/(label+'.log')).write_bytes(r.stdout)
        output=r.stdout.decode('utf-8',errors='replace')
        if r.returncode!=0:
            print(output[-6000:],flush=True)
            raise RuntimeError(f'{label} failed with exit {r.returncode}')
        print(f'{label}: exit 0, {time.monotonic()-started:.2f}s',flush=True)
        return output
    define_args=[item for d in args.define for item in ['-d',d]]
    run('xvlog',['-sv',*define_args,'-f','sources.f'],'compile')
    for top in args.tops:
        run('xelab',[f'work.{top}','-s',top+'_sim','-debug','typical','-timescale','1ns/1ps'],'elaborate_'+top)
        # Each run directory is exactly build/<tag>; TB defaults to ../../vec.
        output=run('xsim',[top+'_sim','-runall'],top)
        markers=re.findall(r'ALL PASS,\s*([0-9]+)/([0-9]+)[^\r\n]*',output)
        if not markers or any(a!=b for a,b in markers) or re.search(r'Fatal:|\$fatal|FATAL',output):
            print(output[-6000:],flush=True)
            raise RuntimeError('No valid complete PASS marker in '+top)
        print('\n'.join(re.findall(r'ALL PASS[^\r\n]*',output)),flush=True)
        results['tests'].append({'top':top,'pass_markers':markers})
    (out/'results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__': main()
