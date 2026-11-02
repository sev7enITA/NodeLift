"""Analyze all completed fixed/adaptive trials against matched host controls."""
import json,statistics,sys
from collections import Counter
from pathlib import Path
folder=Path(sys.argv[1]);manifest=json.loads((folder/'manifest.json').read_text());rows=[json.loads(x) for x in (folder/'runs.jsonl').read_text().splitlines() if x]
host={(r['prompt_id'],r['repetition']):r for r in rows if r['arm']=='host'};conditions=[]
for arm in ('fixed','adaptive'):
 pairs=[];disabled=Counter();attempted=[]
 for r in [x for x in rows if x['arm']==arm]:
  b=host.get((r['prompt_id'],r['repetition']));p={'prompt_id':r['prompt_id'],'repetition':r['repetition'],'candidate_status':r['status'],'baseline_status':b['status'] if b else 'missing','comparable':False}
  if b and r['status']==b['status']=='completed':
   cm,bm=r['metrics'],b['metrics'];blocks=r.get('blocks',[]);draft_blocks=sum(bool(x.get('verification_batch_width')) for x in blocks);attempted.append(draft_blocks);reason=cm.get('draft_disabled_reason') or 'not_disabled';disabled[reason]+=1
   p.update(comparable=True,exact_tokens=r['tokens']==b['tokens'],same_finish=r['finish_reason']==b['finish_reason'],speedup=bm['elapsed_seconds']/cm['elapsed_seconds'],saved_ms=(bm['elapsed_seconds']-cm['elapsed_seconds'])*1000,ttft_change_ms=cm['ttft_ms']-bm['ttft_ms'],draft_blocks=draft_blocks,accepted=cm['accepted_tokens'],proposed=cm['proposed_tokens'],disabled_reason=reason)
  pairs.append(p)
 good=[x for x in pairs if x['comparable']];equal=[x for x in good if x['exact_tokens'] and x['same_finish']]
 conditions.append({'arm':arm,'candidate_runs':len(pairs),'completed_pairs':len(good),'exact_tokens_and_finish':len(equal),'faster_pairs':sum(x['speedup']>1 for x in good),'median_paired_speedup':statistics.median(x['speedup'] for x in good) if good else None,'median_saved_ms':statistics.median(x['saved_ms'] for x in good) if good else None,'median_ttft_change_ms':statistics.median(x['ttft_change_ms'] for x in good) if good else None,'disabled_reasons':dict(disabled),'total_draft_blocks':sum(attempted),'pairs':pairs})
r={'scope':'Third same-Mac exploratory period, not phone or independent hardware','planned_runs':len(manifest['plan']),'observed_runs':len(rows),'completed_runs':sum(x['status']=='completed' for x in rows),'conditions':conditions};Path(sys.argv[2]).write_text(json.dumps(r,indent=2)+'\n')
for x in conditions:print(x['arm'],'pairs',x['completed_pairs'],'exact',x['exact_tokens_and_finish'],'median',round(x['median_paired_speedup'],3) if x['median_paired_speedup'] else None,'disabled',x['disabled_reasons'])
