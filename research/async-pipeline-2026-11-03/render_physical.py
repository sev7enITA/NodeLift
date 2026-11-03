"""Render the interrupted physical attempts without implying qualification."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
rows=json.loads((root/'physical-attempts.json').read_text())['attempts']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
fig,axes=plt.subplots(1,2,figsize=(12,6));fig.patch.set_facecolor('#f7fafc')
for ax,base,key,title in [(axes[0],'reference_duration_ms','remote_duration_ms','Complete request, including fallback and cleanup'),(axes[1],'reference_ttft_ms','remote_ttft_ms','Client time to first text')]:
 for i,r in enumerate(rows):
  for offset,k,color,label in [(-.18,base,'#156c8a','Mac reference'),(.18,key,'#c05b36','Mac + Xiaomi bounded')]:
   value=r[k]/1000;bar=ax.barh(i+offset,value,height=.3,color=color,label=label if i==0 else None)
   ax.text(value+(.2 if ax==axes[0] else .012),i+offset,f'{value:.3f} s',va='center')
 ax.set_yticks([0,1],['Attempt 1','Attempt 2']);ax.invert_yaxis();ax.set_xlabel('Seconds (lower is faster)');ax.set_title(title,fontsize=12,pad=16);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
 ax.set_xlim(0,23 if ax==axes[0] else 1.22)
 for side in ['top','right','left']:ax.spines[side].set_visible(False)
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.93),ncol=2,frameon=False,fontsize=10)
fig.suptitle('Physical Android 0.2.13: two interrupted 8B / 1B attempts',fontweight='bold',fontsize=16,y=.98)
fig.text(.5,.03,'Both requests produced the same 128 tokens as their Mac reference after fallback.\n26 draft tokens accepted; sequence 9 timed out; approximately 2 s cleanup remained incomplete in both attempts.\nOnly 3/72 and 2/72 planned measured arms were retained. These observations are not a completed performance pilot.\nDifferent host source logging between attempts; no energy measurement or sustained thermal qualification.',ha='center',fontsize=10)
fig.subplots_adjust(top=.82,bottom=.26,wspace=.4,left=.1,right=.96)
fig.savefig(root/'physical-interruptions.png',dpi=180);fig.savefig(root/'physical-interruptions.svg');plt.close(fig)
