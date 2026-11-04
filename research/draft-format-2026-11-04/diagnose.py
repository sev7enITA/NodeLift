"""One instrumented replay and fresh serial-history comparison. Not timed evidence."""
from pathlib import Path
import importlib.util,json,gc
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
P=Path(__file__).resolve().parent;R=P.parents[1];A=R/'artifacts';O=A/'draft-format-2026-11-04'
spec=importlib.util.spec_from_file_location('probe',P/'cached_probe.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rows=[json.loads(s) for s in (O/'main/runs.jsonl').read_text().splitlines()];base={(r['rep'],r['prompt']):r for r in rows if r['arm']=='target'}
bad=next((r for r in rows if r['arm']=='aligned_batch' and r['tokens']!=base[r['rep'],r['prompt']]['tokens']),None)
if bad is None:
 m.save(O/'diagnostic.json',{'scope':'No mismatching aligned-batch pair in this run; no diagnostic replay performed'});raise SystemExit(0)
torch.set_num_threads(8);torch.manual_seed(42)
T=(A/'heretic-mac-2026-11-04/base-model-path.txt').read_text().strip();D=json.loads((A/'heretic-mac-2026-11-04/draft-model.json').read_text())['path']
tt=AutoTokenizer.from_pretrained(T,local_files_only=True);dt=AutoTokenizer.from_pretrained(D,local_files_only=True)
models=[AutoModelForCausalLM.from_pretrained(p,local_files_only=True,dtype=torch.float16,device_map='mps',attn_implementation='sdpa').eval() for p in [T,D]];target,draft=models
prompt=json.loads((P/'prompts.json').read_text())[bad['prompt']]['prompt'];messages=[{'role':'system','content':'You are a helpful assistant.'},{'role':'user','content':prompt}]
def encode(tok):
 x=tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False);return x if isinstance(x,list) else x['input_ids']
tp,dp=encode(tt),encode(dt);events=[];original=m.State
class Capture(original):
 def feed(self,ids,phase,all_logits=False):
  z=super().feed(ids,phase,all_logits)
  if self.model is target:
   values=z.detach().float().cpu()
   for i in range(len(values)):
    context=self.ids[:len(self.ids)-len(values)+i+1];events.append({'context':context,'phase':phase,'logits':values[i].clone()})
  return z
m.State=Capture
with torch.inference_mode():
 eos=target.generation_config.eos_token_id; eos=[eos] if isinstance(eos,int) else eos
 result=m.custom(target,draft,tp,dp,'aligned_batch',64,eos);reference=base[bad['rep'],bad['prompt']]['tokens']
 index=next((i for i,(a,b) in enumerate(zip(result['tokens'],reference)) if a!=b),None)
 report={'scope':'Instrumented replay; one prompt, not a performance measurement or kernel attribution','prompt_id':bad['prompt'],'replay_matches_recorded_batch':result['tokens']==bad['tokens'],'replay_tokens':result['tokens'],'reference_tokens':reference,'first_difference_index':index}
 if index is not None:
  wanted=tp+result['tokens'][:index];events_at=[e for e in events if e['context']==wanted and int(e['logits'].argmax())==result['tokens'][index]]
  assert events_at,'No target logit record supports emitted first differing token'
  chosen=events_at[-1];z=chosen['logits'];m.State=original;s=original(target,tp,{},'prefill')
  for token in result['tokens'][:index]:s.feed([token],'serial')
  fresh=s.last.detach().float().cpu();assert s.ids==wanted
  expected=reference[index];observed=result['tokens'][index]
  report.update(context_ids_equal=True,context_matches_original_reference=reference[:index]==result['tokens'][:index],phase=chosen['phase'],batch_argmax=observed,fresh_serial_argmax=int(fresh.argmax()),reference_token=expected,max_abs_logit_delta=float((z-fresh).abs().max()),reference_minus_batch_choice_logit_batch=float(z[expected]-z[observed]),reference_minus_batch_choice_logit_fresh_serial=float(fresh[expected]-fresh[observed]),context_tokens=len(wanted))
 m.save(O/'diagnostic.json',report);print(json.dumps({k:v for k,v in report.items() if not k.endswith('_tokens')},indent=2))
