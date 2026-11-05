"""Per-request bounded scheduling from measured cost; never a correctness gate."""
import math
class CostPolicy:
 version='cost-bounded-mlx-v1'
 def __init__(self,host_seconds_per_token):
  if not math.isfinite(host_seconds_per_token) or host_seconds_per_token<=0:raise ValueError('Invalid serial calibration')
  self.host=host_seconds_per_token;self.k=2;self.losses=0;self.disabled=False;self.decisions=[]
 def choose(self):return 0 if self.disabled else self.k
 def observe(self,row):
  if row['k']==0:return
  elapsed=row['wall_seconds'];emitted=row['emitted']
  if emitted<1 or not math.isfinite(elapsed) or elapsed<=0:raise ValueError('Invalid block observation')
  margin=self.host*emitted/elapsed
  self.losses=self.losses+1 if margin<1.1 else 0
  if self.losses>=3:self.disabled=True
  elif row['accepted']/row['k']>=.75 and margin>=1.1:self.k=min(8,self.k+1)
  elif row['accepted']/row['k']<.5 or margin<1:self.k=max(1,self.k-1)
  self.decisions.append({'observed_k':row['k'],'cost_ratio':margin,'consecutive_losses':self.losses,'next_k':self.choose()})
