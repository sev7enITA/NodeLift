"""Synthetic verifier control checks, not model or performance evidence."""
import importlib.util,json,time
from pathlib import Path
import torch
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('probe',P/'cached_probe.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Model:
 def __init__(self,kind,stop):self.kind=kind;self.stop=stop
 def value(self,prefix):
  if len(prefix)>=self.stop:return 0
  value=(sum((i+1)*x for i,x in enumerate(prefix))+len(prefix)*3)%19+1
  if self.kind=='wrong' or (self.kind=='mixed' and len(prefix)%3==0):value=value%19+1
  return value
class FakeState:
 def __init__(self,model,ids,metrics,phase):self.model=model;self.ids=list(ids);self.metrics=metrics;self.last=self.logits()
 def logits(self):
  z=torch.zeros(20);z[self.model.value(self.ids)]=1;return z
 def next(self):return self.model.value(self.ids)
 def feed(self,ids,phase,all_logits=False):
  rows=[]
  for token in ids:self.ids.append(token);rows.append(self.logits())
  self.last=rows[-1];return torch.stack(rows)
 def crop(self,n):self.ids=self.ids[:n];self.last=self.logits()
 def reconcile(self,desired,phase):self.ids=list(desired);self.last=self.logits()
m.State=FakeState
sync=torch.mps.synchronize;torch.mps.synchronize=lambda:None
checks=0
try:
 for stop in [4,6,10,30]:
  for budget in [1,2,4,5,9,12]:
   target=Model('exact',stop);prefix=[2,3,4];expected=[]
   while len(expected)<budget:
    token=target.value(prefix+expected);expected.append(token)
    if token==0:break
   for kind in ['exact','wrong','mixed']:
    for arm in ['target','raw_batch','aligned_batch','aligned_serial']:
     r=m.custom(target,Model(kind,stop),prefix,prefix,arm,budget,[0])
     assert r['tokens']==expected,(stop,budget,kind,arm,r['tokens'],expected)
     assert r['accepted']+r['discarded']==r['proposed']
     assert all(0<=x['accepted']<=x['proposed'] and 1<=x['committed']<=x['proposed']+1 for x in r['trace'])
     checks+=1
finally:torch.mps.synchronize=sync
v={'checks':checks,'passed':True,'scope':'Synthetic exact, wrong and mixed candidates; EOS and output limits. Fake state does not validate GPU kernels or real KV cache.'}
print(json.dumps(v,indent=2))
(P/'protocol-checks.json').write_text(json.dumps(v,indent=2)+'\n')
