"""Fresh-process MLX screening/validation with measured costs and exact-output evidence."""
from pathlib import Path
import argparse,hashlib,json,time,random,statistics,gc,os
import psutil
import mlx.core as mx
from mlx_lm import load
from mlx_lm.generate import generate_step,speculative_generate_step
from adaptive_mlx import adaptive_generate_step
from policy import CostPolicy
P=Path(__file__).resolve().parent;R=P.parents[1];A=R/'artifacts/adaptive-targets-2026-11-05'
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def resources():
 m=psutil.virtual_memory();s=psutil.swap_memory();return {'available_bytes':m.available,'swap_used_bytes':s.used,'swap_in_bytes':s.sin,'swap_out_bytes':s.sout,'mlx_active_bytes':mx.get_active_memory(),'mlx_peak_bytes':mx.get_peak_memory(),'load_average':list(os.getloadavg())}
def run(model,draft,prefix,eos,arm,budget,host_cost):
 before=resources();assert before['available_bytes']>1.5*1024**3,'Available memory below reserve'
 policy=CostPolicy(host_cost) if arm=='adaptive' else None;trace=[];kw=dict(max_tokens=budget,prefill_step_size=512)
 inp=mx.array(prefix);mx.synchronize();start=time.perf_counter();first=None;tokens=[];accepted=0;finish='length'
 if arm=='host':gen=generate_step(inp,model,**kw)
 elif arm=='adaptive':gen=adaptive_generate_step(inp,model,draft,policy=policy,trace=trace,**kw)
 elif arm.startswith('instrumented'):gen=adaptive_generate_step(inp,model,draft,num_draft_tokens=int(arm.split('-')[1]),trace=trace,**kw)
 else:gen=speculative_generate_step(inp,model,draft,num_draft_tokens=int(arm.split('-')[1]),**kw)
 try:
  for item in gen:
   token=int(item[0]);now=time.perf_counter()
   if first is None:first=now
   tokens.append(token);accepted+=int(bool(item[2])) if len(item)>2 else 0
   if now-start>180:raise TimeoutError('Request exceeded 180 seconds')
   if token in eos:finish='stop';break
   if len(tokens)>=budget:break
 finally:gen.close()
 mx.synchronize();end=time.perf_counter();after=resources()
 return {'tokens':tokens,'finish':finish,'seconds':end-start,'ttft_seconds':first-start if first else None,'decode_seconds':end-first if first else None,'accepted_emitted_tokens':accepted,'trace':trace,'policy_decisions':policy.decisions if policy else [],'draft_disabled':policy.disabled if policy else None,'resources_before':before,'resources_after':after,'swap_growth_bytes':after['swap_used_bytes']-before['swap_used_bytes'],'token_count':len(tokens)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--target',choices=['14B','32B','0.6B'],required=True);ap.add_argument('--stage',choices=['smoke','screen','validate'],required=True);ap.add_argument('--block',type=int,default=0);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--selection',type=Path);a=ap.parse_args();a.out.mkdir(exist_ok=False,parents=True)
 catalog={r['repo']:r for r in json.loads((P/'catalog.json').read_text())};models={r['repo']:r for r in json.loads((A/'models.json').read_text())};tname=f'Qwen/Qwen3-{a.target}-MLX-4bit';dnames=['Qwen/Qwen3-0.6B-MLX-4bit','Qwen/Qwen3-1.7B-MLX-4bit']
 unique=set([tname]+dnames);estimated=sum(catalog[n]['bytes'] for n in unique);available=psutil.virtual_memory().available
 save(a.out/'admission.json',{'estimated_weight_bytes':estimated,'available_bytes':available,'working_allowance_bytes':int(1.5*1024**3),'required_bytes':int(estimated*1.08+1.5*1024**3)})
 if available<estimated*1.08+1.5*1024**3:raise MemoryError('Model pair does not fit the measured admission budget')
 loaded={n:load(models[n]['path']) for n in sorted(unique)};model,tok=loaded[tname];drafts={n:loaded[n][0] for n in dnames}
 vocab=tok.get_vocab();vocab_hash=hashlib.sha256(json.dumps(vocab,sort_keys=True).encode()).hexdigest()
 for n in dnames:assert loaded[n][1].get_vocab()==vocab,'Vocabulary mismatch'
 qs=json.loads((P/'prompts.json').read_text())
 def prefix(prompt):
  msgs=[{'role':'system','content':'You are a helpful assistant.'},{'role':'user','content':prompt}]
  canonical=loaded[dnames[0]][1].apply_chat_template(msgs,tokenize=False,add_generation_prompt=True,enable_thinking=False)
  seq=tok.encode(canonical,add_special_tokens=False)
  for n in dnames:assert loaded[n][1].encode(canonical,add_special_tokens=False)==seq,'Canonical token mismatch'
  return seq
 eos=set(tok.eos_token_ids)
 warm_prefix=prefix(qs['calibration']);calibrations=[run(model,None,warm_prefix,eos,'host',32,.05) for _ in range(3)]
 host_cost=statistics.median(x['decode_seconds']/max(1,x['token_count']-1) for x in calibrations[1:]);save(a.out/'calibration.json',{'scope':'Separate calibration prompt, not paired evaluation baseline','host_seconds_per_token':host_cost,'runs':calibrations})
 if a.stage=='smoke':
  checks=[]
  for k in [1,2,4,8]:
   for budget in [1,5,17]:
    b=run(model,drafts[dnames[0]],warm_prefix,eos,f'fixed-{k}',budget,host_cost);v=run(model,drafts[dnames[0]],warm_prefix,eos,f'instrumented-{k}',budget,host_cost);checks.append({'k':k,'budget':budget,'equal':b['tokens']==v['tokens'] and b['finish']==v['finish']});assert checks[-1]['equal'],checks[-1]
  ad=run(model,drafts[dnames[0]],warm_prefix,eos,'adaptive',32,host_cost);save(a.out/'smoke.json',{'checks':checks,'adaptive':ad});print('SMOKE COMPLETE',flush=True);return
 if a.stage=='screen':
  arms=[{'name':'host','draft':None,'mode':'host'}]+[{'name':d.split('/')[1]+'-'+mode,'draft':d,'mode':mode} for d in dnames for mode in ['fixed-2','fixed-4','fixed-8','adaptive']];prompts=qs['screening'];reps=1
 else:
  selected=json.loads(a.selection.read_text());arms=[{'name':'host','draft':None,'mode':'host'},selected['fixed'],selected['adaptive']];prompts=qs['validation'];reps=2
 warmups=[]
 for arm in arms:
  r=run(model,drafts.get(arm['draft']),warm_prefix,eos,arm['mode'],32,host_cost);warmups.append({'arm':arm['name'],**r})
 save(a.out/'warmups.json',warmups)
 order=[];rng=random.Random(20261105+a.block)
 for rep in range(reps):
  for p in range(len(prompts)):
   ids=list(range(len(arms)));rng.shuffle(ids);order += [{'rep':rep,'prompt':p,'arm_index':i} for i in ids]
 save(a.out/'manifest.json',{'target':tname,'target_revision':models[tname]['revision'],'draft_revisions':{n:models[n]['revision'] for n in dnames},'stage':a.stage,'block':a.block,'prompts':prompts,'arms':arms,'plan':order,'max_tokens':128,'vocabulary_hash':vocab_hash,'canonical_template_repo':dnames[0],'host_seconds_per_token':host_cost,'source_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [P/'runner.py',P/'adaptive_mlx.py',P/'policy.py']},'scope':'Same-Mac MLX prototype; weights resident, fresh KV; EOS respected; no remote or energy test'})
 with (a.out/'runs.jsonl').open('w') as f:
  for i,item in enumerate(order):
   arm=arms[item['arm_index']]
   try:r=run(model,drafts.get(arm['draft']),prefix(prompts[item['prompt']]['prompt']),eos,arm['mode'],128,host_cost);r['status']='completed'
   except Exception as e:
    r={'status':'failed','error':type(e).__name__+': '+str(e)};r.update(item,arm=arm['name']);f.write(json.dumps(r)+'\n');f.flush();raise
   r.update(item,arm=arm['name']);f.write(json.dumps(r,ensure_ascii=False)+'\n');f.flush();print(i+1,len(order),a.target,a.stage,a.block,arm['name'],round(r['seconds'],3),r['token_count'],r['draft_disabled'],flush=True)
 print('COMPLETE',flush=True)
if __name__=='__main__':main()
