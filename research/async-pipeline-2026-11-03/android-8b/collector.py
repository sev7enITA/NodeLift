"""Physical 8B pilot over the existing authenticated gateway; stop on scope drift."""
import argparse,hashlib,importlib.util,json,random,statistics,time
from pathlib import Path
root=Path.cwd();spec=importlib.util.spec_from_file_location('collector',root/'scripts/benchmark-impact.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--repetitions',type=int,default=3);p.add_argument('--tokens',type=int,default=128);p.add_argument('--wait-seconds',type=int,default=60);a=p.parse_args();c=m.Client(Path.home()/'.local/share/nodelift')
expected_target='667b0c1932bc6ffc593ed1d03f895bf2dc8dc6df21db3042284a6f4416b06a29';expected_draft='6f85a640a97cf2bf5b8e764087b1e83da0fdb51d7c9fab7d0fece9385611df83'
def phone():return next(x for x in c.admin('status')['nodes'] if x['name'].startswith('Xiaomi'))
def usable(n):
 caps=n['capabilities'];return n['online'] and caps['engine_ready'] and caps.get('app_version')=='0.2.13' and caps.get('draft_sha256')==expected_draft and caps.get('thermal') in ('nominal','light') and caps.get('battery_percent',0)>=20
for _ in range(a.wait_seconds):
 n=phone()
 if usable(n) and time.time()-n['last_seen']<7:break
 time.sleep(1)
else:raise SystemExit('No fresh, ready 0.2.13 phone with the expected 1B draft')
e=c.admin('engine/status');assert not e['busy'];config=e['config'];sha=lambda x:hashlib.file_digest(open(x,'rb'),'sha256').hexdigest();assert sha(config['target_model'])==expected_target and sha(config['draft_model'])==expected_draft
prompts=json.loads((root/'research/async-pipeline-2026-11-03/local-8b/manifest.json').read_text())['prompts']
arms=[('host','serial','serial',1),('local_draft','serial','serial',4),('local_draft','experimental_batch','serial',1),('local_draft','experimental_batch','serial',4),('lookup','experimental_batch','serial',1),('remote_draft','serial','serial',4),('remote_draft','serial','bounded_v1',4),('remote_draft','experimental_batch','bounded_v1',4)]
order=[];rng=random.Random(2026110308)
for rep in range(a.repetitions):
 for pi in range(len(prompts)):
  ar=list(range(len(arms)));rng.shuffle(ar);order.extend((rep,pi,arm) for arm in ar)
a.output.mkdir(parents=True,exist_ok=False)
plan={'scope':'physical Xiaomi 0.2.13 O3 paired 8B target pilot; exploratory, not sustained qualification','target_sha256':expected_target,'draft_sha256':expected_draft,'native_host_sha256':sha(root/'native/build/host/lib/libnodelift.dylib'),'collector_sha256':sha(Path(__file__)),'source_commit':'ffd3de894e3fe6d36c6a0024892e3ce417d6f746','prompts':prompts,'arms':arms,'plan':order,'seed':2026110308,'max_tokens':a.tokens,'repetitions':a.repetitions,'config':{k:Path(v).name if k.endswith('_model') else v for k,v in config.items()},'phone_caps':n['capabilities'],'topology':'Xiaomi hotspot supplies Mac; operator-described, no wired transport','phone_threads_and_context':'saved device preferences; not yet included in native telemetry','warmup_policy':'warm host/local/remote; keep target and host draft resident in every arm; record warmups separately','limits':['One session, three public prompts; not independent-session confidence or thermal endurance','No measured energy','Self-reported phone durations; residual is not RTT','Experimental batch mismatches disqualify exact-output speedup','Late cleanup can retain unknown work; client completion includes cleanup'],'started_at_unix':time.time()}
m.atomic(a.output/'manifest.json',plan)
def clean(x):
 if isinstance(x,dict):return {k:(m.digest(v) if k=='node_id' and v else clean(v)) for k,v in x.items()}
 if isinstance(x,list):return [clean(v) for v in x]
 return x
def run(rep,pi,arm,warm=False):
 node=phone();assert usable(node),'Phone unavailable or scope changed before run'
 assert c.admin('engine/status')['config']==config,'Host config changed'
 mode,verify,pipeline,k=arms[arm];before=m.telemetry(node)
 r=c.capture('Say hello.' if warm else prompts[pi],mode,n['id'],16 if warm else a.tokens,10000,policy='fixed',draft_k=k,pipeline=pipeline,verification_mode=verify)
 identity=r.get('identity',{});r['identity_matches']=identity.get('target_sha256')==expected_target and identity.get('config')==config and (mode not in ('local_draft','remote_draft') or identity.get('draft_sha256')==expected_draft)
 if identity.get('config'):
  for k2 in ('target_model','draft_model'):identity['config'][k2]=Path(identity['config'][k2]).name
 node_after=phone();r.update(repetition=rep,prompt_id=pi,arm=arm,warmup=warm,telemetry_before=before,telemetry_after=m.telemetry(node_after),phone_available_after=usable(node_after));r=clean(r)
 with (a.output/('warmups.jsonl' if warm else 'runs.jsonl')).open('a') as f:f.write(json.dumps(r)+'\n')
 print('warmup' if warm else 'run',rep,pi,arm,r['status'],round(r['duration_ms'],1),r['metrics'].get('accepted_tokens'),r['fallback'],r['lookahead_cleanup_incomplete'],flush=True)
 if not r['identity_matches'] or r['status']!='completed' or not r['phone_available_after']:raise RuntimeError('Stopped after scope change or failure; retained partial result')
 return r
rows=[]
try:
 for arm in [0,1,5,6]:run(-1,0,arm,True)
 for rep,pi,arm in order:rows.append(run(rep,pi,arm))
finally:
 if rows:
  base={(r['repetition'],r['prompt_id']):r for r in rows if r['arm']==0};summaries=[]
  for arm in range(1,len(arms)):
   pairs=[]
   for r in rows:
    if r['arm']!=arm:continue
    b=base.get((r['repetition'],r['prompt_id']))
    if not b:continue
    exact=r['tokens_sha256']==b['tokens_sha256'] and r['token_count']==b['token_count'] and r['finish_reason']==b['finish_reason']
    pairs.append({'repetition':r['repetition'],'prompt_id':r['prompt_id'],'exact_tokens':exact,'speedup':b['duration_ms']/r['duration_ms'],'ttft_delta_ms':r['ttft_ms']-b['ttft_ms'],'fallback':r['fallback'],'cleanup_incomplete':r['lookahead_cleanup_incomplete']})
   summaries.append({'arm':arm,'definition':arms[arm],'pairs':pairs,'all_exact':bool(pairs) and all(x['exact_tokens'] for x in pairs),'median_speedup':statistics.median(x['speedup'] for x in pairs) if pairs else None})
  m.atomic(a.output/'summary.json',summaries)
