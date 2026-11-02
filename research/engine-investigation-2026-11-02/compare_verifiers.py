import os,sys,time,json,statistics,hashlib
from pathlib import Path
sys.path.insert(0,sys.argv[1]+'/host');from nodelift.native import Native
model=sys.argv[2];gpu=int(sys.argv[3]);outpath=sys.argv[4]
with Native() as oracle,Native() as e:
 info=oracle.call('load',path=model,n_ctx=512,threads=8,gpu_layers=gpu);e.call('load',path=model,n_ctx=512,threads=8,gpu_layers=gpu)
 p=oracle.call('tokenize',text='Rispondi con una frase: perché il cielo appare blu?',chat=True)['tokens'];expected=oracle.call('draft',prefix=p,count=64)['tokens']
 prefix=p+expected[:20]; proposal=expected[20:24];want=expected[20:25];records=[]
 for i in range(20):
  row={'iteration':i,'warmup':i<4}
  for strict in ([False,True] if i%2==0 else [True,False]):
   e.call('reset');e.call('prefill',prefix=prefix)
   t=time.perf_counter();r=e.call('verify',prefix=prefix,proposal=proposal,remaining=5,strict=strict);elapsed=(time.perf_counter()-t)*1000
   name='serial' if strict else 'batch';row[name+'_ms']=elapsed;row[name+'_matches_oracle']=r['tokens']==want;row[name+'_output_sha256']=hashlib.sha256(json.dumps(r['tokens']).encode()).hexdigest();row[name+'_accepted']=r['accepted']
  records.append(row)
 rows=[r for r in records if not r['warmup']]; summary={'serial_median_ms':statistics.median(r['serial_ms'] for r in rows),'batch_median_ms':statistics.median(r['batch_ms'] for r in rows),'paired_serial_to_batch_median':statistics.median(r['serial_ms']/r['batch_ms'] for r in rows),'serial_matches':sum(r['serial_matches_oracle'] for r in rows),'batch_matches':sum(r['batch_matches_oracle'] for r in rows),'sample_count':len(rows)}
 result={'description':'isolated verifier microbenchmark with perfect supplied proposals; not end-to-end inference','model_filename':Path(model).name,'model_sha256':hashlib.sha256(Path(model).read_bytes()).hexdigest(),'native_sha256':hashlib.sha256(Path(os.environ['NODELIFT_LIBRARY']).read_bytes()).hexdigest(),'gpu_layers_requested':gpu,'threads':8,'runtime':info['runtime'],'prefix_len':len(prefix),'proposal_len':len(proposal),'summary':summary,'samples':records}
 Path(outpath).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary,indent=2))
