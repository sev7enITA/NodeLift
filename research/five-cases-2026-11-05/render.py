"""English figures for the diagnostic evidence package."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parent;s=json.loads((P/'summary.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,3,figsize=(16,5),gridspec_kw={'width_ratios':[1.15,1,1.3]})
ax=axes[0];x=np.arange(4)
for shift,lane,color in [(-.18,'native','#d87546'),(.18,'fp32','#167aa0')]:
 rows=[s['envelope'][lane][str(w)] for w in [1,2,4,8]];v=[r['median_request_ratio'] for r in rows];bars=ax.bar(x+shift,v,.34,label=lane.upper(),color=color)
 for b,r in zip(bars,rows):ax.text(b.get_x()+b.get_width()/2,b.get_height()+.03,f"{r['exact']}/6",ha='center',fontsize=9)
ax.axhline(1,color='#333',ls=':',lw=1);ax.set(xticks=x,xticklabels=['1','2','4','8'],xlabel='Verifier width',ylabel='Median paired time ratio vs width 1',title='Free-candidate verifier diagnostic',ylim=(0,2.5));ax.legend(frameon=False);ax.text(.02,.95,'Labels: exact replay runs\nHigher ratio is faster\nNot live speculative generation',transform=ax.transAxes,va='top',fontsize=9)
ax=axes[1];arms=['old-adaptive','charged'];vals=[s['accounting'][a]['median_request_ratio'] for a in arms];bars=ax.bar(['Original\ncontroller','Startup + rewind\ncharged'],vals,color=['#788b9c','#167aa0'])
for b,a in zip(bars,arms):
 r=s['accounting'][a];ax.text(b.get_x()+b.get_width()/2,b.get_height()+.02,f"{r['median_request_ratio']:.3f}x\n{r['exact']}/{r['runs']} exact",ha='center')
ax.axhline(1,color='#333',ls=':',lw=1);ax.set(ylabel='Median paired target-only / request time',title='Actual same-Mac speculative requests',ylim=(0,1.3));ax.text(.02,.95,'FP32 floating parameters\n3 diagnostic prompts, 2 repetitions\nNot a qualification dataset',transform=ax.transAxes,va='top',fontsize=9);ax.text(.5,.07,'Identical k trajectories in 6/6 pairs\nTiming difference is not causal evidence',transform=ax.transAxes,ha='center',color='white',fontsize=9)
ax=axes[2];grid=s['simulation']['grid'];ds=sorted({v['producer_ms_per_token'] for v in grid});ns=sorted({v['delivery_ms_per_block'] for v in grid});matrix=np.array([[next(v['median_ratio'] for v in grid if v['producer_ms_per_token']==d and v['delivery_ms_per_block']==n) for n in ns] for d in ds]);im=ax.imshow(matrix,cmap='RdYlGn',vmin=.5,vmax=1.5,aspect='auto')
for i in range(len(ds)):
 for j in range(len(ns)):ax.text(j,i,f'{matrix[i,j]:.2f}',ha='center',va='center',fontsize=9)
ax.set(xticks=range(len(ns)),xticklabels=ns,yticks=range(len(ds)),yticklabels=ds,xlabel='Hypothetical delivery delay per block (ms)',ylabel='Hypothetical producer cost per token (ms)',title='Ideal bounded-pipeline simulation');fig.colorbar(im,ax=ax,shrink=.65,label='Median paired time ratio')
fig.suptitle('NodeLift: identify the bottleneck before changing the architecture',fontsize=17,fontweight='bold',y=1.02)
fig.text(.5,-.055,'Qwen3 14B 4-bit | Shared M3 Max, low-power mode enabled | Free producer and perfect candidates are assumptions, not phone measurements.\nNo generalized acceleration, energy benefit or shared-memory result is established. Sources: summary.json and retained raw runs.',ha='center',fontsize=10)
fig.tight_layout();fig.savefig(P/'five-cases.png',dpi=180,bbox_inches='tight');fig.savefig(P/'five-cases.svg',bbox_inches='tight')
