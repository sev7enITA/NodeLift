"""Evidence integrity and accounting checks, separate from model qualification."""
from pathlib import Path
import json,math
P=Path(__file__).resolve().parent;R=P/'results';checks=[]
def check(name,value):checks.append(dict(name=name,passed=bool(value)));assert value,name
def rows(path):return [json.loads(v) for v in path.read_text().splitlines()]
for lane in ['native','fp32']:
 data=rows(R/f'envelope-{lane}/runs.jsonl')
 check(lane+' planned replay count',len(data)==24)
 check(lane+' unique tasks',len({(v['prompt_id'],v['rep'],v['width']) for v in data})==24)
 for i,v in enumerate(data):
  check(f'{lane} {i} token alignment',len(v['predictions'])==len(v['reference_tokens'])==sum(b['width'] for b in v['blocks']))
  check(f'{lane} {i} honest exact flag',v['exact']==(v['predictions']==v['reference_tokens']))
  check(f'{lane} {i} positive measured timing',v['seconds']>0 and v['decode_seconds']>0 and v['prefill_seconds']>=0)
 data1=[v for v in data if v['width']==1];check(lane+' width-one reference alignment',all(v['exact'] for v in data1))
readiness=json.loads((R/'device-readiness.json').read_text());check('initial boolean readiness is false',readiness['available_worker_selected'] is False)
data=rows(R/'accounting/runs.jsonl');check('planned complete request count',len(data)==18)
for i,v in enumerate(data):
 if v['arm']=='charged':
  check(f'{i} phase balance',abs(v['seconds']-sum(v['phases'].values())-sum(v['telemetry'].values())-v['unattributed_seconds'])<1e-8)
  check(f'{i} nonnegative unattributed overhead',v['unattributed_seconds']>=0)
 if v['trace']:
  ks=[r['k'] for r in v['trace']];check(f'{i} no stale-state resume',0 not in ks or all(k==0 for k in ks[ks.index(0):]))
for filename in ['localization','localization-attention','projection-probe']:
 v=json.loads((R/filename/'result.json').read_text());check(filename+' instrumentation equivalence',all(a['instrumentation_delta']['changed']==0 for a in v['results'].values()))
for folder in sorted(R.glob('monitor-*')):
 v=json.loads((folder/'completion.json').read_text());failed=folder.name in ['monitor-localization','monitor-attention'];check(folder.name+' retained exit status',(v['exit_code']!=0)==failed)
(P/'verification.json').write_text(json.dumps(dict(checks=checks,scope='Artifact consistency, not broad model correctness or physical acceleration'),indent=2)+'\n');print(len(checks),'integrity checks passed')
