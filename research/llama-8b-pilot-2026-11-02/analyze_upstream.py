"""Compare upstream arms with their server-only baseline, retaining failures."""
import hashlib,json,statistics,sys
from pathlib import Path
folder=Path(sys.argv[1]);manifest=json.loads((folder/'manifest.json').read_text());rows=[json.loads(line) for line in (folder/'runs.jsonl').read_text().splitlines() if line]
base={(r['repetition'],r['prompt_id']):r for r in rows if r['arm']=='none'};conditions=[]
for arm in ('draft-simple','ngram-mod'):
 pairs=[]
 for r in [x for x in rows if x['arm']==arm]:
  b=base.get((r['repetition'],r['prompt_id']));p={'repetition':r['repetition'],'prompt_id':r['prompt_id'],'candidate_status':r['status'],'baseline_status':b['status'] if b else 'missing','comparable':False}
  if b and r['status']==b['status']=='completed':
   p.update(comparable=True,exact_tokens=r['tokens']==b['tokens'],same_stop=r['stop_type']==b['stop_type'],same_truncated=r['truncated']==b['truncated'],speedup=b['request_wall_seconds']/r['request_wall_seconds'],saved_ms=(b['request_wall_seconds']-r['request_wall_seconds'])*1000,candidate_tokens=len(r['tokens']),baseline_tokens=len(b['tokens']))
  pairs.append(p)
 complete=[x for x in pairs if x['comparable']];equal=[x for x in complete if x['exact_tokens'] and x['same_stop'] and x['same_truncated']]
 conditions.append({'arm':arm,'planned_pairs':len(manifest['prompts'])*manifest['repetitions'],'observed_candidates':len(pairs),'completed_pairs':len(complete),'equal_tokens_stop_and_truncation':len(equal),'faster_pairs':sum(x['speedup']>1 for x in complete),'median_paired_speedup':statistics.median(x['speedup'] for x in complete) if complete else None,'median_saved_ms':statistics.median(x['saved_ms'] for x in complete) if complete else None,'pairs':pairs})
result={'scope':'Local upstream HTTP timing. Do not compare raw wall time to NodeLift controller. TTFT not measured.','planned_runs':len(manifest['plan'])*len(manifest['prompts']),'observed_runs':len(rows),'completed_runs':sum(x['status']=='completed' for x in rows),'conditions':conditions}
Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
for c in conditions:print(c['arm'],'pairs',c['completed_pairs'],'exact',c['equal_tokens_stop_and_truncation'],'faster',c['faster_pairs'],'speedup',round(c['median_paired_speedup'],3) if c['median_paired_speedup'] else None)
