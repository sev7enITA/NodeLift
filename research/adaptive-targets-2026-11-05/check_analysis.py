"""Negative controls for acceleration claims; no hardware inference is performed."""
import copy, json
from pathlib import Path
from analyse import aggregate

def fixture():
    return [dict(arm='candidate',prompt=f'p{p}',block=b,rep=r,exact=True,
                 speed_ratio=1.2, saved_seconds=.2, ttft_change_seconds=.01,
                 draft_disabled=False,candidate_swap_growth_bytes=0)
            for b in range(2) for p in range(8) for r in range(2)]

checks=[]
x=fixture();assert aggregate(x)[0]['qualified'];checks.append('A fully exact, consistently faster synthetic candidate passes')
x=fixture();x[0]['exact']=False;assert not aggregate(x)[0]['qualified'];checks.append('One mismatch disqualifies despite speed')
x=fixture();x=[r for r in x if r['block']==0];assert not aggregate(x)[0]['qualified'];checks.append('One process is insufficient')
x=fixture()
for r in x:
    if r['block']==1:r['speed_ratio']=1.04
assert not aggregate(x)[0]['qualified'];checks.append('A subthreshold process prevents promotion')
x=fixture()
for r in x:r['speed_ratio']=.9 if int(r['prompt'][1:])<4 else 1.5
result=aggregate(x)[0];assert not result['qualified'];assert len(result['regressing_workloads'])==4
checks.append('Workload uncertainty prevents promotion despite favorable median')
out={'checks':checks,'passed':len(checks),'scope':'Synthetic negative controls, not inference or performance evidence'}
Path(__file__).with_name('analysis-checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(out)
