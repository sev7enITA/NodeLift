"""Fixed-position 2x2 cache-history/current-width diagnostic, not kernel causality proof."""
from pathlib import Path
import json,hashlib
import mlx.core as mx
import mlx.nn as nn
from mlx_lm import load
from mlx_lm.models.cache import make_prompt_cache
from envelope import prefill,save
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def summary(a,b):
 d=mx.abs(a.astype(mx.float32)-b.astype(mx.float32));mx.eval(d)
 return dict(max_abs=float(mx.max(d)),mean_abs=float(mx.mean(d)),changed=int(mx.sum(d!=0)),elements=d.size)
class Capture(nn.Module):
 def __init__(self,inner,name,sink):
  super().__init__();self.inner=inner;object.__setattr__(self,'capture_name',name);object.__setattr__(self,'capture_sink',sink)
 def __call__(self,*a,**kw):
  out=self.inner(*a,**kw);self.capture_sink[self.capture_name]=out[:,0];return out
def hooks(model,sink):
 restores=[]
 def wrap(parent,key,name):
  old=getattr(parent,key);setattr(parent,key,Capture(old,name,sink));restores.append(lambda p=parent,k=key,o=old:setattr(p,k,o))
 wrap(model.model,'embed_tokens','embedding')
 for i,layer in enumerate(model.layers):
  for k in ['input_layernorm','post_attention_layernorm']:wrap(layer,k,f'{i:02}.{k}')
  for k in ['q_proj','k_proj','v_proj','q_norm','k_norm','o_proj']:wrap(layer.self_attn,k,f'{i:02}.attention.{k}')
  wrap(layer,'self_attn',f'{i:02}.attention.output')
  for k in ['gate_proj','up_proj','down_proj']:wrap(layer.mlp,k,f'{i:02}.mlp.{k}')
  wrap(layer,'mlp',f'{i:02}.mlp.output')
  old=model.model.layers[i];model.model.layers[i]=Capture(old,f'{i:02}.layer.output',sink);restores.append(lambda j=i,o=old:model.model.layers.__setitem__(j,o))
 wrap(model.model,'norm','final_norm');wrap(model,'lm_head','logits')
 return restores
def main():
 out=ROOT/'artifacts/five-cases-2026-11-05/localization';out.mkdir(exist_ok=False)
 old=P.parent/'adaptive-targets-2026-11-05/results/raw/14B-screen'
 manifest=json.loads((old/'manifest.json').read_text());rows=[json.loads(x) for x in (old/'runs.jsonl').read_text().splitlines()]
 ref=next(r for r in rows if r['arm']=='host' and r['prompt']==0);tokens=ref['tokens'];pos=29
 models={r['repo']:r for r in json.loads((ROOT/'artifacts/adaptive-targets-2026-11-05/models.json').read_text())}
 model,tok=load(models['Qwen/Qwen3-14B-MLX-4bit']['path'])
 from transformers import AutoTokenizer
 dt=AutoTokenizer.from_pretrained(models['Qwen/Qwen3-0.6B-MLX-4bit']['path'],local_files_only=True)
 text=dt.apply_chat_template([dict(role='system',content='You are a helpful assistant.'),dict(role='user',content=manifest['prompts'][0]['prompt'])],tokenize=False,add_generation_prompt=True,enable_thinking=False)
 prefix=tok.encode(text,add_special_tokens=False);assert prefix==dt.encode(text,add_special_tokens=False)
 inp=[prefix[-1]]+tokens[:-1];results={};raw={};captured={};states={}
 for hw in [1,4]:
  for cw in [1,4]:
   key=f'history{hw}-current{cw}'
   for instrument in [False,True]:
    cache=make_prompt_cache(model);prefill(model,prefix,cache)
    for n in range(0,pos,hw):
     model(mx.array(inp[n:min(n+hw,pos)],mx.uint32)[None],cache=cache);mx.eval([c.state for c in cache])
    if not instrument:
     states[key]=[(mx.array(c.state[0][...,:c.offset,:]),mx.array(c.state[1][...,:c.offset,:])) for c in cache];mx.eval(states[key])
    sink={};restore=hooks(model,sink) if instrument else []
    try:
     logits=model(mx.array(inp[pos:pos+cw],mx.uint32)[None],cache=cache)[0,0];mx.eval(logits,*sink.values())
    finally:
     for f in reversed(restore):f()
    if instrument:
     captured[key]=sink;results[key]['instrumentation_delta']=summary(raw[key],logits)
    else:
     raw[key]=logits;ids=mx.argsort(logits)[-5:][::-1];mx.eval(ids)
     results[key]=dict(history_width=hw,current_width=cw,argmax=int(mx.argmax(logits)),normalized_argmax=int(mx.argmax(logits-mx.logsumexp(logits))),reference_token=tokens[pos],top_ids=ids.tolist(),top_logits=logits[ids].tolist(),cache_offsets=[c.offset for c in cache])
    print(key,'instrumented' if instrument else 'plain',int(mx.argmax(logits)),flush=True)
 base='history1-current1';comparisons={}
 for key in results:
  comparisons[key]=dict(logit_delta=summary(raw[base],raw[key]),components={name:summary(captured[base][name],v) for name,v in captured[key].items()},kv_history=[dict(layer=i,key=summary(a[0],b[0]),value=summary(a[1],b[1])) for i,(a,b) in enumerate(zip(states[base],states[key]))])
 save(out/'result.json',dict(position=pos,reference_source='../adaptive-targets-2026-11-05/results/raw/14B-screen',reference_tokens=tokens,prefix_tokens=prefix,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),results=results,comparisons=comparisons,scope='Native arithmetic. Identical teacher-forced prefix, frozen historical failing position. Intermediate collection can change fusion; instrumentation_delta must be checked. First divergence is localization, not kernel causality proof.'))
if __name__=='__main__':main()
