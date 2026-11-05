"""Descriptive diagnostics only: three workloads cannot qualify general acceleration."""
from pathlib import Path
import json,statistics,hashlib
from simulate import pipeline
P=Path(__file__).resolve().parent;ROOT=P.parents[1];A=ROOT/'artifacts/five-cases-2026-11-05'
def readlines(path):return [json.loads(x) for x in path.read_text().splitlines()]
def med(v):return statistics.median(v)
def main():
 result=dict(scope='Bounded diagnostics, no general or physical-device acceleration claim',envelope={},accounting={},quality={},simulation={})
 for precision in ['native','fp32']:
  rows=readlines(A/f'envelope-{precision}'/'runs.jsonl');base={(r['prompt_id'],r['rep']):r for r in rows if r['width']==1};group={}
  for width in [1,2,4,8]:
   subset=[r for r in rows if r['width']==width]
   group[width]=dict(runs=len(subset),exact=sum(r['exact'] for r in subset),median_request_ratio=med(base[(r['prompt_id'],r['rep'])]['seconds']/r['seconds'] for r in subset),median_decode_ratio=med(base[(r['prompt_id'],r['rep'])]['decode_seconds']/r['decode_seconds'] for r in subset),median_ttft_delta_ms=med(1000*(r['ttft_seconds']-base[(r['prompt_id'],r['rep'])]['ttft_seconds']) for r in subset),per_prompt={p:dict(exact=all(r['exact'] for r in subset if r['prompt_id']==p),median_request_ratio=med(base[(r['prompt_id'],r['rep'])]['seconds']/r['seconds'] for r in subset if r['prompt_id']==p)) for p in sorted({r['prompt_id'] for r in subset})})
  result['envelope'][precision]=group
  if precision=='fp32':
   simulations=[]
   for dms in [0,1,5,10,25,50]:
    for nms in [0,2,10,50,100]:
     ratios=[]
     for r in rows:
      if r['width']!=8 or not r['exact']:continue
      s=pipeline(r['blocks'],dms/1000,nms/1000);ratios.append(base[(r['prompt_id'],r['rep'])]['seconds']/(r['prefill_seconds']+s['decode_seconds']))
     simulations.append(dict(producer_ms_per_token=dms,delivery_ms_per_block=nms,median_ratio=med(ratios),minimum_ratio=min(ratios),maximum_ratio=max(ratios),paired_runs=len(ratios)))
   result['simulation']=dict(scope='FP32 width 8, perfect continuing candidates, separate resources, one pending block, no draft startup, rejection, host contention or resynchronization. Hypothetical costs, not phone measurements.',grid=simulations)
 path=A/'accounting/runs.jsonl'
 if path.exists():
  rows=readlines(path);base={(r['prompt_id'],r['rep']):r for r in rows if r['arm']=='host'}
  for arm in ['old-adaptive','charged']:
   subset=[r for r in rows if r['arm']==arm]
   result['accounting'][arm]=dict(runs=len(subset),exact=sum(r['tokens']==base[(r['prompt_id'],r['rep'])]['tokens'] and r['finish']==base[(r['prompt_id'],r['rep'])]['finish'] for r in subset),disabled=sum(r['disabled'] for r in subset),median_request_ratio=med(base[(r['prompt_id'],r['rep'])]['seconds']/r['seconds'] for r in subset),median_ttft_delta_ms=med(1000*(r['ttft_seconds']-base[(r['prompt_id'],r['rep'])]['ttft_seconds']) for r in subset),median_request_seconds=med(r['seconds'] for r in subset),median_draft_prefill_seconds=med(r['telemetry']['draft_prefill_seconds'] for r in subset) if arm=='charged' else None)
  charged=[r for r in rows if r['arm']=='charged'];result['accounting']['balance']=dict(nonnegative_residuals=all(r['unattributed_seconds']>=0 for r in charged),max_residual_seconds=max(r['unattributed_seconds'] for r in charged),median_residual_seconds=med(r['unattributed_seconds'] for r in charged))
  old={(r['prompt_id'],r['rep']):r for r in rows if r['arm']=='old-adaptive'}
  result['accounting']['identical_k_trajectories']=sum([v['k'] for v in r['trace']]==[v['k'] for v in old[(r['prompt_id'],r['rep'])]['trace']] for r in charged)
 for monitor in sorted(A.glob('monitor-*')):
  if not (monitor/'completion.json').exists():continue
  samples=readlines(monitor/'resources.jsonl');result['quality'][monitor.name]=dict(completion=json.loads((monitor/'completion.json').read_text()),samples=len(samples),cpu_min=min(s['cpu_percent'] for s in samples),cpu_max=max(s['cpu_percent'] for s in samples),thermal_states=sorted({s['thermal'] for s in samples}),low_power_values=sorted({s['low_power_mode'] for s in samples}),available_min_GiB=min(s['available_bytes'] for s in samples)/2**30,swap_used_start_GiB=samples[0]['swap_used_bytes']/2**30,swap_used_end_GiB=samples[-1]['swap_used_bytes']/2**30,isolated_qualification=False)
 (P/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
