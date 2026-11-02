"""Generate fixed, non-private target token windows for the shape probe."""
import hashlib,json,os,platform,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'host'))
from nodelift.native import Native,library_path
model=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]);gpu=int(sys.argv[3]);threads=8
def digest(path):
 with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
prompts=[('italian_sky','Rispondi con una frase: perché il cielo appare blu?'),('brief_greeting','Say hello briefly.'),('python_add','Write a Python function adding two numbers.'),('network','Explain why low-latency networks matter for distributed inference.')]
cases=[]
with Native() as n:
 info=n.call('load',path=str(model),n_ctx=512,threads=threads,gpu_layers=gpu)
 for name,text in prompts:
  prompt=n.call('tokenize',text=text,chat=True)['tokens'];n.call('reset');generated=n.call('draft',prefix=prompt,count=64)['tokens']
  offsets=(0,8,16,20,22,23,24,32) if name=='italian_sky' else (0,8,16)
  widths=(1,4,8) if name=='italian_sky' else (1,4)
  windows=[{'offset':t,'width':w} for t in offsets for w in widths if t+w-1<=len(generated)]
  cases.append({'name':name,'prompt_tokens':prompt,'generated_tokens':generated,'windows':windows})
result={'schema':1,'model':model.name,'model_sha256':digest(model),'generation_library_sha256':digest(library_path()),'generation_gpu_layers_requested':gpu,'threads':threads,'runtime':info['runtime'],'tokenizer_fingerprint':info['tokenizer_fingerprint'],'platform':platform.platform(),'cases':cases}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'cases':len(cases),'windows':sum(len(c['windows']) for c in cases),'file':str(out)}))
