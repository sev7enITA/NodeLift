"""Pair completed NodeLift runs by prompt and repetition; retain all outcomes."""
import hashlib,json,statistics,sys
from pathlib import Path

def sha(path):
 with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def analyze(folder):
 folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text());rows=[json.loads(line) for line in (folder/'runs.jsonl').read_text().splitlines() if line]
 host={(r['prompt_id'],r['repetition']):r for r in rows if r['mode']=='host'}
 results=[]
 for width in (1,4,8,16):
  candidates=[r for r in rows if r['mode']=='local_draft' and r['draft_k']==width];pairs=[]
  for r in candidates:
   b=host.get((r['prompt_id'],r['repetition']))
   p={'prompt_id':r['prompt_id'],'repetition':r['repetition'],'candidate_status':r['status'],'host_status':b['status'] if b else 'missing','comparable':False}
   if b and r['status']==b['status']=='completed':
    cm,bm=r['metrics'],b['metrics'];p.update(comparable=True,exact_tokens=r['tokens']==b['tokens'],same_finish=r['finish_reason']==b['finish_reason'],candidate_generated=len(r['tokens']),host_generated=len(b['tokens']),candidate_ms=cm['elapsed_seconds']*1000,host_ms=bm['elapsed_seconds']*1000,paired_speedup=bm['elapsed_seconds']/cm['elapsed_seconds'],saved_ms=(bm['elapsed_seconds']-cm['elapsed_seconds'])*1000,ttft_change_ms=cm['ttft_ms']-bm['ttft_ms'],accepted=cm['accepted_tokens'],proposed=cm['proposed_tokens'],fallbacks=cm['fallbacks'])
   pairs.append(p)
  c=[p for p in pairs if p['comparable']];equal=[p for p in c if p['exact_tokens'] and p['same_finish']]
  def med(field):return statistics.median(p[field] for p in c) if c else None
  results.append({'draft_width':width,'planned_pairs':len(manifest['prompts'])*manifest['repetitions'],'candidate_runs':len(candidates),'completed_pairs':len(c),'exact_tokens_and_finish_pairs':len(equal),'median_paired_speedup':med('paired_speedup'),'faster_pairs':sum(p['paired_speedup']>1 for p in c),'min_paired_speedup':min((p['paired_speedup'] for p in c),default=None),'max_paired_speedup':max((p['paired_speedup'] for p in c),default=None),'median_saved_ms':med('saved_ms'),'median_ttft_change_ms':med('ttft_change_ms'),'total_accepted':sum(p['accepted'] for p in c),'total_proposed':sum(p['proposed'] for p in c),'pairs':pairs})
 return {'session':folder.name,'planned_runs':len(manifest['plan']),'observed_runs':len(rows),'completed_runs':sum(r['status']=='completed' for r in rows),'manifest_sha256':sha(folder/'manifest.json'),'runs_sha256':sha(folder/'runs.jsonl'),'conditions':results}
if __name__=='__main__':
 output=Path(sys.argv[1]);out={'warning':'Exploratory same-machine sessions; not independent hardware, no CI, draft resident in host arm.','sessions':[analyze(p) for p in sys.argv[2:]]};output.write_text(json.dumps(out,indent=2)+'\n')
 for s in out['sessions']:
  print(s['session'],s['observed_runs'],'/',s['planned_runs'])
  for c in s['conditions']:print(' k',c['draft_width'],'paired',c['completed_pairs'],'exact',c['exact_tokens_and_finish_pairs'],'speedup',round(c['median_paired_speedup'],3) if c['median_paired_speedup'] else None,'TTFT delta ms',round(c['median_ttft_change_ms'],1) if c['median_ttft_change_ms'] is not None else None)
