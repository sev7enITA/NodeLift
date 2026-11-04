"""Audit evidence consistency. Does not claim production qualification."""
from pathlib import Path
import json,hashlib,ast,math
P=Path(__file__).resolve().parent;E=P/'results';checks=[]
for name,digest in json.loads((P/'input-hashes.json').read_text()).items():assert hashlib.sha256((P/name).read_bytes()).hexdigest()==digest
checks.append('Frozen primary plan and prompts unchanged')
for folder,expected in [(E,90),(E/'api-control',36)]:
 rows=[json.loads(s) for s in (folder/'runs.jsonl').read_text().splitlines()];manifest=json.loads((folder/'manifest.json').read_text());assert len(rows)==expected
 assert [{k:r[k] for k in ['rep','prompt','arm']} for r in rows]==manifest['plan']
 assert len({(r['rep'],r['prompt'],r['arm']) for r in rows})==expected
 for r in rows:assert 0<len(r['tokens'])<=64 and 0<r['ttft_seconds']<=r['seconds']
 source=P/('cached_probe.py' if folder==E else 'api_control.py');assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_sha256']
 checks.append(folder.name+': complete run plan, unique observations, source hash and timing ranges')
v=json.loads((E/'summary.json').read_text());rows=[json.loads(s) for s in (E/'runs.jsonl').read_text().splitlines()];base={(r['rep'],r['prompt']):r for r in rows if r['arm']=='target'}
for arm,summary in v['arms'].items():
 subset=[r for r in rows if r['arm']==arm];assert sum(r['tokens']==base[r['rep'],r['prompt']]['tokens'] for r in subset)==summary['exact_pairs']
 for r,pair in zip(subset,summary['pairs']):
  assert math.isclose(base[r['rep'],r['prompt']]['seconds']/r['seconds'],pair['speed_ratio'])
  if r['phases_seconds'] is not None:
   assert r['proposed']==sum(x['proposed'] for x in r['trace'])
   assert r['accepted']==sum(x['accepted'] for x in r['trace'])
   assert r['proposed']==r['accepted']+r['discarded']
   assert r['unattributed_seconds']>=0
checks.append('Primary token equality, paired ratios, candidate accounting and phase residuals')
f=json.loads((E/'format-probe.json').read_text())['rows']
for row in f:
 total=0
 for b in row['blocks']:
  n=0
  for a,c in zip(b['candidate_ids'],row['target_ids'][b['offset']:b['offset']+4]):
   if a!=c:break
   n+=1
  assert n==b['initial_matches'];total+=n
 assert total==row['matches'] and row['draft_prefix_ids'][:len(row['target_prefix_ids'])]==row['target_prefix_ids']
checks.append('Recomputed format-probe matches and unchanged target prefixes')
a=json.loads((E/'api-control/summary.json').read_text());ar=[json.loads(s) for s in (E/'api-control/runs.jsonl').read_text().splitlines()];ab={(r['rep'],r['prompt']):r for r in ar if r['arm']=='greedy'}
assert sum(r['tokens']==ab[r['rep'],r['prompt']]['tokens'] for r in ar if r['arm']=='assisted')==a['exact_pairs']
checks.append('Matched upstream API output equality independently counted')
d=json.loads((E/'diagnostic.json').read_text());i=d['first_difference_index'];assert d['reference_tokens'][:i]==d['replay_tokens'][:i] and d['reference_tokens'][i]!=d['replay_tokens'][i] and d['fresh_serial_argmax']==d['reference_tokens'][i] and d['context_ids_equal']
checks.append('Diagnostic first-difference and fresh serial argmax consistency')
for x in P.glob('*.py'):ast.parse(x.read_text())
for x in P.glob('*.md'):assert '\u2014' not in x.read_text()
for x in P.rglob('*.json'):json.loads(x.read_text())
checks.append('Python syntax, JSON parsing and authored prose punctuation')
(E/'validation.json').write_text(json.dumps({'passed':True,'checks':checks,'scope':'Artifact integrity and derived calculations only'},indent=2)+'\n');print('\n'.join(checks))
