from pathlib import Path
import json,tomli_w,urllib.request
from huggingface_hub import HfApi
R=Path.cwd();P=R/'research/heretic-mac-2026-11-04';A=R/'artifacts/heretic-mac-2026-11-04'
api=HfApi();revs={n:api.dataset_info(n).sha for n in ['mlabonne/harmless_alpaca','mlabonne/harmful_behaviors','UnstableLlama/praise']}
(P/'dataset-revisions.json').write_text(json.dumps(revs,indent=2)+'\n')
def ds(n,split):return {'dataset':n,'commit':revs[n],'split':split,'column':'text'}
for label in ['refusal','nosyco']:
 c={'model':'Qwen/Qwen3-4B-Instruct-2507','model_commit':'cdbee75f17c01a7cc42f958dc650907174af0554','dtypes':['float16'],'device_map':'mps','quantization':'none','batch_size':1,'max_batch_size':1,'max_response_length':32,'response_prefix':'','n_trials':4,'n_startup_trials':2,'seed':42,'study_checkpoint_dir':str(A/(label+'-checkpoints')),'trial_index':0,'model_action':'save','save_directory':str(A/(label+'-adapter')),'export_strategy':'adapter','system_prompt':'You are a helpful assistant.','scorer':{'KLDivergence':{'prompts':ds('mlabonne/harmless_alpaca','test[:8]')}},'modifier':{'ARA':{'good_prompts':ds('mlabonne/harmless_alpaca','train[:16]'),'lora_rank':8,'n_optimization_steps':1,'max_iter':5}}}
 if label=='refusal':
  c['scorer']['KeywordRate']={'prompts':ds('mlabonne/harmful_behaviors','test[:8]')}
  c['modifier']['ARA']['bad_prompts']=ds('mlabonne/harmful_behaviors','train[:16]')
 else:
  import tomllib
  with urllib.request.urlopen('https://raw.githubusercontent.com/p-e-w/heretic/v2.0.0/config.nosyco.toml') as h:upstream=tomllib.loads(h.read().decode())
  c['scorer']['KeywordRate']=upstream['scorer']['KeywordRate'];c['scorer']['KeywordRate']['prompts'].update(ds('UnstableLlama/praise','train[210:218]'))
  c['modifier']['ARA']['bad_prompts']=upstream['modifier']['ARA']['bad_prompts'];c['modifier']['ARA']['bad_prompts'].update(ds('UnstableLlama/praise','train[:16]'))
  c['modified_model_type']='sycophancy-reduced'
 (P/(label+'.toml')).write_text(tomli_w.dumps(c))
print('Pinned two headless local-only configurations; no uploads')
