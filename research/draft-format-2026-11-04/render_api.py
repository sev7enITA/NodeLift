from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent;v=json.loads((P/'results/api-control/summary.json').read_text());rows=v['by_prompt']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(11,5.3),facecolor='#f8fafc');ax.set_facecolor('#f8fafc');x=np.arange(6);y=[r['median_ratio'] for r in rows]
ax.bar(x,y,color=['#087f8c' if r['candidate_for_new_heldout_trials'] else '#94a3b8' for r in rows],width=.6)
ax.errorbar(x,y,yerr=[[r['median_ratio']-r['min_ratio'] for r in rows],[r['max_ratio']-r['median_ratio'] for r in rows]],fmt='none',capsize=5,color='#334155')
for i,r in enumerate(rows):ax.text(i,r['max_ratio']+.025,f"{r['median_ratio']:.2f}x",ha='center',fontweight='bold')
ax.axhline(1,color='#111827',linestyle='--');ax.set_xticks(x,['Unique list','Epoch','TTFT','JSON','Queue','Memory']);ax.set_ylabel('Upstream greedy time / upstream assisted time');ax.set_ylim(0,max(r['max_ratio'] for r in rows)+.18);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.suptitle('Same API, same instrumentation: does speculation pay?',fontsize=17,fontweight='bold',x=.08,ha='left')
fig.text(.08,.03,f"Output equality: {v['exact_pairs']}/{v['n']} pairs. Bars: medians; whiskers: min/max of 3 paired repeats, not confidence intervals.\nNo workload was faster in all 3 observed pairs. Local MPS; 6 workloads; no phone or network.",fontsize=10,color='#475569')
fig.subplots_adjust(left=.08,right=.98,top=.84,bottom=.22);fig.savefig(P/'matched-api-results.png',dpi=170);fig.savefig(P/'matched-api-results.svg')
