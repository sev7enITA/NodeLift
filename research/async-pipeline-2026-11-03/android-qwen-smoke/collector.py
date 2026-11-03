import importlib.util,time,json
from pathlib import Path
s=importlib.util.spec_from_file_location('collector','scripts/benchmark-impact.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);c=m.Client(Path.home()/'.local/share/nodelift')
for attempt in range(90):
 n=next(x for x in c.admin('status')['nodes'] if x['name'].startswith('Xiaomi'))
 if n['online'] and time.time()-n['last_seen']<6 and n['capabilities']['app_version']=='0.2.13' and n['capabilities']['engine_ready']:break
 time.sleep(1)
else:raise SystemExit('No fresh ready phone contact within 90 seconds')
p=Path('research/async-pipeline-2026-11-03/android-qwen-smoke');p.mkdir(exist_ok=False)
plan={'scope':'physical Android telemetry and pipeline smoke test; not a matched performance benchmark','date':'2026-11-03','node_label':'Xiaomi 17 Ultra (reported Xiaomi 25128PNA1C)','node_id_sha256':m.digest(n['id']),'caps':n['capabilities'],'config':c.admin('engine/status')['config'],'prompt':'Explain in one sentence what RAM does.','tokens':16,'arms':[('host','serial'),('remote_draft','serial'),('remote_draft','bounded_v1')],'timeout_ms':10000,'verification_mode':'serial'}
for k in ['target_model','draft_model']:plan['config'][k]=Path(plan['config'][k]).name
m.atomic(p/'manifest.json',plan)
def clean(x):
 if isinstance(x,dict):return {k:(m.digest(v) if k=='node_id' and v else clean(v)) for k,v in x.items()}
 if isinstance(x,list):return [clean(v) for v in x]
 return x
for mode,pipeline in plan['arms']:
 before=m.telemetry(next(x for x in c.admin('status')['nodes'] if x['id']==n['id']))
 r=c.capture(plan['prompt'],mode,n['id'],plan['tokens'],10000,policy='fixed',draft_k=4,pipeline=pipeline,verification_mode='serial');r.update(mode=mode,pipeline=pipeline,telemetry_before=before,telemetry_after=m.telemetry(next(x for x in c.admin('status')['nodes'] if x['id']==n['id'])))
 if r.get('identity',{}).get('config'):
  for k in ('target_model','draft_model'):
   if k in r['identity']['config']:r['identity']['config'][k]=Path(r['identity']['config'][k]).name
 m.atomic(p/(mode+'-'+pipeline+'.json'),clean(r));print(mode,pipeline,r['status'],r['token_count'],r['duration_ms'],r['metrics'].get('accepted'),r['fallback'],len(r['remote_trace']),flush=True)
