"""Actual candidate generation; fixed teacher output, draft-only template change."""
from pathlib import Path
import json,time,hashlib
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer
P=Path(__file__).resolve().parent;R=P.parents[1];A=R/'artifacts/heretic-mac-2026-11-04';O=R/'artifacts/draft-format-2026-11-04';O.mkdir(exist_ok=True)
assert not (O/'format-probe.json').exists()
torch.manual_seed(42);torch.set_num_threads(8)
path=json.loads((A/'draft-model.json').read_text())['path'];tok=AutoTokenizer.from_pretrained(path,local_files_only=True)
m=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,dtype=torch.float16,device_map='mps',attn_implementation='sdpa').eval()
rows=[]
with torch.inference_mode():
 for row in json.loads((A/'original/teacher-sequences.json').read_text()):
  if row['split']!='heldout':continue
  messages=[{'role':'system','content':'You are a helpful assistant.'},{'role':'user','content':row['prompt']}]
  aligned=tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False)
  if not isinstance(aligned,list):aligned=aligned['input_ids']
  assert aligned[:len(row['input_ids'])]==row['input_ids'],'Expected exact target prefix plus draft-only suffix'
  for mode,prefix in [('raw',row['input_ids']),('aligned',aligned)]:
   blocks=[]
   for start in range(0,len(row['target_ids']),4):
    inp=torch.tensor([prefix+row['target_ids'][:start]],device='mps');torch.mps.synchronize();t=time.perf_counter()
    y=m.generate(input_ids=inp,attention_mask=torch.ones_like(inp),max_new_tokens=4,do_sample=False,pad_token_id=tok.eos_token_id)
    torch.mps.synchronize();dt=time.perf_counter()-t;ids=y[0,inp.shape[1]:].tolist();n=0
    for x,z in zip(ids,row['target_ids'][start:start+4]):
     if x!=z:break
     n+=1
    blocks.append({'offset':start,'candidate_ids':ids,'initial_matches':n,'seconds_including_prefill':dt})
   r={'id':row['id'],'mode':mode,'target_prefix_ids':row['input_ids'],'draft_prefix_ids':prefix,'target_ids':row['target_ids'],'matches':sum(b['initial_matches'] for b in blocks),'blocks':blocks}
   rows.append(r);(O/'format-probe.json').write_text(json.dumps({'scope':'Fixed previous diagnostic continuations, no live verifier or latency gain claim','rows':rows},indent=2)+'\n');print(row['id'],mode,r['matches'],flush=True)
print('COMPLETE',flush=True)
