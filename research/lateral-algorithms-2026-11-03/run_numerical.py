import pathlib,hashlib,json,subprocess,time,datetime
root=pathlib.Path.cwd();out=root/'research/lateral-algorithms-2026-11-03';binary=pathlib.Path('/tmp/nodelift-timing-build/nodelift-shape-probe');model=root/'.models/llama3.1-8b-ollama.gguf';cases=root/'research/async-pipeline-2026-11-03/shape-history-cases.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
assert sha(binary)=='c5e6a757d0888cab9f148711221836c648cd848464a7949bdbdbce8ee5980cc7'
assert sha(model)=='667b0c1932bc6ffc593ed1d03f895bf2dc8dc6df21db3042284a6f4416b06a29'
manifest={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'one-prefix numerical diagnostic, not a performance benchmark','binary_sha256':sha(binary),'model_sha256':sha(model),'cases_sha256':sha(cases),'plan_sha256':sha(out/'NUMERICAL-PLAN.md'),'profiles':[]}
for name,gpu,fa in [('metal-fa',999,1),('metal-no-fa',999,0),('cpu-fa',0,1),('cpu-no-fa',0,0)]:
 print('START',name,flush=True);target=out/(name+'.json');start=time.monotonic()
 try:
  with (out/(name+'.log')).open('w') as f:
   run=subprocess.run([str(binary),str(model),str(cases),str(target),str(gpu),'8',str(fa),'2048','1'],stdout=f,stderr=subprocess.STDOUT,timeout=600)
  row={'profile':name,'exit_code':run.returncode,'diagnostic_elapsed_seconds':time.monotonic()-start}
  if target.exists():
   v=json.loads(target.read_text());pos=[p for w in v['windows'] for p in w['positions']]
   row.update({'positions':len(pos),'argmax_flips':sum(p['top1_flipped'] for p in pos),'serial_repeat_flips':sum(p['control_top1_flipped'] for p in pos),'max_serial_repeat_logit_diff':max(p['max_abs_serial_control'] for p in pos),'result_sha256':sha(target)})
 except subprocess.TimeoutExpired:row={'profile':name,'error':'timeout','diagnostic_elapsed_seconds':time.monotonic()-start}
 manifest['profiles'].append(row);(out/'numerical-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(row),flush=True)
 if row.get('error') or row.get('exit_code')!=0 or row.get('max_serial_repeat_logit_diff',0)!=0:break
manifest['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(out/'numerical-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
