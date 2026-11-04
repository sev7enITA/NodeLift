"""Verify retained observations against derived counts; no model calls."""
from pathlib import Path
import ast,json,hashlib,tomllib
P=Path(__file__).resolve().parent;E=P/'results';v=json.loads((E/'aggregate.json').read_text())
checks=[]
key={c['id']:c['answer'] for c in json.loads((P/'evaluation.json').read_text())}
for arm in ['original','refusal','nosyco']:
 rows=json.loads((E/arm/'responses.json').read_text());assert len(rows)==20
 labelled=[r for r in rows if key[r['id']] is not None]
 assert len(labelled)==16 and len({r['id'] for r in rows})==20
 for r in labelled:assert r['expected']==key[r['id']] and r['strict_correct']==(r['text']==r['expected'])
 assert sum(r['strict_correct'] for r in labelled)==v['technical'][arm]['strict_correct']
 assert sum(r['text'][:1]==r['expected'] for r in labelled)==v['technical'][arm]['answer_letter_correct']
 follow=json.loads((E/(arm+'-followup')/'responses.json').read_text());assert len(follow)==4 and all(not r['hit_token_limit'] for r in follow)
 checks.append(arm+': answer-key, derived scores, complete follow-up')
original=json.loads((E/'draft-original-agreement.json').read_text())['rows']
modified=json.loads((E/'draft-modified-agreement.json').read_text())['rows']
for before,after in zip(original,modified):assert before['id']==after['id'] and before['target_ids']==after['target_ids']
for arm,rows in [('original',original),('modified',modified)]:
 counts=[]
 for row in rows:
  assert row['matches']==sum(a==b for a,b in zip(row['predicted_ids'],row['target_ids']))
  lengths=[]
  for i,block in enumerate(row['actual_greedy_k4_candidate_ids']):
   n=0
   for a,b in zip(block,row['target_ids'][i*4:i*4+4]):
    if a!=b:break
    n+=1
   lengths.append(n)
  assert lengths==row['actual_greedy_k4_matching_lengths'];counts+=lengths
 assert sum(counts)==v['draft'][arm]['actual_k4_prefix_matches'] and len(counts)==32
checks.append('draft: identical target continuations and recomputed greedy prefix matches')
for arm in ['refusal','nosyco','draft']:
 s=json.loads((E/(arm+'-config-cwd-status.json')).read_text());assert s['exit_code']==0 and s['adapter_exported']
probe=json.loads((E/'lophius-probe.json').read_text());assert probe['model_device']=='mps:0' and all(probe[k]['finite'] for k in ['top_logits','top_token_ids','entropy','first_token_hidden_states'])
checks.append('three exported stages and finite MPS introspection')
for f in P.glob('*.py'):ast.parse(f.read_text())
for f in P.rglob('*.json'):json.loads(f.read_text())
for f in P.glob('*.toml'):tomllib.loads(f.read_text())
for f in P.glob('*.md'):assert '\u2014' not in f.read_text(),f.name
checks.append('Python AST, JSON, TOML, authored Markdown punctuation')
for name,digest in json.loads((P/'input-hashes.json').read_text()).items():
 # The input file contains frozen filenames and SHA256 strings.
 assert hashlib.sha256((P/name).read_bytes()).hexdigest()==digest,name
checks.append('predeclared input hashes unchanged')
(E/'validation.json').write_text(json.dumps({'passed':True,'checks':checks,'scope':'artifact consistency, not model capability or production correctness'},indent=2)+'\n')
print('\n'.join(checks))
