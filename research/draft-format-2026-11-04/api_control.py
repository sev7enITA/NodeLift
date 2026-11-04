"""Fair upstream greedy/assisted API comparison; fresh KV and identical streamer."""
import importlib.util,json,time,random,hashlib
from pathlib import Path
import torch,psutil
from transformers import AutoTokenizer,AutoModelForCausalLM
P=Path(__file__).resolve().parent;R=P.parents[1];A=R/'artifacts';O=A/'draft-format-2026-11-04/api-control';O.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('probe',P/'cached_probe.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
torch.manual_seed(42);torch.set_num_threads(8)
T=(A/'heretic-mac-2026-11-04/base-model-path.txt').read_text().strip();D=json.loads((A/'heretic-mac-2026-11-04/draft-model.json').read_text())['path'];tok=AutoTokenizer.from_pretrained(T,local_files_only=True)
target,draft=[AutoModelForCausalLM.from_pretrained(p,local_files_only=True,dtype=torch.float16,device_map='mps',attn_implementation='sdpa').eval() for p in [T,D]]
def tokens(prompt):
 v=tok.apply_chat_template([{'role':'system','content':'You are a helpful assistant.'},{'role':'user','content':prompt}],tokenize=True,add_generation_prompt=True,enable_thinking=False);return v if isinstance(v,list) else v['input_ids']
qs=json.loads((P/'prompts.json').read_text());plan=[];rng=random.Random(20261105)
for rep in range(3):
 for i in range(6):
  arms=['greedy','assisted'];rng.shuffle(arms);plan += [{'rep':rep,'prompt':i,'arm':arm} for arm in arms]
m.save(O/'manifest.json',{'plan':plan,'prompts':qs,'budget':64,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'helper_sha256':hashlib.sha256((P/'cached_probe.py').read_bytes()).hexdigest(),'scope':'Post-hoc matched upstream API timing control; local MPS, both models resident, no network or energy'})
with torch.inference_mode():
 warm=[{'arm':arm,**m.upstream(target,draft,tokens('Explain a mutex in one sentence.'),64,arm=='assisted')} for arm in ['greedy','assisted']];m.save(O/'warmup.json',warm)
 with (O/'runs.jsonl').open('w') as f:
  for i,item in enumerate(plan):
   assert psutil.virtual_memory().available>2*1024**3
   r=m.upstream(target,draft,tokens(qs[item['prompt']]['prompt']),64,item['arm']=='assisted');r.update(item);f.write(json.dumps(r)+'\n');f.flush();print(i+1,len(plan),item,round(r['seconds'],3),flush=True)
print('COMPLETE',flush=True)
