"""Check evidence integrity, timing accounting, output counts and fallback invariants."""
from pathlib import Path
import hashlib,json,math
P=Path(__file__).resolve().parent
raw=P/'results/raw'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in json.loads((P/'input-hashes.json').read_text()).items():assert sha(P/name)==h
selection=json.loads((P/'selection-14B-fp32.json').read_text())
assert sha(raw/'14B-fp32-screen/runs.jsonl')==selection['screening_sha256']
requests=0;adaptive=0
for stage in ['14B-screen','14B-fp32-screen','14B-fp32-validation-0','14B-fp32-validation-1']:
 m=json.loads((raw/stage/'manifest.json').read_text())
 for name,h in m['source_hashes'].items():assert sha(P/name)==h,(stage,name)
 rows=[json.loads(x) for x in (raw/stage/'runs.jsonl').read_text().splitlines()]
 assert len(rows)==len(m['plan'])
 for row in rows:
  requests+=1
  assert row['status']=='completed' and row['token_count']==len(row['tokens'])
  assert 0<row['ttft_seconds']<=row['seconds'] and 0<row['token_count']<=128
  assert row['finish'] in ['stop','length']
  if row['trace']:
   adaptive+=1;t=row['trace']
   assert sum(x['emitted'] for x in t)==row['token_count']
   assert sum(x['accepted'] for x in t)==row['accepted_emitted_tokens']
   assert sum(x['draft_seconds']+x['verify_seconds'] for x in t)<=row['seconds']+1e-6
   zero_seen=False
   for x in t:
    assert 0<=x['k']<=8 and 0<=x['accepted']<=x['k'] and x['accepted']<=x['emitted']<=x['k']+1
    assert x['draft_seconds']>=0 and x['verify_seconds']>=0
    if zero_seen:assert x['k']==0,'Draft resumed with stale cache'
    if x['k']==0:zero_seen=True
 assert json.loads((raw/stage/'status.json').read_text())['exit_code']==0
smoke=json.loads((raw/'smoke-template-retry/smoke.json').read_text())
assert len(smoke['checks'])==12 and all(x['equal'] for x in smoke['checks'])
assert requests==150 and adaptive==44
result={'passed':True,'comparison_requests':requests,'instrumented_adaptive_requests':adaptive,'fixed_upstream_smoke_comparisons':12,'scope':'Integrity and accounting checks; no formal numerical proof or distributed validation'}
(P/'validation-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
