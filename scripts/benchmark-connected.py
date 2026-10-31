"""Paired physical-node experiment on a running host. Refuses offline/legacy nodes.

Uses public fixture prompts only; output omits credentials, node IDs and model paths.
No performance result is written when the readiness gate fails.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import statistics
import subprocess
import time
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
PROMPTS=[
    'Write a Python function returning unique list elements in their original order.',
    'Spiega in italiano la differenza tra capacità RAM e larghezza di banda della memoria.',
    'Compare Wi-Fi and a wired local connection for cooperative inference. Use three brief points.',
    'Compute 17 times 23 and explain the arithmetic briefly.',
]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--node',help='paired node ID; omitted selects the only ready native node')
parser.add_argument('--port',type=int,default=9868)
parser.add_argument('--state-dir',type=Path,default=Path.home()/'.local/share/nodelift')
parser.add_argument('--output',type=Path,default=ROOT/'artifacts/connected-benchmark')
parser.add_argument('--tokens',type=int,choices=range(16,513),default=128,metavar='16..512')
parser.add_argument('--repetitions',type=int,choices=range(1,11),default=3,metavar='1..10')
parser.add_argument('--draft-k',type=int,choices=range(1,17),default=4,metavar='1..16')
parser.add_argument('--remote-timeout-ms',type=int,default=30000)
parser.add_argument('--topology',required=True,help='explicit wiring/hotspot description recorded with the run')
args=parser.parse_args()
if not 1<=args.port<=65535 or not 500<=args.remote_timeout_ms<=60000:parser.error('invalid port or remote timeout')
token=os.environ.get('NODELIFT_ADMIN_TOKEN','')
if not token:
    found=re.findall(r'http://127\.0\.0\.1:'+str(args.port)+r'/#([A-Za-z0-9_-]+)',(args.state_dir/'host-session.log').read_text())
    if not found:raise SystemExit('No local administrator session; supply NODELIFT_ADMIN_TOKEN privately.')
    token=found[-1]
def api(path,body=None):
    req=urllib.request.Request(f'http://127.0.0.1:{args.port}'+path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=15) as response:return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(json.loads(error.read()).get('error',f'HTTP {error.code}')) from None
def peer():
    return next((n for n in api('/admin/status')['nodes'] if n['id']==args.node),None)
def observation(node):
    if not node:return {'online':False}
    caps=node.get('capabilities',{})
    keep=('model','os','app_version','thermal','transport','lifecycle','battery_percent',
          'physical_memory_bytes','available_memory_bytes','process_memory_bytes','cpu_cores',
          'engine_ready','draft_sha256','tokenizer_fingerprint')
    return {'online':node['online'],'capabilities':{k:caps[k] for k in keep if k in caps}}
ready=[n for n in api('/admin/status')['nodes'] if n['online'] and n['capabilities'].get('engine_ready')]
if args.node:ready=[n for n in ready if n['id']==args.node]
if len(ready)!=1:raise SystemExit('Need exactly one selected online native draft node. Update/open the companion and load its draft first; no benchmark was run.')
args.node=ready[0]['id']
engine=api('/admin/engine/status')
if engine['busy']:raise SystemExit('Engine already busy; existing work was left untouched.')
if not engine['config']['target_model'] or not engine['config']['draft_model']:raise SystemExit('Configure a target and matching draft in the dashboard first.')
args.output.mkdir(parents=True,exist_ok=False)
plan=[(prompt,rep,mode) for prompt in range(len(PROMPTS)) for rep in range(args.repetitions)
      for mode in ('host','local_draft','remote_draft')]
random.Random(20261031).shuffle(plan)
manifest={'scope':'connected physical-node experiment; telemetry is self-reported',
          'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'topology':args.topology,'initial_node':observation(ready[0]),'prompts':PROMPTS,
          'plan':plan,'tokens_max':args.tokens,'draft_k':args.draft_k,'remote_timeout_ms':args.remote_timeout_ms,
          'sampling':'greedy, EOS respected','started':time.time(),
          'limitations':['shared desktop activity not instrumented','self-reported thermal state, no power meter',
                         'full-prefix native recovery; warmup recorded separately, not included in paired results']}
(args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
active=None
def run(prompt,mode):
    global active
    before=observation(peer());begin=time.perf_counter()
    active=api('/admin/engine/run',{'prompt':prompt,'mode':mode,'node_id':args.node,
               'max_tokens':args.tokens,'draft_k':args.draft_k,'remote_timeout_ms':args.remote_timeout_ms})['run_id']
    deadline=time.monotonic()+600
    while True:
        status=api('/admin/engine/status')
        value=next((r for r in status['runs'] if r['id']==active),None)
        if value and value['status'] in ('completed','failed','cancelled'):
            # Wait for persistence/teardown before starting the next controlled run.
            if not status['busy']:break
        if time.monotonic()>deadline:raise TimeoutError('connected run deadline exceeded')
        time.sleep(.05)
    active=None;value['client_wall_ms']=(time.perf_counter()-begin)*1000
    value.pop('node_id',None);value['node_before']=before;value['node_after']=observation(peer())
    for key in ('target_model','draft_model'):
        if 'identity' in value:value['identity']['config'][key]=Path(value['identity']['config'][key]).name
    return value
rows=[]
try:
    warm=[]
    for mode in ('host','local_draft','remote_draft'):
        value=run('Say hello briefly.',mode);warm.append(value)
        (args.output/'warmup.json').write_text(json.dumps(warm,indent=2)+'\n')
        if value['status']!='completed' or value['metrics'].get('fallbacks',0):raise RuntimeError('Warmup failed/fell back; inspect the saved evidence before benchmarking.')
    with (args.output/'runs.jsonl').open('w') as output:
        for i,(prompt,rep,mode) in enumerate(plan):
            try:value=run(PROMPTS[prompt],mode)
            except RuntimeError as error:value={'mode':mode,'status':'failed','error':str(error),'metrics':{}}
            value.update(prompt_id=prompt,repetition=rep);rows.append(value)
            output.write(json.dumps(value,ensure_ascii=False)+'\n');output.flush()
            print(f'{i+1}/{len(plan)} {mode}: {value["status"]}',flush=True)
    baselines={(r['prompt_id'],r['repetition']):r for r in rows if r['mode']=='host'}
    comparisons=[]
    for r in rows:
        if r['mode']=='host':continue
        baseline=baselines[(r['prompt_id'],r['repetition'])]
        valid=r['status']==baseline['status']=='completed'
        comparisons.append({'mode':r['mode'],'prompt_id':r['prompt_id'],'repetition':r['repetition'],
                            'both_completed':valid,'exact_tokens':valid and r['tokens']==baseline['tokens'],
                            'fallbacks':r['metrics'].get('fallbacks'),
                            'speedup':baseline['metrics']['elapsed_seconds']/r['metrics']['elapsed_seconds'] if valid else None})
    summary={'comparisons':comparisons,'failed_runs':sum(r['status']!='completed' for r in rows),
             'median_speedup':{m:statistics.median([c['speedup'] for c in comparisons if c['mode']==m and c['speedup'] is not None])
                               if any(c['mode']==m and c['speedup'] is not None for c in comparisons) else None
                               for m in ('local_draft','remote_draft')}}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
finally:
    if active:api('/admin/engine/stop',{'run_id':active})
    files=[p for p in args.output.iterdir() if p.is_file() and p.name!='hashes.json']
    (args.output/'hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
