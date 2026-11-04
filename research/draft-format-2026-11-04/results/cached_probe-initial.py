"""Isolated cached greedy reference and candidate verifier. Not production NodeLift."""
import argparse,copy,hashlib,json,random,time,gc
from pathlib import Path
import torch,psutil
from transformers import AutoModelForCausalLM,AutoTokenizer
from transformers.generation.streamers import BaseStreamer
P=Path(__file__).resolve().parent;R=P.parents[1];A=R/'artifacts/heretic-mac-2026-11-04'
def save(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
class State:
 def __init__(self,model,ids,metrics,phase):
  self.model=model;self.ids=[];self.cache=None;self.last=None;self.metrics=metrics;self.feed(ids,phase)
 def feed(self,ids,phase,all_logits=False):
  assert ids
  torch.mps.synchronize();start=time.perf_counter()
  x=torch.tensor([ids],device='mps');mask=torch.ones((1,len(self.ids)+len(ids)),dtype=torch.long,device='mps')
  result=self.model(input_ids=x,attention_mask=mask,past_key_values=self.cache,use_cache=True,logits_to_keep=0 if all_logits else 1)
  self.cache=result.past_key_values;z=result.logits[0];self.ids+=ids;self.last=z[-1]
  assert self.cache.get_seq_length()==len(self.ids)
  if not torch.isfinite(z).all().item():raise ValueError('Nonfinite logits')
  torch.mps.synchronize();self.metrics[phase]=self.metrics.get(phase,0)+time.perf_counter()-start
  return z
 def crop(self,n):
  assert 0<=n<=len(self.ids)
  if n<len(self.ids):self.cache.crop(n-len(self.ids));self.ids=self.ids[:n];self.last=None
  assert self.cache.get_seq_length()==n
 def reconcile(self,desired,phase):
  common=0
  for a,b in zip(self.ids,desired):
   if a!=b:break
   common+=1
  if common==len(desired)==len(self.ids):assert self.last is not None;return
  if common==len(desired):common-=1
  self.crop(common);self.feed(desired[common:],phase)
 def next(self):return int(self.last.argmax().item())
class Clock(BaseStreamer):
 def __init__(self):self.first=None;self.prompt=True
 def put(self,value):
  if self.prompt:self.prompt=False
  elif self.first is None:torch.mps.synchronize();self.first=time.perf_counter()
 def end(self):pass

def custom(target,draft,tp,dp,arm,budget,eos):
 phases={};torch.mps.synchronize();start=time.perf_counter();t=State(target,tp,phases,'target_prefill');out=[t.next()];torch.mps.synchronize();ttft=time.perf_counter()-start
 accepted=proposed=rounds=0;trace=[];d=None
 if out[-1] not in eos and len(out)<budget:t.feed([out[-1]],'target_decode')
 while len(out)<budget and out[-1] not in eos:
  if time.perf_counter()-start>180:raise TimeoutError('Per-run 180 second limit')
  if arm=='target':
   token=t.next();out.append(token)
   if token not in eos and len(out)<budget:t.feed([token],'target_decode')
   continue
  before=len(out);k=min(4,budget-before);dst=dp+out
  if d is None:d=State(draft,dst,phases,'draft_prefill')
  else:d.reconcile(dst,'draft_sync')
  cand=[]
  for i in range(k):
   token=d.next();cand.append(token)
   if token in eos:break
   if i<k-1:d.feed([token],'draft_decode')
  proposed+=len(cand);rounds+=1;j=0
  if arm=='aligned_serial':
   for token in cand:
    expected=t.next();out.append(expected);same=token==expected
    if same:j+=1
    if expected in eos or len(out)>=budget:break
    t.feed([expected],'target_verify_serial')
    if not same:break
   if j==len(cand) and len(out)<budget and out[-1] not in eos:
    out.append(t.next())
    if out[-1] not in eos and len(out)<budget:t.feed([out[-1]],'target_verify_serial')
  else:
   # Reject a wrong first candidate using already-available authoritative logits.
   expected=t.next();old_length=len(t.ids)
   if cand[0]!=expected:committed=[expected]
   else:
    z=t.feed(cand,'target_verify_batch',all_logits=True);pred=[expected]+z.argmax(-1).tolist()
    while j<len(cand) and cand[j]==pred[j]:j+=1
    committed=cand[:j]+[pred[j]]
   committed=committed[:budget-before]
   for index,token in enumerate(committed):
    if token in eos:committed=committed[:index+1];break
   out+=committed;j=min(j,len(committed))
   if len(out)<budget and out[-1] not in eos:
    # The last committed token is the verifier's correction or bonus token.
    keep=old_length+len(committed)-1;t.crop(keep);t.feed([committed[-1]],'target_sync')
  accepted+=j;trace.append({'offset':before,'proposed':len(cand),'accepted':j,'committed':len(out)-before,'candidate_ids':cand})
 torch.mps.synchronize();elapsed=time.perf_counter()-start
 return {'tokens':out,'seconds':elapsed,'ttft_seconds':ttft,'phases_seconds':phases,'unattributed_seconds':elapsed-sum(phases.values()),'proposed':proposed,'accepted':accepted,'discarded':proposed-accepted,'rounds':rounds,'trace':trace}

def upstream(target,draft,tp,budget,assisted=False):
 x=torch.tensor([tp],device='mps');clock=Clock();kwargs={}
 if assisted:
  draft.generation_config.num_assistant_tokens=4;draft.generation_config.num_assistant_tokens_schedule='constant';draft.generation_config.assistant_confidence_threshold=0
  kwargs['assistant_model']=draft
 torch.mps.synchronize();start=time.perf_counter()
 y=target.generate(input_ids=x,attention_mask=torch.ones_like(x),max_new_tokens=budget,do_sample=False,pad_token_id=target.generation_config.eos_token_id,streamer=clock,**kwargs)
 torch.mps.synchronize();end=time.perf_counter()
 return {'tokens':y[0,len(tp):].tolist(),'seconds':end-start,'ttft_seconds':clock.first-start,'phases_seconds':None,'scope':'Upstream API including streamer; no per-phase instrumentation'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--smoke',action='store_true');a=ap.parse_args();a.out.mkdir(exist_ok=False,parents=True)
 torch.manual_seed(42);torch.set_num_threads(8)
 targetpath=(A/'base-model-path.txt').read_text().strip();draftpath=json.loads((A/'draft-model.json').read_text())['path']
 tt=AutoTokenizer.from_pretrained(targetpath,local_files_only=True);dt=AutoTokenizer.from_pretrained(draftpath,local_files_only=True)
 assert tt.get_vocab()==dt.get_vocab()
 target=AutoModelForCausalLM.from_pretrained(targetpath,local_files_only=True,dtype=torch.float16,device_map='mps',attn_implementation='sdpa').eval()
 draft=AutoModelForCausalLM.from_pretrained(draftpath,local_files_only=True,dtype=torch.float16,device_map='mps',attn_implementation='sdpa').eval()
 eos=target.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else eos
 prompts=json.loads((P/'prompts.json').read_text());arms=['target','raw_batch','aligned_batch','aligned_serial','upstream_assisted'];budget=12 if a.smoke else 64;reps=1 if a.smoke else 3
 def templates(prompt):
  messages=[{'role':'system','content':'You are a helpful assistant.'},{'role':'user','content':prompt}]
  def tokens(tok):
   v=tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False);return v if isinstance(v,list) else v['input_ids']
  tp,dp=tokens(tt),tokens(dt);assert dp[:len(tp)]==tp;return tp,dp
 def run(arm,prompt):
  if psutil.virtual_memory().available<2*1024**3:raise MemoryError('Low available memory')
  tp,dp=templates(prompt)
  if arm=='upstream_assisted':return upstream(target,draft,tp,budget,True)
  return custom(target,draft,tp,dp if arm.startswith('aligned') else tp,arm,budget,eos)
 with torch.inference_mode():
  # All arms run before measurements. Compare custom serial with upstream serial.
  warm=[]
  for arm in arms:
   r=run(arm,'Explain a mutex in one sentence.');warm.append({'arm':arm,**r});print('WARM',arm,round(r['seconds'],3),flush=True)
  tp,_=templates('Explain a mutex in one sentence.');reference=upstream(target,draft,tp,budget)
  assert warm[0]['tokens']==reference['tokens'],'Custom serial differs from upstream serial warmup'
  assert next(x for x in warm if x['arm']=='aligned_serial')['tokens']==reference['tokens'],'Serial verifier differs from reference warmup'
  save(a.out/'warmup.json',{'rows':warm,'upstream_serial':reference})
  plan=[];rng=random.Random(20261104)
  for rep in range(reps):
   for i,p in enumerate(prompts[:1] if a.smoke else prompts):
    order=arms.copy();rng.shuffle(order);plan += [{'rep':rep,'prompt':i,'arm':arm} for arm in order]
  save(a.out/'manifest.json',{'scope':'Local PyTorch MPS prototype, no native NodeLift/network/energy measurement','budget':budget,'repetitions':reps,'plan':plan,'prompts':prompts,'arms':arms,'torch':torch.__version__,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'target_revision':'cdbee75f17c01a7cc42f958dc650907174af0554','draft_revision':'c1899de289a04d12100db370d81485cdf75e47ca','timing':'Resident models; fresh KV per request; MPS synchronization and finite checks included; upstream arm has different instrumentation','first_token':'Authoritative first token emitted before draft prefill in custom speculative arms'})
  with (a.out/'runs.jsonl').open('w') as f:
   for i,item in enumerate(plan):
    r=run(item['arm'],prompts[item['prompt']]['prompt']);r.update(item);r['text']=tt.decode(r['tokens'],skip_special_tokens=True);f.write(json.dumps(r)+'\n');f.flush();print(i+1,len(plan),item,round(r['seconds'],3),len(r['tokens']),flush=True)
    if a.smoke:
     tp,_=templates(prompts[item['prompt']]['prompt']);ref=upstream(target,draft,tp,budget)
     if item['arm'] in ['target','aligned_serial']:assert r['tokens']==ref['tokens'],'Serial reference mismatch'
  print('COMPLETE',flush=True)
if __name__=='__main__':main()
