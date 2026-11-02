"""Visualize paired exploratory same-machine sessions; no confidence intervals."""
from pathlib import Path
import json,statistics,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
here=Path(__file__).resolve().parent;data=json.loads((here/'paired-summary.json').read_text());lang=sys.argv[1] if len(sys.argv)>1 else 'en';out=Path(sys.argv[2]) if len(sys.argv)>2 else here/'local-8b-pairs.png'
translations={
'en':{'initial':'Initial','repeat':'Repeat','total':'Total response time','ttft':'First-token delay','speed':'Host-only duration / local-draft duration (>1 is faster)','delay':'Local draft minus host-only TTFT (ms; positive is slower)','title':'NodeLift local 8B / 3B experiment: paired runs on one Mac','note':'Each dot is one prompt/repetition pair; diamonds are medians. Both models are resident. No phone or PC; no confidence interval.'},
'it':{'initial':'Prima sessione','repeat':'Ripetizione','total':'Tempo totale di risposta','ttft':'Ritardo del primo token','speed':'Durata solo host / durata draft locale (>1 è più veloce)','delay':'TTFT draft locale meno solo host (ms; positivo è più lento)','title':'NodeLift 8B / 3B in locale: prove a coppie su un Mac','note':'Ogni punto è una coppia di prove; i rombi sono mediane. Entrambi i modelli sono residenti. Nessun telefono o PC; nessun intervallo di confidenza.'},
'zh-Hans':{'initial':'初次','repeat':'复测','total':'总响应时间','ttft':'首个 token 延迟','speed':'仅主机用时 / 本地草稿用时（大于 1 表示更快）','delay':'本地草稿减去仅主机首 token 时间（毫秒；正数更慢）','title':'NodeLift 本地 8B / 3B 实验：一台 Mac 上的配对测试','note':'每个点是一组配对测试；菱形为中位数。两个模型均驻留本机。未使用手机或 PC；未计算置信区间。'}}
if lang not in translations:raise ValueError('unsupported language')
t=translations[lang]
if lang=='zh-Hans':
 path='/System/Library/Fonts/STHeiti Light.ttc';font_manager.fontManager.addfont(path);plt.rcParams['font.family']=font_manager.FontProperties(fname=path).get_name();plt.rcParams['axes.unicode_minus']=False
fig,axes=plt.subplots(1,2,figsize=(13,7),layout='constrained');fig.patch.set_facecolor('#091425')
for ax in axes:
 ax.set_facecolor('#101f33');ax.spines[:].set_visible(False);ax.tick_params(colors='#e6f2ff');ax.xaxis.label.set_color('#e6f2ff')
colors=['#64d1ec','#a5a5f5'];labels=[];ys=[]
for si,session in enumerate(data['sessions']):
 for j,c in enumerate(session['conditions']):
  y=si*5+j;ys.append(y);labels.append((t['initial'] if si==0 else t['repeat'])+' | k='+str(c['draft_width']))
  pairs=[p for p in c['pairs'] if p['comparable']];xs=[p['paired_speedup'] for p in pairs];ts=[p['ttft_change_ms'] for p in pairs]
  axes[0].scatter(xs,[y]*len(xs),s=25,color=colors[si],alpha=.6);axes[1].scatter(ts,[y]*len(ts),s=25,color=colors[si],alpha=.6)
  if xs:axes[0].scatter([statistics.median(xs)],[y],s=90,marker='D',color='white',zorder=5);axes[1].scatter([statistics.median(ts)],[y],s=90,marker='D',color='white',zorder=5)
for ax in axes:ax.set_yticks(ys,labels);ax.invert_yaxis()
axes[0].axvline(1,color='#ffcf77',ls='--');axes[0].set_xlabel(t['speed']);axes[0].set_title(t['total'],loc='left',color='#f0f8ff')
axes[1].axvline(0,color='#ffcf77',ls='--');axes[1].set_xlabel(t['delay']);axes[1].set_title(t['ttft'],loc='left',color='#f0f8ff')
fig.suptitle(t['title'],color='white',fontsize=15,fontweight='bold',x=.03,ha='left')
fig.text(.03,-.035,t['note'],color='#bdd0e4',fontsize=9)
out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=160,bbox_inches='tight',facecolor=fig.get_facecolor())
