"""Fixed versus measured adaptive gate on the same existing local models."""
import argparse,hashlib,json,os,random,subprocess,sys,tempfile,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--checkout',required=True);p.add_argument('--target',required=True);p.add_argument('--draft',required=True);p.add_argument('--prompt-manifest',required=True);p.add_argument('--output',required=True);args=p.parse_args()
checkout=Path(args.checkout).resolve();sys.path.insert(0,str(checkout/'host'))
from nodelift.engine import Controller
from nodelift.state import State
from nodelift.native import library_path

def digest(path):
 with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
prompts=json.loads(Path(args.prompt_manifest).read_text())['prompts'];folder=Path(args.output);folder.mkdir(parents=True,exist_ok=True)
plan=[(p,r,arm) for p in range(len(prompts)) for r in range(2) for arm in ('host','fixed','adaptive')];random.Random(20261102).shuffle(plan)
manifest={'purpose':'Exploratory same-host adaptive policy','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip(),'library_sha256':digest(library_path()),'target_sha256':digest(args.target),'draft_sha256':digest(args.draft),'prompt_manifest_sha256':digest(args.prompt_manifest),'prompts':prompts,'seed':20261102,'plan':plan,'n_ctx':2048,'threads_requested':8,'gpu_layers_requested':999,'output_budget':64,'started':time.time(),'limitations':['both models are resident','not a physical phone or PC test','one period on one Mac','no load or thermals telemetry']}
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with tempfile.TemporaryDirectory(prefix='nodelift-adaptive-') as state:
 engine=Controller(State(Path(state)));engine.configure({'target_model':str(Path(args.target).resolve()),'draft_model':str(Path(args.draft).resolve()),'n_ctx':2048,'threads':8,'gpu_layers':999})
 def execute(text,arm):
  run={'prompt':text,'mode':'host' if arm=='host' else 'local_draft','draft_policy':'adaptive' if arm=='adaptive' else 'fixed','max_tokens':64,'draft_k':4}
  engine.start(run);deadline=time.monotonic()+180
  while engine.busy:
   if time.monotonic()>deadline:engine.stop();raise TimeoutError('run deadline')
   time.sleep(.05)
  return engine.status()['runs'][0]
 try:
  w=execute('Say hello briefly.','fixed')
  if w['status']!='completed':raise RuntimeError('warmup failed')
  with (folder/'runs.jsonl').open('w') as out:
   for i,(index,rep,arm) in enumerate(plan):
    try:
     row=execute(prompts[index],arm);row.update(prompt_id=index,repetition=rep,arm=arm)
     if 'identity' in row:
      for name in ('target_model','draft_model'):row['identity']['config'][name]=Path(row['identity']['config'][name]).name
    except Exception as e:row={'prompt_id':index,'repetition':rep,'arm':arm,'status':'failed','error':type(e).__name__+': '+str(e)[:200]}
    out.write(json.dumps(row,ensure_ascii=False)+'\n');out.flush();print(i+1,'/',len(plan),arm,index,rep,row['status'],flush=True)
 finally:
  for n in (engine.target,engine.draft):
   if n:n.close()
