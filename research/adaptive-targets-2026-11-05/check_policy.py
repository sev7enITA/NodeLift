"""Deterministic scheduling invariants, separate from model performance evidence."""
from policy import CostPolicy
import json
from pathlib import Path
checks=0
p=CostPolicy(.01)
for _ in range(3):p.observe({'k':p.choose(),'accepted':0,'emitted':1,'wall_seconds':.1});checks+=1
assert p.choose()==0 and p.disabled
for _ in range(20):p.observe({'k':0,'accepted':0,'emitted':1,'wall_seconds':.001});assert p.choose()==0;checks+=1
p=CostPolicy(.1)
for _ in range(30):
 k=p.choose();p.observe({'k':k,'accepted':k,'emitted':k+1,'wall_seconds':.01});assert 1<=p.choose()<=8;checks+=1
assert p.choose()==8 and not p.disabled
p=CostPolicy(.01);p.observe({'k':2,'accepted':0,'emitted':1,'wall_seconds':.1});p.observe({'k':1,'accepted':1,'emitted':2,'wall_seconds':.001});assert p.losses==0;checks+=1
for bad in [0,-1,float('nan'),float('inf')]:
 try:CostPolicy(bad)
 except ValueError:checks+=1
 else:raise AssertionError('Invalid calibration accepted')
Path(__file__).with_name('policy-checks.json').write_text(json.dumps({'passed':True,'checks':checks,'scope':'Pure scheduling bounds, permanent fallback and reset; not speed or numerical correctness'},indent=2)+'\n');print(checks,'policy checks passed')
