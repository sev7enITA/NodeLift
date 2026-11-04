"""Collect only this experiment's evidence and derive auditable descriptive totals."""
from pathlib import Path
import hashlib,json,shutil
P=Path(__file__).resolve().parent
A=P.parents[1]/'artifacts/heretic-mac-2026-11-04'
E=P/'results'; E.mkdir(exist_ok=True)
for arm in ['original','refusal','nosyco','original-followup','refusal-followup','nosyco-followup']:
 (E/arm).mkdir(exist_ok=True)
 for name in ['responses.json','summary.json','manifest.json']:
  shutil.copyfile(A/arm/name,E/arm/name)
shutil.copyfile(A/'original/teacher-sequences.json',E/'teacher-sequences.json')
for name in ['draft-original-agreement.json','draft-modified-agreement.json','tokenizer-compatibility.json','followup-status.json','lophius-probe.json','lophius-probe.log','refusal-native.log','refusal-native-status.json','mps-small-smoke.log','mps-small-smoke-retry.log']:
 if (A/name).exists():shutil.copyfile(A/name,E/name)
for arm in ['refusal','nosyco','draft']:
 for suffix in ['config-cwd.log','config-cwd-status.json']:
  shutil.copyfile(A/(arm+'-'+suffix),E/(arm+'-'+suffix))
artifacts=[]
for arm in ['refusal','nosyco','draft']:
 for f in sorted((A/(arm+'-adapter')).iterdir()):
  artifacts.append({'file':arm+'-adapter/'+f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(E/'adapter-manifest.json').write_text(json.dumps(artifacts,indent=2)+'\n')
v={'scope':'Small targeted single-run pilot, not a population benchmark or speedup measurement','technical':{},'draft':{}}
for arm in ['original','refusal','nosyco']:
 rows=json.loads((E/arm/'responses.json').read_text()); labelled=[r for r in rows if r['expected'] is not None]
 v['technical'][arm]={'n':len(labelled),'strict_correct':sum(r['strict_correct'] for r in labelled),'answer_letter_correct':sum(r['first_answer_letter']==r['expected'] for r in labelled),'incorrect_or_format_ids':[r['id'] for r in labelled if not r['strict_correct']]}
for arm in ['original','modified']:
 rows=json.loads((E/('draft-'+arm+'-agreement.json')).read_text())['rows']
 v['draft'][arm]={'teacher_forced_argmax_matches':sum(r['matches'] for r in rows),'candidate_positions':sum(r['positions'] for r in rows),'actual_k4_prefix_matches':sum(sum(r['actual_greedy_k4_matching_lengths']) for r in rows),'workloads':[{'id':r['id'],'prefix_matches':sum(r['actual_greedy_k4_matching_lengths']),'positions':r['positions']} for r in rows]}
v['calibration']={'refusal':{'keyword_baseline':8,'keyword_selected':1,'n':8,'selected_trial':1,'kl':0.8435},'nosyco':{'keyword_baseline':4,'keyword_selected':0,'n':8,'selected_trial':2,'kl':6.0427},'draft':{'first_token_kl_baseline':28.648560,'first_token_kl_selected':27.829408,'n':8,'selected_trial':3}}
(E/'aggregate.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps(v,indent=2))
