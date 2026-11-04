"""Render measured paired ratios and the separate fixed-prefix diagnostic."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parent;v=json.loads((P/'results/summary.json').read_text())
arms=['raw_batch','aligned_batch','aligned_serial','upstream_assisted'];labels=['Raw draft / batch','Aligned draft / batch','Aligned draft / serial','Upstream assisted']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(14,6.2),facecolor='#f8fafc',gridspec_kw={'width_ratios':[1,2]})
for ax in axs:ax.set_facecolor('#f8fafc')
bars=axs[0].bar(['Raw draft','Aligned draft'],[v['format_probe'][a]['matching'] for a in ['raw','aligned']],color=['#94a3b8','#087f8c'],width=.55);axs[0].bar_label(bars,padding=3);axs[0].set_ylim(0,128);axs[0].set_ylabel('Matching initial tokens / 128 candidates');axs[0].set_title('Reused fixed-prefix diagnostic',loc='left',fontweight='bold');axs[0].grid(axis='y',alpha=.2);axs[0].set_axisbelow(True)
x=np.arange(6);colors=['#64748b','#087f8c','#d97706','#7c3aed']
for i,(arm,label) in enumerate(zip(arms,labels)):
 rows=v['arms'][arm]['by_prompt'];means=[r['median_ratio'] for r in rows];lo=[r['median_ratio']-r['min_ratio'] for r in rows];hi=[r['max_ratio']-r['median_ratio'] for r in rows]
 axs[1].errorbar(x+(i-1.5)*.10,means,yerr=[lo,hi],fmt='o',markersize=5,capsize=3,label=label,color=colors[i])
 for j,r in enumerate(rows):
  if r['exact_pairs']<3:axs[1].plot(j+(i-1.5)*.10,r['median_ratio'],'x',markersize=11,color='#dc2626')
axs[1].axhline(1,color='#111827',linestyle='--',linewidth=1);axs[1].set_xticks(x,['Unique list','Epoch','TTFT','JSON','Queue','Memory']);axs[1].set_ylabel('Target-only time / candidate-arm time');axs[1].set_title('Cached execution: above 1 is faster',loc='left',fontweight='bold');axs[1].grid(axis='y',alpha=.2);axs[1].legend(fontsize=9,ncol=2,loc='upper right')
fig.suptitle('NodeLift | Draft format versus actual execution cost',fontsize=18,fontweight='bold',x=.06,ha='left')
fig.text(.06,.025,'Right: medians and min/max of 3 paired repeats per workload, not confidence intervals. Red crosses: output mismatch in at least one repeat.\nMixed API instrumentation: use the separate matched-API control to assess the upstream arm.\nFloat16 PyTorch/MPS, 64-token cap, resident models. No network, phone, energy or native-engine qualification.',fontsize=10,color='#475569')
fig.subplots_adjust(left=.06,right=.98,bottom=.25,top=.80,wspace=.27);fig.savefig(P/'format-versus-cost.png',dpi=170);fig.savefig(P/'format-versus-cost.svg')
print('Rendered chart')
