"""Matched upstream comparators. Real weights, serial arms, actual token IDs."""
import argparse
import hashlib
import json
import random
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'host'))
from nodelift.native import Native, library_path

def digest(path):
    with open(path,'rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

parser=argparse.ArgumentParser()
parser.add_argument('--target',type=Path,default=ROOT/'.models/qwen2.5-1.5b-instruct-q4_k_m.gguf')
parser.add_argument('--draft',type=Path,default=ROOT/'.models/qwen2.5-0.5b-instruct-q4_k_m.gguf')
parser.add_argument('--prompt-manifest',type=Path,default=ROOT/'research/measurements/engine-control-pilot/manifest.json')
parser.add_argument('--draft-widths',type=int,nargs='+',default=[4])
parser.add_argument('--repetitions',type=int,default=2)
parser.add_argument('--tokens',type=int,default=64)
parser.add_argument('--output',default=str(ROOT/'research/measurements/upstream-control-pilot'))
args=parser.parse_args()
folder=Path(args.output);folder.mkdir(parents=True,exist_ok=True)
target=args.target.resolve()
draft=args.draft.resolve()
binary=ROOT/'.deps/llama.cpp/build/bin/llama-server'
prompts=json.loads(args.prompt_manifest.read_text())['prompts']
with Native() as engine:
    engine.call('load',path=str(target),n_ctx=2048,threads=8,gpu_layers=999)
    prefixes=[engine.call('tokenize',text=p,chat=True)['tokens'] for p in prompts]
manifest={'llama_commit':(ROOT/'native/llama.lock').read_text().strip(),'server_sha256':digest(binary),
          'native_tokenizer_sha256':digest(library_path()),'target_sha256':digest(target),'draft_sha256':digest(draft),
          'prompts':prompts,'prompt_token_ids':prefixes,'max_tokens':args.tokens,'repetitions':args.repetitions,
          'draft_widths':args.draft_widths,'source_sha256':digest(Path(__file__)),'seed':20261031,'started':time.time(),'limitations':['selected target/draft pair only',
          'arm order randomized in blocks; process/model restarted per arm',
          'warm request wall time includes HTTP; excludes model load',
          'EOS respected; not all requests generate the full token budget',
          'best-local candidates for this pair, not an exhaustive optimized-runtime search', 'output equality assessed within upstream path; cross-harness timing is not a paired speedup']}
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

def request(path,value=None):
    payload=json.dumps(value).encode() if value is not None else None
    req=urllib.request.Request('http://127.0.0.1:19869'+path,data=payload,
                               headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as response:return json.load(response)

assert all(1<=k<=16 for k in args.draft_widths)
arms=[('none',4)]+[(mode,k) for mode in ('draft-simple','ngram-mod') for k in args.draft_widths];rng=random.Random(20261031);rows=[]
with (folder/'runs.jsonl').open('w') as output:
    for repetition in range(args.repetitions):
        order=arms[:];rng.shuffle(order)
        for spec,k in order:
            arm=spec if spec=='none' else spec+'-k'+str(k)
            command=[str(binary),'-m',str(target),'-ngl','999','-c','2048','-b','512','-ub','512',
                     '-t','8','-tb','8','-fa','on','--parallel','1','--host','127.0.0.1','--port','19869',
                     '--spec-type',spec,'--spec-draft-n-max',str(k),'--no-context-shift','--no-webui']
            if spec=='draft-simple':command+=['-md',str(draft),'-ngld','999','-td','8','--spec-draft-p-min','0']
            with (ROOT/'artifacts'/f'upstream-{repetition}-{arm}.log').open('w') as log:
                process=subprocess.Popen(command,stdout=log,stderr=log)
                try:
                    deadline=time.monotonic()+90
                    while True:
                        if process.poll() is not None:raise RuntimeError('upstream server exited; inspect artifact log')
                        try:
                            if request('/health').get('status')=='ok':break
                        except (OSError,ValueError):pass
                        if time.monotonic()>deadline:raise TimeoutError('upstream startup')
                        time.sleep(.2)
                    def payload(index,count):
                        return {'prompt':prefixes[index],'n_predict':count,'temperature':0,'top_k':1,'top_p':1,
                                'min_p':0,'repeat_penalty':1,'frequency_penalty':0,'presence_penalty':0,
                                'cache_prompt':False,'return_tokens':True,'stream':False,'seed':0}
                    request('/completion',payload(0,16))
                    indices=list(range(len(prompts)));rng.shuffle(indices)
                    for index in indices:
                        started=time.perf_counter()
                        result=request('/completion',payload(index,args.tokens))
                        row={'arm':arm,'repetition':repetition,'prompt_id':index,
                             'request_wall_seconds':time.perf_counter()-started,'tokens':result.get('tokens'),
                             'content':result.get('content'),'timings':result.get('timings'),
                             'stop_type':result.get('stop_type'),'tokens_predicted':result.get('tokens_predicted'),
                             'truncated':result.get('truncated'),'timestamp':time.time()}
                        rows.append(row);output.write(json.dumps(row,ensure_ascii=False)+'\n');output.flush()
                        print(arm,repetition,index,round(row['request_wall_seconds'],4),len(row['tokens'] or []),flush=True)
                finally:
                    process.terminate()
                    try:process.wait(timeout=10)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
    baseline={(r['repetition'],r['prompt_id']):r for r in rows if r['arm']=='none'}
    summary=[]
    for spec,k in arms[1:]:
        arm=spec+'-k'+str(k)
        comparisons=[]
        for row in rows:
            if row['arm']!=arm:continue
            base=baseline[(row['repetition'],row['prompt_id'])]
            comparisons.append({'repetition':row['repetition'],'prompt_id':row['prompt_id'],
                                'exact_tokens':row['tokens']==base['tokens'],
                                'wall_speedup':base['request_wall_seconds']/row['request_wall_seconds']})
        summary.append({'arm':arm,'comparisons':comparisons,
                        'all_tokens_equal':all(r['exact_tokens'] for r in comparisons),
                        'median_paired_wall_speedup':statistics.median(r['wall_speedup'] for r in comparisons)})
    (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(folder/'hashes.json').write_text(json.dumps({p.name:digest(p) for p in folder.iterdir() if p.is_file() and p.name!='hashes.json'},indent=2)+'\n')
print(json.dumps(summary),flush=True)
