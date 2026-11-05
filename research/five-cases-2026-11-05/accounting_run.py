"""Accounting equivalence and charged-policy diagnostics. No production scheduler changes."""
from pathlib import Path
import sys,json,time,statistics,random,hashlib
import mlx.core as mx
from mlx_lm import load
from mlx_lm.generate import generate_step
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
sys.path.append(str(P.parent/'adaptive-targets-2026-11-05'))
from adaptive_mlx import adaptive_generate_step
from policy import CostPolicy
from accounted_mlx import accounted_generate_step
from envelope import save,state
class ChargedPolicy(CostPolicy):
 version='startup-and-rewind-charged-diagnostic-v2'
 def observe(self,row):
  super().observe(dict(row,wall_seconds=row['controller_charge_seconds']))
def run(model,draft,prefix,eos,arm,cap,host=.05):
 trace=[];tel={};policy=ChargedPolicy(host) if arm=='charged' else CostPolicy(host) if arm=='old-adaptive' else None
 mx.synchronize();start=time.perf_counter();first=None;tokens=[];accepted=0
 kw=dict(max_tokens=cap,prefill_step_size=512)
 if arm=='host':gen=generate_step(mx.array(prefix),model,**kw)
 elif arm.startswith('old'):gen=adaptive_generate_step(mx.array(prefix),model,draft,trace=trace,policy=policy,num_draft_tokens=2,**kw)
 else:gen=accounted_generate_step(mx.array(prefix),model,draft,trace=trace,telemetry=tel,policy=policy,num_draft_tokens=2,**kw)
 try:
  for item in gen:
   now=time.perf_counter();first=first or now;tokens.append(int(item[0]));accepted+=int(item[2]) if len(item)>2 else 0
   if now-start>180:raise TimeoutError('request deadline')
   if tokens[-1] in eos:break
 finally:gen.close()
 mx.synchronize();end=time.perf_counter()
 phases={k:sum(r.get(k,0) for r in trace) for k in ['draft_seconds','verify_seconds','rewind_seconds']}
 measured=sum(phases.values())+sum(tel.values())
 return dict(arm=arm,tokens=tokens,finish='stop' if tokens[-1] in eos else 'length',seconds=end-start,ttft_seconds=first-start,telemetry=tel,phases=phases,unattributed_seconds=end-start-measured if tel else None,trace=trace,accepted=accepted,disabled=policy.disabled if policy else None,decisions=policy.decisions if policy else [],resources_after=state())
def main():
 out=ROOT/'artifacts/five-cases-2026-11-05/accounting';out.mkdir(exist_ok=False)
 models={v['repo']:v for v in json.loads((ROOT/'artifacts/adaptive-targets-2026-11-05/models.json').read_text())}
 model,tok=load(models['Qwen/Qwen3-14B-MLX-4bit']['path']);draft,dtok=load(models['Qwen/Qwen3-0.6B-MLX-4bit']['path'])
 for m in (model,draft):m.set_dtype(mx.float32);mx.eval(m.parameters())
 def prefix(s):
  text=dtok.apply_chat_template([dict(role='system',content='You are a helpful assistant.'),dict(role='user',content=s)],tokenize=False,add_generation_prompt=True,enable_thinking=False)
  a=tok.encode(text,add_special_tokens=False);assert a==dtok.encode(text,add_special_tokens=False);return a
 eos=set(tok.eos_token_ids);warm=prefix('Explain what a cache is in two sentences.')
 cal=[run(model,draft,warm,eos,'host',32) for _ in range(3)];host=statistics.median((r['seconds']-r['ttft_seconds'])/(len(r['tokens'])-1) for r in cal[1:]);save(out/'calibration.json',dict(host_seconds_per_token=host,runs=cal))
 smoke=[]
 for cap in [1,5,17]:
  old=run(model,draft,warm,eos,'old-fixed',cap);new=run(model,draft,warm,eos,'accounted-fixed',cap)
  smoke.append(dict(cap=cap,old=old,new=new,exact=old['tokens']==new['tokens'] and old['finish']==new['finish']));save(out/'smoke.json',smoke);assert smoke[-1]['exact'],'Accounting instrumentation altered output'
 prompts=json.loads((P/'prompts.json').read_text());order=[];rng=random.Random(20261105)
 for rep in range(2):
  for q in prompts:
   arms=['host','old-adaptive','charged'];rng.shuffle(arms);order.extend(dict(rep=rep,prompt=q,arm=a) for a in arms)
 save(out/'manifest.json',dict(precision='fp32-floating-parameters-packed-integers-preserved',order=order,cap=128,host_cost=host,scope='Same Mac, diagnostic only',source_hashes={f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['accounted_mlx.py','accounting_run.py']}))
 with (out/'runs.jsonl').open('w') as f:
  for n,item in enumerate(order):
   r=run(model,draft,prefix(item['prompt']['prompt']),eos,item['arm'],128,host);r.update(rep=item['rep'],prompt_id=item['prompt']['id']);f.write(json.dumps(r)+'\n');f.flush();print(n+1,len(order),r['prompt_id'],r['arm'],round(r['seconds'],3),flush=True)
if __name__=='__main__':main()
