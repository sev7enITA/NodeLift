"""Teacher-forced verifier envelope. Free candidates are a diagnostic, never a deployable speedup."""
from pathlib import Path
import argparse,hashlib,json,time,random,os
import psutil
import mlx.core as mx
from mlx_lm import load
from mlx_lm.generate import generate_step
from mlx_lm.models.cache import make_prompt_cache
from transformers import AutoTokenizer

P=Path(__file__).resolve().parent;ROOT=P.parents[1]
MODELS=ROOT/'artifacts/adaptive-targets-2026-11-05/models.json'
def save(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def state():
 m=psutil.virtual_memory();s=psutil.swap_memory()
 return dict(unix=time.time(),available_bytes=m.available,swap_used_bytes=s.used,swap_in_bytes=s.sin,swap_out_bytes=s.sout,load_average=list(os.getloadavg()),mlx_active_bytes=mx.get_active_memory(),mlx_peak_bytes=mx.get_peak_memory())
def prefill(model,prefix,cache):
 seq=mx.array(prefix[:-1],mx.uint32)
 while seq.size:
  count=min(512,seq.size);model(seq[:count][None],cache=cache);mx.eval([c.state for c in cache]);seq=seq[count:];mx.clear_cache()
def predict(logits):
 logprobs=logits-mx.logsumexp(logits,axis=-1,keepdims=True)
 return mx.argmax(logprobs,axis=-1),mx.argmax(logits,axis=-1)
def reference(model,tok,prefix,budget):
 tokens=[];start=time.perf_counter();first=None;gen=generate_step(mx.array(prefix),model,max_tokens=budget,prefill_step_size=512)
 try:
  for t,_ in gen:
   tokens.append(int(t));first=first or time.perf_counter()
   if tokens[-1] in set(tok.eos_token_ids):break
   if time.perf_counter()-start>180:raise TimeoutError('reference deadline')
 finally:gen.close()
 mx.synchronize()
 return dict(tokens=tokens,finish='stop' if tokens[-1] in set(tok.eos_token_ids) else 'length',seconds=time.perf_counter()-start,ttft_seconds=first-start)
def replay(model,prefix,tokens,width):
 before=state();assert before['available_bytes']>1.5*2**30
 cache=make_prompt_cache(model);mx.synchronize();start=time.perf_counter();prefill(model,prefix,cache);prefilled=time.perf_counter()
 inp=[prefix[-1]]+tokens[:-1];pred=[];raw=[];blocks=[];first=None
 for pos in range(0,len(tokens),width):
  t=time.perf_counter();batch=mx.array(inp[pos:pos+width],mx.uint32)
  logits=model(batch[None],cache=cache)[0];ids,raw_ids=predict(logits);mx.eval(ids,raw_ids);now=time.perf_counter();first=first or now
  chosen=ids.tolist();raw_chosen=raw_ids.tolist();pred.extend(chosen);raw.extend(raw_chosen)
  blocks.append(dict(offset=pos,width=len(batch),seconds=now-t,matches=sum(a==b for a,b in zip(chosen,tokens[pos:pos+len(batch)]))))
  if now-start>180:raise TimeoutError('replay deadline')
 mx.synchronize();end=time.perf_counter()
 return dict(width=width,seconds=end-start,prefill_seconds=prefilled-start,decode_seconds=end-prefilled,ttft_seconds=first-start,
             predictions=pred,raw_argmax_predictions=raw,reference_tokens=tokens,exact=pred==tokens,matches=sum(a==b for a,b in zip(pred,tokens)),
             logprob_argmax_differs_from_raw=sum(a!=b for a,b in zip(pred,raw)),blocks=blocks,resources_before=before,resources_after=state(),
             scope='Teacher-forced replay, zero candidate producer and transport cost; not free generation')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--precision',choices=['native','fp32'],required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 models={x['repo']:x for x in json.loads(MODELS.read_text())};target=models['Qwen/Qwen3-14B-MLX-4bit'];draft=models['Qwen/Qwen3-0.6B-MLX-4bit']
 before=state();save(a.out/'admission.json',before)
 assert before['available_bytes']>9*2**30 and psutil.disk_usage(ROOT).free>12*2**30,'Resource admission failed'
 model,tok=load(target['path']);canon=AutoTokenizer.from_pretrained(draft['path'],local_files_only=True)
 if a.precision=='fp32':model.set_dtype(mx.float32);mx.eval(model.parameters())
 def prefix(text):
  s=canon.apply_chat_template([{'role':'system','content':'You are a helpful assistant.'},{'role':'user','content':text}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
  ids=tok.encode(s,add_special_tokens=False);assert ids==canon.encode(s,add_special_tokens=False);return ids
 warm=prefix('Explain what a cache is in two sentences.');warm_ref=reference(model,tok,warm,24)
 smoke=replay(model,warm,warm_ref['tokens'],1);save(a.out/'serial-alignment-smoke.json',smoke);assert smoke['exact'],'Replay width-one does not match upstream reference'
 prompts=json.loads((P/'prompts.json').read_text());refs=[]
 for q in prompts:
  ids=prefix(q['prompt']);r=reference(model,tok,ids,128);refs.append(dict(id=q['id'],prefix=ids,**r));print('reference',q['id'],len(r['tokens']),flush=True)
 save(a.out/'references.json',refs)
 order=[];rng=random.Random(20261105)
 for r in range(2):
  for i in range(len(refs)):
   widths=[1,2,4,8];rng.shuffle(widths);order.extend(dict(prompt=i,rep=r,width=w) for w in widths)
 save(a.out/'manifest.json',dict(target=target['repo'],revision=target['revision'],precision=a.precision,order=order,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),claim='diagnostic envelope only',concurrent_agent_browser_or_download_work=False))
 with (a.out/'runs.jsonl').open('w') as f:
  for i,task in enumerate(order):
   r=refs[task['prompt']]
   try:v=replay(model,r['prefix'],r['tokens'],task['width']);v.update(task,prompt_id=r['id'],status='completed')
   except Exception as e:
    f.write(json.dumps(dict(**task,status='failed',error=type(e).__name__+': '+str(e)))+'\n');f.flush();raise
   f.write(json.dumps(v)+'\n');f.flush();print(i+1,len(order),a.precision,r['id'],task['width'],round(v['seconds'],3),v['exact'],flush=True)
if __name__=='__main__':main()
