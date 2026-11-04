"""Derive paired results without treating repeats as independent workloads."""
from pathlib import Path
import json,statistics,shutil,hashlib
P=Path(__file__).resolve().parent;A=P.parents[1]/'artifacts/draft-format-2026-11-04';E=P/'results';E.mkdir(exist_ok=True)
status=json.loads((A/'cached-main-status.json').read_text());assert status['exit_code']==0,status
runs=[json.loads(s) for s in (A/'main/runs.jsonl').read_text().splitlines()];assert len(runs)==90
manifest=json.loads((A/'main/manifest.json').read_text());assert manifest['source_sha256']==hashlib.sha256((P/'cached_probe.py').read_bytes()).hexdigest()
base={(r['rep'],r['prompt']):r for r in runs if r['arm']=='target'}
v={'scope':'Six workloads with three same-session repeats; experimental MPS prototype, not physical offload','arms':{},'target_repeat_consistency':{},'format_probe':{}}
for prompt in range(6):
 values=[base[rep,prompt]['tokens'] for rep in range(3)];v['target_repeat_consistency'][str(prompt)]=all(x==values[0] for x in values)
for arm in manifest['arms']:
 rows=[r for r in runs if r['arm']==arm];pairs=[]
 for r in rows:
  b=base[r['rep'],r['prompt']];exact=r['tokens']==b['tokens']
  assert len(r['tokens'])<=manifest['budget']
  if arm!='upstream_assisted':
   assert r['accepted']+r['discarded']==r['proposed']
   assert abs(r['seconds']-sum(r['phases_seconds'].values())-r['unattributed_seconds'])<1e-6
  pairs.append({'rep':r['rep'],'prompt':r['prompt'],'exact_tokens':exact,'speed_ratio':b['seconds']/r['seconds'],'saved_seconds':b['seconds']-r['seconds'],'ttft_delta_seconds':r['ttft_seconds']-b['ttft_seconds'],'seconds':r['seconds'],'target_seconds':b['seconds'],'output_tokens':len(r['tokens'])})
 by_prompt=[]
 for prompt in range(6):
  subset=[r for r in pairs if r['prompt']==prompt];ratios=[r['speed_ratio'] for r in subset]
  by_prompt.append({'prompt':prompt,'id':manifest['prompts'][prompt]['id'],'median_ratio':statistics.median(ratios),'min_ratio':min(ratios),'max_ratio':max(ratios),'exact_pairs':sum(x['exact_tokens'] for x in subset)})
 v['arms'][arm]={'pairs':pairs,'by_prompt':by_prompt,'exact_pairs':sum(r['exact_tokens'] for r in pairs),'n':len(pairs),'median_seconds':statistics.median(r['seconds'] for r in rows),'median_paired_speed_ratio':statistics.median(r['speed_ratio'] for r in pairs),'median_saved_seconds':statistics.median(r['saved_seconds'] for r in pairs),'median_ttft_delta_ms':1000*statistics.median(r['ttft_delta_seconds'] for r in pairs),'proposed':sum(r.get('proposed',0) for r in rows) if arm!='upstream_assisted' else None,'accepted':sum(r.get('accepted',0) for r in rows) if arm!='upstream_assisted' else None,'discarded':sum(r.get('discarded',0) for r in rows) if arm!='upstream_assisted' else None}
 if arm!='upstream_assisted':
  keys=set(k for r in rows for k in r['phases_seconds']);v['arms'][arm]['mean_phase_seconds']={k:statistics.mean(r['phases_seconds'].get(k,0) for r in rows) for k in sorted(keys)}
  v['arms'][arm]['mean_unattributed_seconds']=statistics.mean(r['unattributed_seconds'] for r in rows)
format_rows=json.loads((A/'format-probe.json').read_text())['rows']
for mode in ['raw','aligned']:
 rows=[r for r in format_rows if r['mode']==mode];v['format_probe'][mode]={'matching':sum(r['matches'] for r in rows),'candidate_positions':128,'first_block_matches':[r['blocks'][0]['initial_matches'] for r in rows]}
for f in ['format-probe.json','cached-main-status.json','cached-smoke-status.json','cached-smoke-retry-status.json','cached-smoke.log','cached-smoke-retry.log','cached-main.log','cached_probe-initial.py']:
 shutil.copyfile(A/f,E/f)
for f in ['runs.jsonl','manifest.json','warmup.json']:shutil.copyfile(A/'main'/f,E/f)
(E/'summary.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({arm:{k:x[k] for k in ['exact_pairs','n','median_seconds','median_paired_speed_ratio','median_ttft_delta_ms','proposed','accepted']} for arm,x in v['arms'].items()},indent=2))
print('Target repeats:',v['target_repeat_consistency'])
