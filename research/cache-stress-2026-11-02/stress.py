"""Exercise cached authoritative-prefix transitions across two native builds."""
import hashlib,json,os,random,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'host'))
from nodelift.native import Native
model=Path(sys.argv[1]).resolve();gpu=int(sys.argv[2]);base=Path(sys.argv[3]).resolve();candidate=Path(sys.argv[4]).resolve();output=Path(sys.argv[5]);seed=20261102

def sha(path):
 with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def compare(x,y):return x['tokens']==y['tokens'] and x['eos']==y['eos']
engines={}
try:
 infos={}
 for name,lib in [('default',base),('deferred',candidate)]:
  os.environ['NODELIFT_LIBRARY']=str(lib);engine=Native();engines[name]=engine
  infos[name]=engine.call('load',path=str(model),n_ctx=1024,threads=8,gpu_layers=gpu)
 assert infos['default']['tokenizer_fingerprint']==infos['deferred']['tokenizer_fingerprint']
 prompts=['Explain briefly why networks can slow distributed inference.','Return integers from one to ten separated by commas.','Write a small Python function adding two numbers.','Rispondi in italiano: perché il cielo appare blu?']
 fill=engines['default'].call('tokenize',text=' ordinary words and numbers',chat=False)['tokens'];assert fill
 rng=random.Random(seed);rows=[];errors=[]
 for i in range(80):
  if i%20==0:
   p=engines['default'].call('tokenize',text=prompts[(i//20)%len(prompts)],chat=True)['tokens'];origin=p[:]
   for e in engines.values():e.call('reset')
  if i%13==5 and len(p)>len(origin)+2:p=p[:-rng.randint(1,min(4,len(p)-len(origin)))]
  if i%7==3:
   for e in engines.values():e.call('prefill',prefix=p)
  count=(1,2,4,8)[rng.randrange(4)];results={};failure=None
  for name,e in engines.items():
   try:results[name]=e.call('draft',prefix=p,count=count)
   except Exception as ex:failure={'engine':name,'message':str(ex)};break
  row={'iteration':i,'prefix_length':len(p),'requested':count,'error':failure}
  if failure:errors.append(row);rows.append(row);break
  row.update(matched=compare(results['default'],results['deferred']),default_count=len(results['default']['tokens']),candidate_count=len(results['deferred']['tokens']))
  if not row['matched']:
   row['prefix_sha256']=hashlib.sha256(json.dumps(p).encode()).hexdigest();row['default_token_sha256']=hashlib.sha256(json.dumps(results['default']['tokens']).encode()).hexdigest();row['candidate_token_sha256']=hashlib.sha256(json.dumps(results['deferred']['tokens']).encode()).hexdigest()
   after={}
   for name,e in engines.items():e.call('reset');after[name]=e.call('draft',prefix=p,count=count)
   row['matched_after_reset']=compare(after['default'],after['deferred'])
  rows.append(row)
  proposed=results['default']['tokens'];keep=rng.randrange(len(proposed)+1) if proposed else 0
  # Keep a prefix of the generated suggestions, then append an authoritative
  # correction/bonus; this is a controlled state transition, not target acceptance.
  p+=proposed[:keep]+[fill[rng.randrange(len(fill))]]
 result={'scope':'scripted cache transitions, not end-to-end inference','model_name':model.name,'model_sha256':sha(model),'default_sha256':sha(base),'candidate_sha256':sha(candidate),'gpu_layers_requested':gpu,'threads':8,'seed':seed,'planned':80,'executed':len(rows),'mismatches':sum(not r.get('matched',True) for r in rows),'errors':len(errors),'rows':rows}
 output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('planned','executed','mismatches','errors')}))
finally:
 for e in engines.values():e.close()
