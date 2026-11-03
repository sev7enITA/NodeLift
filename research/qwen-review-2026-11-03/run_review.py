#!/usr/bin/env python3
"""Run frozen source packets through the actual local NodeLift provider bridge.

Requires an already downloaded, verified model. Saves model responses without
executing model suggestions. No cloud inference, patching, or publishing.
"""
import argparse,hashlib,http.client,importlib.util,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
MODEL='Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q4_K_P.gguf'
EXPECTED='ba36dc3c2b2ff5e0aa5d71092a8894546996a6a119ae391803dda07cdc08516d'
ALIAS='nodelift-review-qwen38-27b-q4kp';PORT=9891

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while b:=f.read(8*1024**2):h.update(b)
 return h.hexdigest()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--server',type=Path,required=True);parser.add_argument('--wait-download',type=int,default=0);parser.add_argument('--output-directory',type=Path);args=parser.parse_args()
 record_dir=args.output_directory.resolve() if args.output_directory else OUT
 if (record_dir/'run-manifest.json').exists():raise RuntimeError('Evidence already exists; choose a new --output-directory')
 record_dir.mkdir(parents=True,exist_ok=True)
 artifact=ROOT/'artifacts/qwen-review-2026-11-03';model=ROOT/'.models'/MODEL
 deadline=time.monotonic()+args.wait_download
 while not model.exists():
  if time.monotonic()>deadline:raise RuntimeError('Verified model is not downloaded yet')
  time.sleep(5)
 if sha(model)!=EXPECTED:raise RuntimeError('Model hash differs from pinned Hub identity')
 spec=importlib.util.spec_from_file_location('benchmark_client',ROOT/'scripts/benchmark-impact.py');clientmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(clientmod)
 client=clientmod.Client(Path.home()/'.local/share/nodelift')
 state=client.admin('engine/status')
 if state['busy']:raise RuntimeError('NodeLift is busy; do not overlap another inference')
 command=[str(args.server.resolve()),'--model',str(model),'--alias',ALIAS,'--host','127.0.0.1','--port',str(PORT),'--ctx-size','16384','--parallel','1','--n-gpu-layers','999','--flash-attn','on','--jinja','--reasoning','off','--chat-template-kwargs','{"enable_thinking":false}','--spec-type','none']
 manifest={'model_repo':'HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF','revision':'993a5971fda8f30dd1b7eb2654792ba4415c7460','model_file':MODEL,'model_sha256':EXPECTED,'server_sha256':sha(args.server),'server_source_commit':'ddf48f85c933c1f438212a02eb21e7b001d2d37d','server_source_verification':'/tmp/nodelift-upstream-source-verify.json','backend':'local_api','context_tokens':16384,'max_output_tokens':512,'reasoning':False,'mtp_enabled':False,'scope':'Static source review through NodeLift; no model-executed tests; no distributed inference','started_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'host/nodelift/engine.py',ROOT/'host/nodelift/providers.py',ROOT/'host/nodelift/host.py']}}
 (record_dir/'run-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 log=open(artifact/'server.log','wb');server=subprocess.Popen(command,stdout=log,stderr=log)
 try:
  for _ in range(180):
   if server.poll() is not None:raise RuntimeError('Local server exited; inspect retained server log')
   try:
    conn=http.client.HTTPConnection('127.0.0.1',PORT,timeout=2);conn.request('GET','/health');res=conn.getresponse();ok=res.status==200;res.read();conn.close()
    if ok:break
   except OSError:pass
   time.sleep(1)
  else:raise RuntimeError('Local model load deadline exceeded')
  client.admin('models/import',{'path':str(model.resolve())})
  previous=state['providers']['local_url']
  client.admin('providers/configure',{'backend':'local_api','base_url':f'http://127.0.0.1:{PORT}/v1'})
  catalog=client.admin('providers/models',{'backend':'local_api'})
  if not any(x['id']==ALIAS for x in catalog['models']):raise RuntimeError('Model missing from NodeLift provider catalog')
  packets=json.loads((OUT/'packets.json').read_text());results=[]
  for packet in packets:
   name=packet['id'];prompt=(OUT/(name+'.prompt.txt')).read_text()
   if hashlib.sha256(prompt.encode()).hexdigest()!=packet['prompt_sha256']:raise RuntimeError('Packet changed')
   run_id=client.admin('engine/run',{'backend':'local_api','provider_model':ALIAS,'mode':'host','prompt':prompt,'max_tokens':512})['run_id']
   deadline=time.monotonic()+320
   while time.monotonic()<deadline:
    rows=client.admin('engine/status')['runs'];run=next(x for x in rows if x['id']==run_id)
    if run['status'] in ('completed','failed','cancelled'):break
    time.sleep(1)
   else:
    client.admin('engine/stop',{'run_id':run_id});raise RuntimeError('NodeLift review deadline exceeded')
   record={'packet':name,'run_id':run_id,'status':run['status'],'backend':run['backend'],'provider_model':run['provider_model'],'text':run['text'],'finish_reason':run.get('finish_reason'),'usage':run.get('usage'),'metrics':run['metrics'],'measurement_scope':run.get('measurement_scope'),'error':run.get('error')}
   (record_dir/(name+'.response.json')).write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n');results.append(record)
   print(name,record['status'],record['finish_reason'],flush=True)
   if run['status']!='completed':raise RuntimeError('Review failed; do not label it completed')
  (record_dir/'completion.json').write_text(json.dumps({'completed_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'completed_packets':len(results),'truncated_packets':[r['packet'] for r in results if r['finish_reason']=='length'],'human_adjudication':'pending'},indent=2)+'\n')
 finally:
  # Restore only this session's local endpoint after work. Do not touch native
  # target/draft configuration, phone pairing, credentials, or other servers.
  if 'previous' in locals():
   try:client.admin('providers/configure',{'backend':'local_api','base_url':previous})
   except Exception:pass
  server.terminate()
  try:server.wait(timeout=10)
  except subprocess.TimeoutExpired:server.kill();server.wait()
  log.close()
if __name__=='__main__':main()
