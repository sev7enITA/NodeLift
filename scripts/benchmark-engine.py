"""Real-weight paired pilot. Same prompts/output budgets; keeps mismatches and failures."""
import argparse
import hashlib
import json
import random
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'host'))
from nodelift.engine import Controller
from nodelift.state import State
from nodelift.native import library_path

PROMPTS=[
    'Write a Python function that returns the unique elements of a list in their original order.',
    'Explain in Italian why network latency matters when computers collaborate. Use three brief points.',
    'Return a JSON object describing a fictional book: title, author, year, and three keywords.',
    'Compute 17 times 23. Explain the arithmetic briefly.',
    'Complete this pattern with ten more terms: 2, 4, 8, 16,',
    'Write a concise comparison of RAM capacity and memory bandwidth.',
]
parser=argparse.ArgumentParser()
parser.add_argument('--target',default=str(ROOT/'.models/qwen2.5-1.5b-instruct-q4_k_m.gguf'))
parser.add_argument('--draft',default=str(ROOT/'.models/qwen2.5-0.5b-instruct-q4_k_m.gguf'))
parser.add_argument('--output',default=str(ROOT/'research/measurements/engine-control-pilot'))
parser.add_argument('--repetitions',type=int,default=2)
parser.add_argument('--tokens',type=int,default=64)
args=parser.parse_args();folder=Path(args.output);folder.mkdir(parents=True,exist_ok=True)
plan=[(p,rep,mode,k) for p in range(len(PROMPTS)) for rep in range(args.repetitions) for mode,k in [('host',1),('local_draft',1),('local_draft',4),('local_draft',8),('local_draft',16)]]
random.Random(20261031).shuffle(plan)
manifest={'purpose':'Exploratory small-model pipeline pilot; not best-local/frontier benchmark','seed':20261031,'prompts':PROMPTS,'tokens_max':args.tokens,'repetitions':args.repetitions,'plan':plan,'started':time.time(),'sampling':'greedy; EOS respected; actual output counts retained','modes':['host','local_draft'],'limitations':['single host session','small control models','no upstream best-local baseline yet','no mobile inference in this run','draft remains resident after its first load; concurrent GPU workloads not instrumented']}
manifest['limitations'][2]='upstream comparisons are a separate benchmark with a different timing path'
manifest['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
manifest['working_tree_dirty']=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
manifest['native_library_sha256']=hashlib.sha256(library_path().read_bytes()).hexdigest()
manifest['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                           [Path(__file__),ROOT/'host/nodelift/engine.py',ROOT/'host/nodelift/native.py',ROOT/'native/core.cpp',ROOT/'native/core.h',ROOT/'native/llama.lock']}
manifest['timing']='elapsed_seconds includes prefill and delta detokenization; per-token rate excludes prefill; neither includes initial load'
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with tempfile.TemporaryDirectory(prefix='nodelift-bench-') as state:
    engine=Controller(State(Path(state)))
    engine.configure({'target_model':str(Path(args.target).resolve()),'draft_model':str(Path(args.draft).resolve()),'n_ctx':2048,'threads':8,'gpu_layers':999})
    # Explicit unreported warmup compiles GPU kernels and loads both models.
    engine.start({'prompt':'Say hello briefly.','mode':'local_draft','max_tokens':16,'draft_k':4})
    while engine.busy:time.sleep(.05)
    if engine.runs[-1]['status']!='completed':raise RuntimeError(engine.runs[-1])
    rows=[]
    with (folder/'runs.jsonl').open('w') as output:
        for i,(p,rep,mode,k) in enumerate(plan):
            engine.start({'prompt':PROMPTS[p],'mode':mode,'max_tokens':args.tokens,'draft_k':k})
            deadline=time.monotonic()+180
            while engine.busy:
                if time.monotonic()>deadline:engine.stop();raise TimeoutError('benchmark deadline')
                time.sleep(.05)
            run=engine.status()['runs'][0]
            run.update(prompt_id=p,repetition=rep)
            if 'identity' in run:
                for key in ('target_model','draft_model'):
                    run['identity']['config'][key]=Path(run['identity']['config'][key]).name
            rows.append(run);output.write(json.dumps(run,ensure_ascii=False)+'\n');output.flush()
            print(f'{i+1}/{len(plan)} {mode} k={k} {run["status"]} '+str(run['metrics']),flush=True)
    by_pair={(r['prompt_id'],r['repetition']):r for r in rows if r['mode']=='host'}
    summary=[]
    for k in (1,4,8,16):
        selected=[r for r in rows if r['mode']=='local_draft' and r['draft_k']==k]
        compared=[]
        for row in selected:
            base=by_pair[(row['prompt_id'],row['repetition'])]
            if row['status']=='completed' and base['status']=='completed':
                compared.append({'prompt':row['prompt_id'],'repetition':row['repetition'],'exact_tokens':row['tokens']==base['tokens'],
                                 'speedup_end_to_end':base['metrics']['elapsed_seconds']/row['metrics']['elapsed_seconds']})
        summary.append({'k':k,'runs':len(selected),'completed':len(compared),'comparisons':compared,
                        'all_tokens_equal':bool(compared) and all(c['exact_tokens'] for c in compared),
                        'median_paired_speedup':statistics.median(c['speedup_end_to_end'] for c in compared) if compared else None})
    (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('SUMMARY',json.dumps(summary),flush=True)
    for native in (engine.target,engine.draft):
        if native:native.close()
files=[p for p in folder.iterdir() if p.is_file() and p.name!='hashes.json']
(folder/'hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
