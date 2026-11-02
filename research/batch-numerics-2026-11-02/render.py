"""Visualize selected overlapping windows; never extrapolate to a failure rate."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent;data=json.loads((p/'summary.json').read_text())['runs'];fig,ax=plt.subplots(figsize=(10.5,5.7),layout='constrained');fig.patch.set_facecolor('#091425');ax.set_facecolor('#101f33');ax.spines[:].set_visible(False);ax.tick_params(colors='#e6f2ff');ax.xaxis.label.set_color('#e6f2ff')
labels=[];values=[];ann=[]
for r in data:
 name=r['raw_file'].replace('metal-flash-on-','Metal, flash on / ').replace('metal-flash-off-','Metal, flash off / ').replace('cpu-flash-on-','CPU, flash on / ').replace('cpu-flash-off-','CPU, flash off / ').replace('.json','')
 labels.append(name);values.append(r['counts'].get('serial_batch_top1_flips',0));ann.append(r['counts']['positions'])
bars=ax.barh(labels,values,color='#67cee8');ax.invert_yaxis();ax.set_xlim(0,max(values)+2.7);ax.set_xlabel('Top-1 changes in selected token positions');ax.set_title('Batch vs one-token evaluation on the same prefix',loc='left',color='white',fontweight='bold',fontsize=13)
for bar,n in zip(bars,ann):ax.text(bar.get_width()+.15,bar.get_y()+bar.get_height()/2,f'{int(bar.get_width())} / {n}',color='white',va='center')
fig.text(.04,-.035,'Overlapping windows repeat positions. Serial A/A had no logit differences in these cases; no population rate or phone claim.',color='#bdd0e4',fontsize=9)
fig.savefig(p/'shape-comparison.png',dpi=160,bbox_inches='tight',facecolor=fig.get_facecolor())
