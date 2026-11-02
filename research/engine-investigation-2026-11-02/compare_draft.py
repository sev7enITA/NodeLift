import os,sys,time,json,hashlib,statistics,platform
from pathlib import Path
sys.path.insert(0,sys.argv[1]+'/host')
from nodelift.native import Native
model=sys.argv[2]; gpu=int(sys.argv[3]); output=sys.argv[4]
libs={'baseline':sys.argv[5],'candidate':sys.argv[6]}
engines={}
for name,path in libs.items():
 os.environ['NODELIFT_LIBRARY']=path
 e=Native(); info=e.call('load',path=model,n_ctx=1024,threads=8,gpu_layers=gpu);engines[name]=e
prefix=engines['baseline'].call('tokenize',text='Explain why predictable network latency matters for distributed machine learning. Include a practical example.',chat=True)['tokens']
assert prefix == engines['candidate'].call('tokenize',text='Explain why predictable network latency matters for distributed machine learning. Include a practical example.',chat=True)['tokens']
records=[]
for scenario in ['all_rejected','partial_acceptance','all_accepted']:
 for i in range(16):
  row={'scenario':scenario,'iteration':i,'warmup':i<4}; outputs={}
  order=['baseline','candidate'] if i%2==0 else ['candidate','baseline']
  for name in order:
   e=engines[name];e.call('reset');e.call('prefill',prefix=prefix)
   first=e.call('draft',prefix=prefix,count=4)['tokens']
   assert len(first)==4
   accepted={'all_rejected':0,'partial_acceptance':2,'all_accepted':4}[scenario]
   p=prefix+first[:accepted]+[(first[accepted%4]+1)%info['vocab_size']]
   t=time.perf_counter(); out=e.call('draft',prefix=p,count=4); dt=1000*(time.perf_counter()-t)
   outputs[name]=(first,out['tokens'],out['eos']);row[name+'_ms']=dt
  assert outputs['baseline']==outputs['candidate'], ('outputs differ',scenario,i)
  row['token_output_sha256']=hashlib.sha256(json.dumps(outputs['baseline']).encode()).hexdigest();records.append(row)
for i in range(10):
 row={'scenario':'autoregressive_32','iteration':i,'warmup':i<2};outputs={}
 order=['baseline','candidate'] if i%2==0 else ['candidate','baseline']
 for name in order:
  e=engines[name];e.call('reset');p=prefix[:]; generated=[]
  t=time.perf_counter()
  for _ in range(32):
   out=e.call('draft',prefix=p,count=1);generated+=out['tokens'];p+=out['tokens']
   if out['eos']:break
  row[name+'_ms']=1000*(time.perf_counter()-t); outputs[name]=generated
 assert outputs['baseline']==outputs['candidate'],('autoregressive tokens differ',i)
 row['token_output_sha256']=hashlib.sha256(json.dumps(outputs['baseline']).encode()).hexdigest();records.append(row)
for scenario in ['two_call_all_rejected','two_call_all_retained']:
 for i in range(16):
  row={'scenario':scenario,'iteration':i,'warmup':i<4};outputs={}
  order=['baseline','candidate'] if i%2==0 else ['candidate','baseline']
  for name in order:
   e=engines[name];e.call('reset');e.call('prefill',prefix=prefix)
   t=time.perf_counter();first=e.call('draft',prefix=prefix,count=4)['tokens']
   retained=0 if scenario=='two_call_all_rejected' else 4
   p=prefix+first[:retained]+[(first[retained%4]+1)%info['vocab_size']]
   second=e.call('draft',prefix=p,count=4)
   row[name+'_ms']=1000*(time.perf_counter()-t);outputs[name]=(first,second['tokens'],second['eos'])
  assert outputs['baseline']==outputs['candidate'],(scenario,i)
  row['token_output_sha256']=hashlib.sha256(json.dumps(outputs['baseline']).encode()).hexdigest();records.append(row)
summary={}
for scenario in sorted(set(r['scenario'] for r in records)):
 rows=[r for r in records if r['scenario']==scenario and not r['warmup']]
 ratios=[r['candidate_ms']/r['baseline_ms'] for r in rows]
 summary[scenario]={'n':len(rows),'baseline_median_ms':statistics.median(r['baseline_ms'] for r in rows),'candidate_median_ms':statistics.median(r['candidate_ms'] for r in rows),'paired_ratio_median':statistics.median(ratios),'min_ratio':min(ratios),'max_ratio':max(ratios)}
result={'kind':'isolated native microbenchmark, not a phone benchmark','model_filename':Path(model).name,'model_sha256':hashlib.sha256(Path(model).read_bytes()).hexdigest(),'native_sha256':{n:hashlib.sha256(Path(p).read_bytes()).hexdigest() for n,p in libs.items()},'requested_gpu_layers':gpu,'threads':8,'platform':platform.platform(),'runtime':info['runtime'],'prompt_tokens':len(prefix),'warmup_excluded':True,'summary':summary,'samples':records}
Path(output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary,indent=2))
for e in engines.values():e.close()
