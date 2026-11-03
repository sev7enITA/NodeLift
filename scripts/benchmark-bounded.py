#!/usr/bin/env python3
"""Frozen-order real-model bounded pipeline pilot. No synthetic speed results."""
import argparse,hashlib,json,random,statistics,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'host'))
from nodelift.engine import Controller
from nodelift.state import State
from nodelift.native import library_path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--repetitions',type=int,default=3);p.add_argument('--tokens',type=int,default=128);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/'.models/llama3.1-8b-ollama.gguf';DRAFT=ROOT/'.models/Llama-3.2-1B-Instruct-Q4_K_M.gguf'
prompts=['Write a Python function returning the unique elements of a list in their original order. Explain its time complexity.', 'Explain in Italian why network latency matters when computers collaborate. Use three brief points.', 'Write a concise comparison of RAM capacity and memory bandwidth for local language model inference.']
arms=[('host','serial','serial',1),('local_draft','serial','serial',4),('local_draft','serial','bounded_v1',4),('local_draft','experimental_batch','serial',1),('local_draft','experimental_batch','serial',4),('local_draft','experimental_batch','serial',8),('local_draft','experimental_batch','bounded_v1',4),('lookup','experimental_batch','serial',4)]
plan=[];rng=random.Random(20261103)
for rep in range(a.repetitions):
 for prompt in range(len(prompts)):
  order=list(range(len(arms)));rng.shuffle(order);plan.extend((rep,prompt,arm) for arm in order)
sha=lambda path:hashlib.file_digest(open(path,'rb'),'sha256').hexdigest()
manifest=dict(prompts=prompts,arms=arms,plan=plan,seed=20261103,max_tokens=a.tokens,n_ctx=2048,threads=8,gpu_layers_requested=999,target_sha256=sha(TARGET),draft_sha256=sha(DRAFT),native_sha256=sha(library_path()),source_sha256={str(f.relative_to(ROOT)):sha(f) for f in [Path(__file__),ROOT/'native/core.cpp',ROOT/'host/nodelift/engine.py',ROOT/'host/nodelift/lookahead.py']},limitations=['Exploratory single-session pilot, not statistical qualification','Target and local draft resident in every arm after warmup','No network or phone in this local arm set','No energy measurement','Greedy output equality checked; different outputs disqualify speedup claims','Native/worker timing, not client-observed TTFT; upstream HTTP separately scoped'])
(a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with tempfile.TemporaryDirectory() as temp:
 c=Controller(State(Path(temp)));c.configure(dict(target_model=str(TARGET.resolve()),draft_model=str(DRAFT.resolve()),n_ctx=2048,threads=8,gpu_layers=999))
 def run(body):
  c.start(body);deadline=time.monotonic()+180
  while c.busy:
   if time.monotonic()>deadline:c.stop();raise TimeoutError('pilot run deadline')
   time.sleep(.025)
  return c.status()['runs'][0]
 warm=run(dict(prompt='Say hello.',mode='local_draft',max_tokens=16,draft_k=4));assert warm['status']=='completed',warm.get('error')
 rows=[]
 with (a.output/'runs.jsonl').open('w') as out:
  for i,(rep,prompt,arm) in enumerate(plan):
   mode,verify,pipeline,k=arms[arm]
   r=run(dict(prompt=prompts[prompt],mode=mode,verification_mode=verify,pipeline=pipeline,draft_k=k,max_tokens=a.tokens))
   r.update(repetition=rep,prompt_id=prompt,arm=arm)
   if 'identity' in r:
    for key in ('target_model','draft_model'):r['identity']['config'][key]=Path(r['identity']['config'][key]).name
   rows.append(r);out.write(json.dumps(r,ensure_ascii=False)+'\n');out.flush()
   print(i+1,len(plan),rep,prompt,arm,r['status'],round(r['metrics']['request_total_ms'],1),flush=True)
 for n in (c.target,c.draft):
  if n:n.close()
base={(r['repetition'],r['prompt_id']):r for r in rows if r['arm']==0}
summary=[]
for arm in range(1,len(arms)):
 values=[]
 for r in rows:
  if r['arm']!=arm:continue
  b=base[r['repetition'],r['prompt_id']]
  good=r['status']==b['status']=='completed'
  values.append(dict(repetition=r['repetition'],prompt_id=r['prompt_id'],completed=good,exact_tokens=good and r.get('tokens')==b.get('tokens'),speedup=b['metrics']['request_total_ms']/r['metrics']['request_total_ms'] if good else None,ttft_delta_ms=r['metrics'].get('worker_first_token_ready_ms',0)-b['metrics'].get('worker_first_token_ready_ms',0) if good else None,cleanup_ms=r['metrics']['cleanup_ms']))
 summary.append(dict(arm=arm,definition=arms[arm],pairs=values,all_exact=all(x['exact_tokens'] for x in values),median_speedup=statistics.median(x['speedup'] for x in values if x['completed'])))
(a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
