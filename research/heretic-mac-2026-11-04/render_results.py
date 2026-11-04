"""Render descriptive paired results, never an inferred speedup."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parent
v=json.loads((P/'results/aggregate.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(14,5.6),facecolor='#f8fafc')
colors=['#087f8c','#ec9a29']; w=.35
for ax in axs:ax.set_facecolor('#f8fafc');ax.set_axisbelow(True);ax.grid(axis='y',alpha=.2)
x=np.arange(3); arms=['original','refusal','nosyco']
for i,(field,label) in enumerate([('strict_correct','Correct and exact format'),('answer_letter_correct','Correct first answer letter')]):
 bars=axs[0].bar(x+(i-.5)*w,[v['technical'][a][field] for a in arms],w,label=label,color=colors[i]);axs[0].bar_label(bars,padding=3)
axs[0].set_xticks(x,['Original 4B','Reduced refusal','Anti-sycophancy']);axs[0].set_ylim(0,16.8);axs[0].set_yticks([0,4,8,12,16]);axs[0].set_ylabel('Correct answers / 16 targeted cases');axs[0].set_title('Technical screening: no overall qualification',loc='left',fontweight='bold');axs[0].legend(loc='lower left',fontsize=9)
x=np.arange(4)
for i,(arm,label) in enumerate([('original','Original draft 0.6B'),('modified','Teacher-KL modified draft')]):
 bars=axs[1].bar(x+(i-.5)*w,[r['prefix_matches'] for r in v['draft'][arm]['workloads']],w,label=label,color=colors[i]);axs[1].bar_label(bars,padding=3)
axs[1].set_xticks(x,['Race','Experiment','Correction','Clean code']);axs[1].set_ylim(0,34);axs[1].set_yticks([0,8,16,24,32]);axs[1].set_ylabel('Matching initial tokens / 32 candidates');axs[1].set_title('Draft k=4: 49 to 47 matches across 128 candidates',loc='left',fontweight='bold');axs[1].legend(loc='upper left',fontsize=9)
fig.suptitle('NodeLift | Heretic pilot on Apple M3 Max',fontsize=18,fontweight='bold',x=.06,ha='left')
fig.text(.06,.02,'4 optimization trials per variant; one held-out pass. Draft prefixes fixed by the target. No live verifier or network.\nDescriptive results only: these are not throughput, acceptance-in-production or distributed acceleration measurements.',fontsize=10,color='#475569')
fig.subplots_adjust(top=.80,bottom=.20,wspace=.30,left=.06,right=.98)
fig.savefig(P/'mac-pilot-results.png',dpi=170);fig.savefig(P/'mac-pilot-results.svg')
print('Rendered PNG and SVG')
