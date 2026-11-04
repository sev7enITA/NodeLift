"""Summarize the matched upstream API follow-up without hiding slower workloads."""
from pathlib import Path
import json,statistics,shutil
P=Path(__file__).resolve().parent;A=P.parents[1]/'artifacts/draft-format-2026-11-04';E=P/'results/api-control';E.mkdir(exist_ok=True)
assert json.loads((A/'api-control-status.json').read_text())['exit_code']==0
r=[json.loads(x) for x in (A/'api-control/runs.jsonl').read_text().splitlines()];assert len(r)==36
base={(x['rep'],x['prompt']):x for x in r if x['arm']=='greedy'};pairs=[]
for x in r:
 if x['arm']!='assisted':continue
 b=base[x['rep'],x['prompt']];pairs.append({'rep':x['rep'],'prompt':x['prompt'],'exact_tokens':b['tokens']==x['tokens'],'ratio':b['seconds']/x['seconds'],'saved_seconds':b['seconds']-x['seconds'],'ttft_delta_ms':1000*(x['ttft_seconds']-b['ttft_seconds'])})
qs=json.loads((P/'prompts.json').read_text());summary={'scope':'Post-hoc matched upstream API control, 6 workloads and 3 repeated pairs each; no distributed inference','pairs':pairs,'exact_pairs':sum(x['exact_tokens'] for x in pairs),'n':len(pairs),'median_ratio':statistics.median(x['ratio'] for x in pairs),'median_ttft_delta_ms':statistics.median(x['ttft_delta_ms'] for x in pairs),'by_prompt':[]}
for i,q in enumerate(qs):
 sub=[x for x in pairs if x['prompt']==i];summary['by_prompt'].append({'id':q['id'],'median_ratio':statistics.median(x['ratio'] for x in sub),'min_ratio':min(x['ratio'] for x in sub),'max_ratio':max(x['ratio'] for x in sub),'median_saved_seconds':statistics.median(x['saved_seconds'] for x in sub),'median_ttft_delta_ms':statistics.median(x['ttft_delta_ms'] for x in sub),'exact_pairs':sum(x['exact_tokens'] for x in sub),'candidate_for_new_heldout_trials':all(x['exact_tokens'] and x['ratio']>1 for x in sub)})
for name in ['runs.jsonl','manifest.json','warmup.json']:shutil.copyfile(A/'api-control'/name,E/name)
for name in ['diagnostic.json','diagnostic-status.json','diagnostic.log','api-control-status.json','api-control.log']:shutil.copyfile(A/name,P/'results'/name)
(E/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='pairs'},indent=2))
