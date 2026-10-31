"""Randomized interleaved real-weight A/B; baseline lives in a frozen private copy.

Two persistent worker processes retain the same model pair. Calls are serialized
so they do not compete for the GPU. Public output uses only the fixed prompts
below and model basenames. This is a small-model host study, never phone evidence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import select
import statistics
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
PROMPTS=[
    'Write a Python function that returns the unique elements of a list in their original order.',
    'Explain in Italian why network latency matters when computers collaborate. Use three brief points.',
    'Return a JSON object describing a fictional book: title, author, year, and three keywords.',
    'Compute 17 times 23. Explain the arithmetic briefly.',
    'Complete this pattern with ten more terms: 2, 4, 8, 16,',
    'Write a concise comparison of RAM capacity and memory bandwidth.',
    'Output this exact line eight times, with no other text: The local computer verifies every proposed token.',
    'Copy the following text exactly, without commentary: amber birch cedar delta ember forest garden harbor amber birch cedar delta ember forest garden harbor amber birch cedar delta ember forest garden harbor amber birch cedar delta ember forest garden harbor',
]
VARIANTS={
    'baseline_host':('baseline','host','fixed'),
    'baseline_draft':('baseline','local_draft','fixed'),
    'optimized_host':('candidate','host','fixed'),
    'optimized_draft':('candidate','local_draft','fixed'),
    'adaptive_draft':('candidate','local_draft','adaptive'),
    'lookup':('candidate','lookup','fixed'),
    'adaptive_lookup':('candidate','lookup','adaptive'),
}


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def worker(args):
    sys.path.insert(0,str(args.baseline/'host' if args.worker=='baseline' else ROOT/'host'))
    import nodelift.engine as module
    import nodelift.native as native
    from nodelift.state import State
    module.ROOT=native.ROOT=ROOT
    os.environ['NODELIFT_LIBRARY']=str(args.baseline/'libnodelift-baseline.dylib' if args.worker=='baseline' else ROOT/'native/build/host/lib/libnodelift.dylib')
    with tempfile.TemporaryDirectory(prefix='nodelift-optimization-') as folder:
        engine=module.Controller(State(Path(folder)))
        engine.configure({'target_model':str(args.target.resolve()),'draft_model':str(args.draft.resolve()),
                          'n_ctx':2048,'threads':8,'gpu_layers':999})
        try:
            for line in sys.stdin:
                request=json.loads(line)
                if request.get('shutdown'):break
                engine.start(request)
                deadline=time.monotonic()+120
                while engine.busy:
                    if time.monotonic()>deadline:engine.stop();raise TimeoutError('worker run deadline')
                    time.sleep(.002)
                run=engine.status()['runs'][0]
                for field in ('target_model','draft_model'):
                    if 'identity' in run:run['identity']['config'][field]=Path(run['identity']['config'][field]).name
                print(json.dumps(run,ensure_ascii=False),flush=True)
        finally:
            for model in (engine.target,engine.draft):
                if model:model.close()


def summarize(rows):
    indexed={(r['prompt_id'],r['repetition'],r['variant']):r for r in rows}
    summaries={}
    for group,ids in [('all',range(8)),('general',range(6)),('repetition',range(6,8))]:
        summaries[group]={}
        for variant in VARIANTS:
            selected=[r for r in rows if r['variant']==variant and r['prompt_id'] in ids]
            comparisons=[]
            for row in selected:
                peers={v:indexed[(row['prompt_id'],row['repetition'],v)] for v in ('baseline_host','optimized_host','baseline_draft')}
                item={'prompt_id':row['prompt_id'],'repetition':row['repetition'],'completed':row['status']=='completed',
                      'output_tokens':len(row.get('tokens',[]))}
                item['exact_tokens']=item['completed'] and peers['baseline_host']['status']=='completed' and row['tokens']==peers['baseline_host']['tokens']
                for name,base in peers.items():
                    # An output mismatch is retained in the denominator, but
                    # must never enter a same-output speedup distribution.
                    if item['completed'] and base['status']=='completed' and row['tokens']==base['tokens']:
                        item['speedup_vs_'+name]=base['metrics']['elapsed_seconds']/row['metrics']['elapsed_seconds']
                comparisons.append(item)
            summaries[group][variant]={'runs':len(selected),'completed':sum(c['completed'] for c in comparisons),
                'all_tokens_equal':bool(comparisons) and all(c['exact_tokens'] for c in comparisons),
                'exact_pairs':sum(c['exact_tokens'] for c in comparisons),
                'median_ttft_ms':statistics.median([r['metrics']['ttft_ms'] for r in selected if r['status']=='completed']) if any(r['status']=='completed' for r in selected) else None,
                'comparisons':comparisons}
            for base in ('baseline_host','optimized_host','baseline_draft'):
                values=[c['speedup_vs_'+base] for c in comparisons if 'speedup_vs_'+base in c]
                summaries[group][variant]['speedup_pair_count_vs_'+base]=len(values)
                summaries[group][variant]['median_speedup_vs_'+base]=statistics.median(values) if values else None
    return summaries


def main(args):
    if args.output.exists():raise SystemExit('Output exists; use a new path to preserve previous evidence')
    args.output.mkdir(parents=True)
    plan=[(p,r,v) for p in range(len(PROMPTS)) for r in range(args.repetitions) for v in VARIANTS]
    random.Random(args.seed).shuffle(plan)
    sources=[Path(__file__),ROOT/'host/nodelift/engine.py',ROOT/'host/nodelift/native.py',ROOT/'host/nodelift/scheduling.py',ROOT/'native/core.cpp',ROOT/'native/llama.lock']
    manifest={'started_unix':time.time(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain','--','host','native','scripts'],cwd=ROOT,text=True).strip()),
              'dirty_check_scope':['host','native','scripts'],
              'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sources},
              'baseline':json.loads((args.baseline/'manifest.json').read_text()),
              'candidate_library_sha256':digest(ROOT/'native/build/host/lib/libnodelift.dylib'),
              'models':{p.name:digest(p) for p in (args.target,args.draft)},
              'prompts':PROMPTS,'variants':VARIANTS,'plan':plan,'seed':args.seed,'tokens_max':args.tokens,'draft_k':4,
              'timing':'Paired elapsed_seconds includes prefill, proposal, verification, text decoding and intervening publication; model load excluded. request_total_ms retained separately.',
              'limitations':['small control models on one M3 Max/Metal host','no physical phone','resident baseline/candidate models; GPU calls serialized','no thermal isolation or cross-device generalization','general prompts reused from the earlier pilot; separate repetition subgroup; no pooling of subgroup claims','adaptive thresholds frozen before this run; no calibrated confidence claim']}
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    workers={};logs=[];rows=[]
    def request(kind,payload):
        process=workers[kind];process.stdin.write(json.dumps(payload)+'\n');process.stdin.flush()
        if not select.select([process.stdout],[],[],150)[0]:raise TimeoutError('worker response deadline')
        line=process.stdout.readline()
        if not line:raise RuntimeError('worker exited; inspect private log')
        return json.loads(line)
    try:
        for kind in ('baseline','candidate'):
            log=(ROOT/'artifacts'/f'optimization-{kind}.log').open('w');logs.append(log)
            workers[kind]=subprocess.Popen([sys.executable,str(Path(__file__)), '--worker',kind,'--baseline',str(args.baseline),
                                           '--target',str(args.target),'--draft',str(args.draft)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                          stderr=log,text=True,bufsize=1)
            warm=request(kind,{'prompt':'Say hello briefly.','mode':'local_draft','max_tokens':16,'draft_k':4})
            if warm['status']!='completed':raise RuntimeError(warm.get('error','warmup failed'))
        with (args.output/'runs.jsonl').open('w') as out:
            for index,(p,repetition,variant) in enumerate(plan):
                kind,mode,policy=VARIANTS[variant]
                run=request(kind,{'prompt':PROMPTS[p],'mode':mode,'draft_policy':policy,'max_tokens':args.tokens,'draft_k':4})
                run.update(prompt_id=p,repetition=repetition,variant=variant)
                rows.append(run);out.write(json.dumps(run,ensure_ascii=False)+'\n');out.flush()
                print(f'{index+1}/{len(plan)} {variant} p{p} r{repetition}: {run["status"]} {len(run.get("tokens",[]))} tokens',flush=True)
        summary=summarize(rows)
        (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps({group:{v:round(s['median_speedup_vs_baseline_host'],3) if s['median_speedup_vs_baseline_host'] is not None else None for v,s in variants.items()}
                          for group,variants in summary.items()},indent=2))
        if not all(r['status']=='completed' for r in rows):raise RuntimeError('failed runs retained')
        if not all(s['all_tokens_equal'] for s in summary['all'].values()):raise RuntimeError('token mismatch retained; inspect before any performance claim')
    finally:
        for process in workers.values():
            if process.poll() is None:
                try:process.stdin.write('{"shutdown":true}\n');process.stdin.flush();process.wait(timeout=10)
                except (OSError,subprocess.TimeoutExpired):process.kill();process.wait()
        for log in logs:log.close()
        files=[p for p in args.output.iterdir() if p.is_file() and p.name!='hashes.json']
        (args.output/'hashes.json').write_text(json.dumps({p.name:digest(p) for p in files},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',choices=['baseline','candidate'])
    parser.add_argument('--baseline',type=Path,default=ROOT/'artifacts/optimization-baseline')
    parser.add_argument('--target',type=Path,default=ROOT/'.models/qwen2.5-1.5b-instruct-q4_k_m.gguf')
    parser.add_argument('--draft',type=Path,default=ROOT/'.models/qwen2.5-0.5b-instruct-q4_k_m.gguf')
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/optimization-pilot')
    parser.add_argument('--tokens',type=int,default=96)
    parser.add_argument('--repetitions',type=int,default=2)
    parser.add_argument('--seed',type=int,default=20261031)
    args=parser.parse_args()
    if not 1<=args.tokens<=512 or not 1<=args.repetitions<=10:parser.error('tokens 1..512, repetitions 1..10')
    worker(args) if args.worker else main(args)
