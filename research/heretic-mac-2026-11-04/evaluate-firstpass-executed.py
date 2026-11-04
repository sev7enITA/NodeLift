"""Frozen local model evaluation. Never executes generated code or changes NodeLift."""
import argparse,json,time,hashlib,os
from pathlib import Path
import torch,psutil
from transformers import AutoModelForCausalLM,AutoTokenizer
from transformers.generation.streamers import BaseStreamer
P=Path(__file__).resolve().parent
class Clock(BaseStreamer):
 def __init__(self):self.start=time.perf_counter();self.first=None;self.prompt=True
 def put(self,value):
  if self.prompt:self.prompt=False
  elif self.first is None:self.first=time.perf_counter()
 def end(self):pass

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--model',required=True);ap.add_argument('--adapter');ap.add_argument('--label',required=True);ap.add_argument('--out',required=True);ap.add_argument('--teacher',action='store_true');a=ap.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
 torch.manual_seed(42);torch.set_num_threads(8)
 tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True,trust_remote_code=False)
 if tok.pad_token_id is None:tok.pad_token=tok.eos_token
 model=AutoModelForCausalLM.from_pretrained(a.model,local_files_only=True,trust_remote_code=False,dtype=torch.float16,device_map='mps',attn_implementation='sdpa').eval()
 if a.adapter:
  from peft import PeftModel
  model=PeftModel.from_pretrained(model,a.adapter,is_trainable=False).eval()
 vocab=tok.get_vocab();fingerprint=hashlib.sha256(json.dumps(vocab,sort_keys=True).encode()).hexdigest()
 manifest={'label':a.label,'adapter':bool(a.adapter),'torch':torch.__version__,'device':str(model.device),'dtype':str(model.dtype),'vocab_hash':fingerprint,'time_scope':'single-run diagnostic; includes streamer overhead; no comparative speed qualification','started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 def inputs(prompt):
  s=tok.apply_chat_template([{'role':'system','content':'You are a helpful assistant.'},{'role':'user','content':prompt}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
  return tok(s,return_tensors='pt',return_token_type_ids=False).to('mps')
 rows=[]
 with torch.inference_mode():
  for c in json.loads((P/'evaluation.json').read_text()):
   if psutil.virtual_memory().available<2*1024**3:raise RuntimeError('Low available system memory')
   inp=inputs(c['prompt']);clock=Clock();y=model.generate(**inp,max_new_tokens=c['max_tokens'],do_sample=False,pad_token_id=tok.pad_token_id,streamer=clock)
   torch.mps.synchronize();end=time.perf_counter();ids=y[0,inp['input_ids'].shape[1]:].tolist();text=tok.decode(ids,skip_special_tokens=True).strip()
   r={'id':c['id'],'text':text,'token_ids':ids,'expected':c['answer'],'strict_correct':None if c['answer'] is None else text==c['answer'],'first_answer_letter':text[:1] if text[:1] in ['A','B'] else None,'hit_token_limit':len(ids)>=c['max_tokens'],'ttft_seconds':None if clock.first is None else clock.first-clock.start,'total_seconds':end-clock.start}
   rows.append(r);(out/'responses.json').write_text(json.dumps(rows,indent=2)+'\n');print(a.label,c['id'],r['strict_correct'],round(r['total_seconds'],2),flush=True)
  if a.teacher:
   logits=[];sequences=[]
   for group,prompts in [('calibration',(P/'calibration.txt').read_text().splitlines()),('heldout',[c['prompt'] for c in json.loads((P/'evaluation.json').read_text())[-4:]])]:
    for i,prompt in enumerate(prompts):
     inp=inputs(prompt);z=model(**inp,use_cache=False).logits[0,-1].float().cpu()
     if not torch.isfinite(z).all():raise RuntimeError('Nonfinite teacher logits')
     if group=='calibration':logits.append(z)
     y=model.generate(**inp,max_new_tokens=32,do_sample=False,pad_token_id=tok.pad_token_id)
     sequences.append({'id':group+'-'+str(i),'split':group,'prompt':prompt,'input_ids':inp['input_ids'][0].tolist(),'target_ids':y[0,inp['input_ids'].shape[1]:].tolist()})
   torch.save(torch.stack(logits),out/'teacher-calibration-logits.pt')
   (out/'teacher-sequences.json').write_text(json.dumps(sequences,indent=2)+'\n')
 labelled=[r for r in rows if r['expected'] is not None]
 (out/'summary.json').write_text(json.dumps({'label':a.label,'cases':len(rows),'labelled_cases':len(labelled),'strict_correct':sum(r['strict_correct'] for r in labelled),'answer_letter_correct':sum(r['first_answer_letter']==r['expected'] for r in labelled),'truncated':sum(r['hit_token_limit'] for r in rows),'open_ended_adjudication':'pending','mps_driver_allocated_bytes_at_end':torch.mps.driver_allocated_memory()},indent=2)+'\n')
 print('COMPLETE',a.label,flush=True)
if __name__=='__main__':main()
