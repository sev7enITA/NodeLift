"""Validate persisted experimental artifacts without loading model weights."""
import hashlib,json,math
from pathlib import Path
base=Path(__file__).resolve().parent;root=base.parents[1];checks=0
for name in ('results','repeat','adaptive','upstream'):
 folder=base/name;index=json.loads((folder/'hashes.json').read_text())
 for filename,expected in index.items():
  actual=hashlib.sha256((folder/filename).read_bytes()).hexdigest();assert actual==expected,(name,filename);checks+=1
summary=json.loads((base/'paired-summary.json').read_text())
for session in summary['sessions']:
 assert session['planned_runs']==session['observed_runs']==session['completed_runs']==60
 for c in session['conditions']:
  assert c['planned_pairs']==c['candidate_runs']==c['completed_pairs']==12
  assert 0<=c['exact_tokens_and_finish_pairs']<=12 and math.isfinite(c['median_paired_speedup'])
  checks+=1
adaptive=json.loads((base/'adaptive-summary.json').read_text());assert adaptive['planned_runs']==adaptive['observed_runs']==adaptive['completed_runs']==36
upstream=json.loads((base/'upstream-summary.json').read_text());assert upstream['planned_runs']==upstream['observed_runs']==upstream['completed_runs']==36
checks+=2
shape=root/'research/batch-numerics-2026-11-02';shape_summary=json.loads((shape/'summary.json').read_text())
for run in shape_summary['runs']:
 path=shape/run['raw_file'];raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==run['raw_sha256'];data=json.loads(raw)
 assert len(data['windows'])==run['counts']['windows'];assert sum(len(w['positions']) for w in data['windows'])==run['counts']['positions']
 for w in data['windows']:
  assert len(w['positions'])==w['width']
  for pos in w['positions']:
   assert pos['top1_flipped']==(pos['serial_top1']!=pos['batch_top1'])
   assert pos['control_top1_flipped']==(pos['serial_top1']!=pos['control_top1'])
   assert math.isfinite(pos['max_abs_serial_batch']) and pos['max_abs_serial_batch']>=0
 checks+=1
cache=root/'research/cache-stress-2026-11-02'
for name in ('metal-0.5b.json','cpu-0.5b.json','metal-1.5b.json','cpu-1.5b.json'):
 d=json.loads((cache/name).read_text());assert d['planned']==d['executed']==len(d['rows'])==80;assert d['mismatches']==sum(not x.get('matched',True) for x in d['rows']);checks+=1
assert json.loads((base/'tokenizer-preflight.json').read_text())['same'] is True
print(checks,'artifact checks passed')
