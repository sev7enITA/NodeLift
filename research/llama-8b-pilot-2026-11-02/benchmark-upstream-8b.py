"""Loopback llama-server comparison on identical tokenized public prompts.

Three upstream arms are compared only with their own server baseline. Errors
are retained as records. Models are local inputs and are not redistributed.
"""
import argparse,hashlib,json,os,random,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'host'))
from nodelift.native import Native,library_path

def digest(path):
 with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def free_port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def fetch(port,path,value=None):
 raw=None if value is None else json.dumps(value).encode();req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=raw,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=180) as r:return json.load(r)
p=argparse.ArgumentParser();p.add_argument('--target',required=True);p.add_argument('--draft',required=True);p.add_argument('--server',required=True);p.add_argument('--prompt-manifest',required=True);p.add_argument('--output',required=True);p.add_argument('--repetitions',type=int,default=2);p.add_argument('--tokens',type=int,default=64);args=p.parse_args()
folder=Path(args.output);folder.mkdir(parents=True,exist_ok=True);target=Path(args.target).resolve();draft=Path(args.draft).resolve();binary=Path(args.server).resolve();prompts=json.loads(Path(args.prompt_manifest).read_text())['prompts']
with Native() as e:
 info=e.call('load',path=str(target),n_ctx=2048,threads=8,gpu_layers=999);prefixes=[e.call('tokenize',text=text,chat=True)['tokens'] for text in prompts]
rng=random.Random(20261031);arms=['none','draft-simple','ngram-mod'];plan=[]
for rep in range(args.repetitions):
 order=arms[:];rng.shuffle(order)
 for arm in order:
  ids=list(range(len(prompts)));rng.shuffle(ids);plan.append({'repetition':rep,'arm':arm,'prompt_order':ids})
manifest={'source_revision':(ROOT/'native/llama.lock').read_text().strip(),'server_sha256':digest(binary),'native_sha256':digest(library_path()),'target_sha256':digest(target),'draft_sha256':digest(draft),'tokenizer_fingerprint':info['tokenizer_fingerprint'],'prompt_manifest_sha256':digest(args.prompt_manifest),'prompts':prompts,'prefixes':prefixes,'tokens_max':args.tokens,'repetitions':args.repetitions,'seed':20261031,'plan':plan,'started':time.time(),'limitations':['server HTTP timing is not NodeLift controller timing','server process restarted and warmed per arm','all models local, one host and one experimental period','CPU/GPU utilization, effective placement, energy and thermals unmeasured']}
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');rows=[]
with (folder/'runs.jsonl').open('w') as out:
 for cell in plan:
  arm=cell['arm'];rep=cell['repetition'];port=free_port();process=None;start_error=None
  command=[str(binary),'-m',str(target),'-ngl','999','-c','2048','-b','512','-ub','512','-t','8','-tb','8','-fa','on','--parallel','1','--host','127.0.0.1','--port',str(port),'--spec-type',arm,'--spec-draft-n-max','4','--no-context-shift','--no-webui']
  if arm=='draft-simple':command+=['-md',str(draft),'-ngld','999','-td','8','--spec-draft-p-min','0']
  # Logs are temporary and not published: they can contain local model paths.
  with tempfile.TemporaryFile(mode='w+') as log:
   try:
    process=subprocess.Popen(command,stdout=log,stderr=log);deadline=time.monotonic()+90
    while True:
     if process.poll() is not None:raise RuntimeError('server exited before readiness')
     try:
      if fetch(port,'/health').get('status')=='ok':break
     except (OSError,ValueError):pass
     if time.monotonic()>deadline:raise TimeoutError('server readiness timeout')
     time.sleep(.2)
    def payload(index,count):return {'prompt':prefixes[index],'n_predict':count,'temperature':0,'top_k':1,'top_p':1,'min_p':0,'repeat_penalty':1,'frequency_penalty':0,'presence_penalty':0,'cache_prompt':False,'return_tokens':True,'stream':False,'seed':0}
    fetch(port,'/completion',payload(0,16))
   except Exception as e:start_error=type(e).__name__+': '+str(e)[:160]
   for index in cell['prompt_order']:
    row={'arm':arm,'repetition':rep,'prompt_id':index,'status':'failed' if start_error else 'running'}
    if start_error:row['error']=start_error
    else:
     t=time.perf_counter()
     try:
      result=fetch(port,'/completion',payload(index,args.tokens));elapsed=time.perf_counter()-t;tokens=result.get('tokens')
      if not isinstance(tokens,list):raise ValueError('missing token list')
      row.update(status='completed',request_wall_seconds=elapsed,tokens=tokens,content=result.get('content'),timings=result.get('timings'),stop_type=result.get('stop_type'),tokens_predicted=result.get('tokens_predicted'),truncated=result.get('truncated'))
     except Exception as e:row.update(status='failed',error=type(e).__name__+': '+str(e)[:160],request_wall_seconds=time.perf_counter()-t)
    rows.append(row);out.write(json.dumps(row,ensure_ascii=False)+'\n');out.flush();print(len(rows),'/',len(plan)*len(prompts),arm,rep,index,row['status'],flush=True)
   if process:
    process.terminate()
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:process.kill();process.wait()
(folder/'hashes.json').write_text(json.dumps({p.name:digest(p) for p in folder.iterdir() if p.is_file() and p.name!='hashes.json'},indent=2)+'\n')
