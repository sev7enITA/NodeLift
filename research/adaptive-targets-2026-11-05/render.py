"""Render measured pairs; screening and held-out validation stay visibly separate."""
from pathlib import Path
import json, statistics
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P = Path(__file__).resolve().parent
s = json.loads((P/'results/summary.json').read_text())
pairs = json.loads((P/'results/validation-pairs.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig, axes = plt.subplots(2, 2, figsize=(14, 10), layout='constrained')
native = s['screening']['14B-screen']
fp32 = s['screening']['14B-fp32-screen']
labels = [r['arm'].replace('Qwen3-','').replace('-MLX-4bit-', ' / ') for r in native]
y = np.arange(len(labels))
axes[0,0].barh(y-.18,[r['median_paired_speed_ratio'] for r in native],height=.35,color='#e79755',label='Native: every arm only 2/3 exact')
axes[0,0].barh(y+.18,[r['median_paired_speed_ratio'] for r in fp32],height=.35,color='#527da5',label='FP32: every arm 3/3 exact')
axes[0,0].set_yticks(y, labels);axes[0,0].invert_yaxis();axes[0,0].axvline(1,color='black',lw=1)
axes[0,0].set(xlabel='Host elapsed / candidate elapsed (>1 is faster)',title='SCREENING ONLY: speed does not establish equivalence')
axes[0,0].legend(fontsize=8,loc='lower left')
summaries=s['validation']['14B-fp32'];colors=['#527da5','#8f64b1']
names=list(summaries[0]['workload_median_ratios']);y=np.arange(len(names))
for i,(arm,col) in enumerate(zip(summaries,colors)):
 label='Adaptive' if 'adaptive' in arm['arm'] else 'Fixed k=2'
 axes[0,1].barh(y+(i-.5)*.35,[arm['workload_median_ratios'][p] for p in names],height=.35,color=col,label=label)
axes[0,1].set_yticks(y,names);axes[0,1].invert_yaxis();axes[0,1].axvline(1,color='black',lw=1)
axes[0,1].set(xlabel='Median paired speed ratio, four repeats per workload',title='HELD-OUT: 14B FP32, draft 0.6B');axes[0,1].legend()
for i,(arm,col) in enumerate(zip(summaries,colors)):
 r=[x for x in pairs if x['arm']==arm['arm']];label='Adaptive' if 'adaptive' in arm['arm'] else 'Fixed k=2'
 x=np.array([v['speed_ratio'] for v in r]);axes[1,0].scatter(x,np.full(len(x),i),s=20,alpha=.55,color=col)
 lo,hi=arm['workload_bootstrap_95_interval'];mid=arm['median_workload_speed_ratio']
 axes[1,0].errorbar(mid,i,yerr=None,xerr=[[mid-lo],[hi-mid]],fmt='D',color='black',capsize=5)
 axes[1,1].barh(i,1000*arm['median_ttft_change_seconds'],color=col)
axes[1,0].set_yticks([0,1],['Adaptive','Fixed k=2']);axes[1,0].axvline(1,color='black',lw=1)
axes[1,0].set_ylim(-.6,1.6)
axes[1,0].set(xlabel='Paired ratios; diamond: workload median and 95% cluster bootstrap',title='Repeatability: eight workloads, not 32 independent samples')
axes[1,1].set_yticks([0,1],['Adaptive','Fixed k=2']);axes[1,1].axvline(0,color='black',lw=1)
axes[1,1].set(xlabel='Median candidate TTFT minus host TTFT (ms, >0 is worse)',title='First-token cost includes speculative startup')
fig.suptitle('NodeLift | Adaptive speculation: no qualified acceleration\nSame model within each arithmetic lane. Shared Mac with background load; no distributed or energy claim.',fontsize=15)
for ext in ['png','svg']:fig.savefig(P/f'adaptive-results.{ext}',dpi=160)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(14,5),layout='constrained')
adaptive=[r for r in pairs if 'adaptive' in r['arm']]
names=sorted({r['prompt'] for r in adaptive});y=np.arange(len(names));left=np.zeros(len(names))
for key,label,col in [('draft_seconds','Measured draft steps','#8f64b1'),('verify_seconds','Target steps (includes serial fallback)','#527da5'),('unattributed_seconds','Residual: prefill, setup and other work','#d8ad57')]:
 values=np.array([statistics.mean(r[key] for r in adaptive if r['prompt']==p) for p in names])
 axes[0].barh(y,values,left=left,label=label,color=col);left+=values
axes[0].set_yticks(y,names);axes[0].invert_yaxis();axes[0].set(xlabel='Mean seconds across four repeats (additive)',title='Adaptive wall-time accounting');axes[0].legend(fontsize=8)
drafted=np.array([statistics.mean(r['drafted_tokens'] for r in adaptive if r['prompt']==p) for p in names])
discard=np.array([statistics.mean(r['discarded_or_unemitted_tokens'] for r in adaptive if r['prompt']==p) for p in names])
axes[1].barh(y,drafted-discard,color='#527da5',label='Accepted and emitted')
axes[1].barh(y,discard,left=drafted-discard,color='#d8ad57',label='Discarded or not emitted before stop')
axes[1].set_yticks(y,names);axes[1].invert_yaxis();axes[1].set(xlabel='Mean draft tokens across four repeats',title='Work kept and work discarded');axes[1].legend(fontsize=8)
fig.suptitle('NodeLift | Cost visibility, including fallback\nPhase boundaries synchronize MLX. Residual is not labelled as network, energy or pure compute.',fontsize=14)
for ext in ['png','svg']:fig.savefig(P/f'adaptive-costs.{ext}',dpi=160)
