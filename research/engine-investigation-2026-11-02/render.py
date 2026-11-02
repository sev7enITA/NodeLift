from pathlib import Path
import json,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
micro=json.loads((HERE/'draft-metal-final.json').read_text()); verifier=json.loads((HERE/'verifier-metal.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(11.5,4.9),layout='constrained')
fig.patch.set_facecolor('#091425')
for ax in axes:
 ax.set_facecolor('#101f33');ax.spines[:].set_visible(False);ax.tick_params(colors='#e6f2ff');ax.title.set_color('#f0f8ff');ax.xaxis.label.set_color('#e6f2ff');ax.yaxis.label.set_color('#e6f2ff')
a=axes[0]; scenarios=['two_call_all_rejected','two_call_all_retained'];labels=['Draft tail discarded','Draft tail retained'];colors=['#64d1ec','#5ea3f3']
for y,(scenario,label,col) in enumerate(zip(scenarios,labels,colors)):
 rows=[r for r in micro['samples'] if r['scenario']==scenario and not r['warmup']];ratios=[r['candidate_ms']/r['baseline_ms'] for r in rows]
 a.scatter(ratios,[y]*len(ratios),s=24,color=col,alpha=.60);a.scatter([statistics.median(ratios)],[y],s=125,marker='D',color='#ffffff',zorder=5)
a.axvline(1,color='#f4c56b',linestyle='--',linewidth=1);a.set_yticks(range(2),labels);a.invert_yaxis();a.set_xlim(0,1.15);a.set_xlabel('Candidate / baseline time (lower is faster)');a.set_title('Two native draft calls, 0.5B model',loc='left',fontsize=12,color='#f0f8ff')
b=axes[1];s=verifier['summary']; bars=b.barh(['Batch verification','Serial verification'],[s['batch_median_ms'],s['serial_median_ms']],color=['#5ea3f3','#64d1ec']);b.invert_yaxis();b.set_xlim(0,max(s['serial_median_ms']*1.42,1));b.set_xlabel('Median time per verification (ms)');b.set_title('Verifier trade-off, 1.5B model',loc='left',fontsize=12,color='#f0f8ff')
for bar,count in zip(bars,[s['batch_matches'],s['serial_matches']]):
 b.text(bar.get_width()+.4,bar.get_y()+bar.get_height()/2,f'{bar.get_width():.1f} ms | {count}/{s["sample_count"]} match',va='center',color='#f0f8ff',fontsize=9)
fig.suptitle('NodeLift native experiments on Mac: exploratory only',color='#ffffff',fontweight='bold',fontsize=14,x=.035,ha='left')
fig.text(.035,-.06,'One session per experiment; controlled cache states; warmups excluded. No phone, network, energy or end-to-end result.',color='#bdd0e4',fontsize=9)
fig.savefig(HERE/'native-experiments.png',dpi=160,bbox_inches='tight',facecolor=fig.get_facecolor())
