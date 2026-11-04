"""Teacher-forced agreement diagnostic on held-out prefixes, not a speed benchmark."""
import json,argparse,hashlib,time
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
p=argparse.ArgumentParser();p.add_argument('--adapter');p.add_argument('--out',required=True);a=p.parse_args()
A=Path('artifacts/heretic-mac-2026-11-04');modelpath=json.loads((A/'draft-model.json').read_text())['path'];tok=AutoTokenizer.from_pretrained(modelpath,local_files_only=True)
assert hashlib.sha256(json.dumps(tok.get_vocab(),sort_keys=True).encode()).hexdigest()==json.loads((A/'original/manifest.json').read_text())['vocab_hash']
m=AutoModelForCausalLM.from_pretrained(modelpath,local_files_only=True,dtype=torch.float16,device_map='mps',attn_implementation='sdpa').eval()
if a.adapter:
 from peft import PeftModel
 m=PeftModel.from_pretrained(m,a.adapter,is_trainable=False).eval()
rows=[]
with torch.inference_mode():
 for r in json.loads((A/'original/teacher-sequences.json').read_text()):
  if r['split']!='heldout':continue
  prefix=r['input_ids'];target=r['target_ids'];x=torch.tensor([prefix+target],device='mps');z=m(input_ids=x,attention_mask=torch.ones_like(x),use_cache=False).logits[0,len(prefix)-1:len(prefix)-1+len(target)].float()
  if not torch.isfinite(z).all():raise ValueError('Nonfinite logits')
  pred=z.argmax(-1).tolist();matches=[x==y for x,y in zip(pred,target)];accept=[]
  for start in range(0,len(matches),4):
   count=0
   for good in matches[start:start+4]:
    if not good:break
    count+=1
   accept.append(count)
  actual_accept=[];actual_candidates=[]
  for start in range(0,len(target),4):
   inp=torch.tensor([prefix+target[:start]],device='mps');budget=min(4,len(target)-start)
   y=m.generate(input_ids=inp,attention_mask=torch.ones_like(inp),max_new_tokens=budget,do_sample=False,pad_token_id=tok.eos_token_id)
   ids=y[0,inp.shape[1]:].tolist();count=0
   for left,right in zip(ids,target[start:start+budget]):
    if left!=right:break
    count+=1
   actual_accept.append(count);actual_candidates.append(ids)
  rows.append({'actual_greedy_k4_matching_lengths':actual_accept,'actual_greedy_k4_candidate_ids':actual_candidates,'id':r['id'],'positions':len(target),'matches':sum(matches),'k4_initial_matching_lengths':accept,'predicted_ids':pred,'target_ids':target})
  print(r['id'],sum(matches),'/',len(target),flush=True)
Path(a.out).write_text(json.dumps({'scope':'Teacher-forced logits and actual greedy k4 candidates against frozen teacher continuations. No live verifier, transport or speculative speedup measurement.','adapter':bool(a.adapter),'rows':rows},indent=2)+'\n')
