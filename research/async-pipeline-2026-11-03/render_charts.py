"""Render every paired point, retaining unequal-output cases."""
from pathlib import Path
import json,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
local=json.loads((ROOT/'local-8b/summary.json').read_text())
up=json.loads((ROOT/'upstream-8b/summary.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
fig,axes=plt.subplots(1,2,figsize=(15,7),gridspec_kw={'wspace':.7});fig.patch.set_facecolor('#f7fafc')
labels=['Serial draft k4','Serial bounded k4','Batch draft k1','Batch draft k4','Batch draft k8','Batch bounded k4','Lookup batch k4']
for ax,rows,names,title in [(axes[0],local,labels,'NodeLift controller'),(axes[1],up,[r['arm'].replace('draft-simple','Draft').replace('ngram-mod','Ngram') for r in up],'llama.cpp HTTP control')]:
 for y,(row,name) in enumerate(zip(rows,names)):
  pairs=row.get('pairs',row.get('comparisons'));values=[p.get('speedup',p.get('wall_speedup')) for p in pairs]
  for i,(p,x) in enumerate(zip(pairs,values)):
   good=p['exact_tokens'];ax.scatter(x,y+(i-4)*.045,c='#156c8a' if good else '#b54035',marker='o' if good else 'x',s=34,alpha=.8)
  med=statistics.median(values);ax.plot([med,med],[y-.28,y+.28],color='#172c40',lw=2)
  bad=sum(not p['exact_tokens'] for p in pairs)
  ax.text(2.03,y,f'{med:.3f}x\n{bad}/9 differ',va='center',fontsize=9,color='#b54035' if bad else '#172c40')
 ax.set_yticks(range(len(rows)),names);ax.invert_yaxis();ax.axvline(1,color='#172c40',ls='--',lw=1)
 ax.set_xlim(.3,2.0);ax.set_title(title,pad=15,fontweight='bold');ax.set_xlabel('Paired speed ratio: target-only time / candidate time\nLeft of 1 = slower; right = faster');ax.grid(axis='x',alpha=.2)
 for side in ['top','right','left']:ax.spines[side].set_visible(False)
fig.suptitle('8B target / 1B draft: speed is conditional on output equivalence',fontsize=17,fontweight='bold',y=.99)
fig.text(.5,.01,'3 public prompts × 3 repeats per arm; 128-token budget. Each panel has its own timing baseline.\nBlue circles: identical token sequence. Red crosses: unequal output, disqualified as exact-output speedup. Black tick: median.\nSingle-session pilot; no confidence interval, phone result or energy claim.',ha='center',fontsize=10)
fig.subplots_adjust(top=.86,bottom=.2,left=.13,right=.92)
fig.savefig(ROOT/'comparative-pilot.png',dpi=180);fig.savefig(ROOT/'comparative-pilot.svg');plt.close(fig)
