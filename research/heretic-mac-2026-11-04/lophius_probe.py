"""Actual Lophius introspection smoke test, distinct from llama.cpp diagnosis."""
from pathlib import Path
import json,torch,importlib.metadata
import lophius
A=Path('artifacts/heretic-mac-2026-11-04')
base=json.loads((A/'draft-model.json').read_text())['path']
m=lophius.load(base,model_kwargs={'device_map':'mps','dtype':torch.float16,'local_files_only':True,'trust_remote_code':False},tokenizer_kwargs={'local_files_only':True,'trust_remote_code':False})
o=m.generate('State what a mutex protects in one sentence.',return_logits=True,return_hidden_states=True,return_attentions=False,batch_size=1,generation_kwargs={'max_new_tokens':8,'do_sample':False},show_progress=False,top_logits=5)
g=o.generations[0]
v={'scope':'Lophius PyTorch/MPS introspection smoke test; not the llama.cpp numerical diagnostic','lophius':importlib.metadata.version('lophius'),'torch':torch.__version__,'model_device':str(m.model.device),'text':g.generated_text,'tokens':g.generated_token_ids}
for name in ['top_logits','top_token_ids','entropy','first_token_hidden_states']:
 t=getattr(g,name);v[name]={'shape':list(t.shape),'finite':bool(torch.isfinite(t).all())}
v['top_logits']['values']=g.top_logits.tolist();v['top_token_ids']['values']=g.top_token_ids.tolist();v['entropy']['values']=g.entropy.tolist()
(A/'lophius-probe.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
