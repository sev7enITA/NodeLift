"""Render observed connection pressure; this is not a speed benchmark."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
source=json.loads((root/'socket-diagnostic.json').read_text())
samples=source['samples'];limit=source['server_slot_limit']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
fig,ax=plt.subplots(figsize=(11,6.4));fig.patch.set_facecolor('#f7fafc')
x=[s['elapsed_s'] for s in samples];y=[s['established'] for s in samples]
ax.step(x,y,where='post',color='#156c8a',linewidth=2,label='Observed established companion TLS connections')
ax.scatter([t for t,v in zip(x,y) if v==limit],[v for v in y if v==limit],color='#bd4b33',zorder=3,s=24,label='Observed at the slot limit')
ax.axhline(limit,color='#bd4b33',linestyle='--',linewidth=1,label='Server limit: 32 concurrent slots')
ax.set_ylim(0,36);ax.set_xlim(0,max(x));ax.set_xlabel('Seconds since diagnostic sampling started');ax.set_ylabel('Established connections')
fig.suptitle('Android serial request: connection pressure reached the server limit',fontweight='bold',fontsize=14,y=.98)
ax.grid(alpha=.18);ax.set_axisbelow(True)
for side in ('top','right'):ax.spines[side].set_visible(False)
handles,labels=ax.get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.93),fontsize=9,frameon=False)
fig.text(.5,.03,'One physical Xiaomi 0.2.13 diagnostic with an 8B target and 1B draft.\n43 proposed draft tokens were accepted before a later lease expired and the host used fallback.\nConcurrent socket sampling changes the workload: these timings are diagnostic, not performance evidence.\nThe host connection-lifetime correction passes local tests; a post-fix phone run is still required.',ha='center',fontsize=9)
fig.subplots_adjust(left=.09,right=.97,top=.77,bottom=.25)
for suffix in ('png','svg'):fig.savefig(root/('tls-slot-pressure.'+suffix),dpi=180)
plt.close(fig)
