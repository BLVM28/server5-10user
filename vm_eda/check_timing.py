"""Strict report acceptance; a successful tool exit is insufficient."""
from pathlib import Path
import re,json,argparse,os,math
def inspect(base):
 rows=[]
 for corner in ['slow','fast']:
  d=base/('sta_eco_'+corner);row={'corner':corner,'execution_complete':False,'constraints_met':False}
  if not d.is_dir():rows.append(row);continue
  log=(d/'tool.log').read_text(errors='replace')
  row['execution_complete']='KWT_TEMPUS_STA_COMPLETE' in log and not re.search(r'\*\*ERROR|^Error\s*:',log,re.M)
  for kind in ['setup','hold']:
   s=(d/(kind+'.rpt')).read_text()
   m=re.search(r'Slack Time\s+(-?[\d.]+)',s);row[kind+'_slack_ns']=float(m.group(1)) if m else None
  c=(d/'constraints.rpt').read_text();drv=(d/'drv.rpt').read_text()
  row['violation_lines']=[l.strip() for l in c.splitlines() if 'VIOLATED' in l]
  row['drv_groups_clean']=drv.count('No Violations found')==3
  row['constraints_met']=row['execution_complete'] and not row['violation_lines'] and row['drv_groups_clean'] and all(row[k+'_slack_ns'] is not None and math.isfinite(row[k+'_slack_ns']) and row[k+'_slack_ns']>=0 for k in ['setup','hold'])
  row['coverage_report']=str(d/'coverage.rpt');rows.append(row)
 return {'scope':'dot64 GPDK045 pre-layout; ideal clock, no extracted parasitics or variation derates','corners':rows,'reported_constraints_met':all(x['constraints_met'] for x in rows)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('version',choices=['v1','v2']);a=p.parse_args()
 base=Path(os.environ['KWT_VM_ROOT'])/'results'/a.version;r=inspect(base)
 (base/'timing_summary.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
 raise SystemExit(0 if r['reported_constraints_met'] else 1)
