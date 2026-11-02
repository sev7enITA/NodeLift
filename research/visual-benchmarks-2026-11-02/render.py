"""Rebuild the published figures from retained paired attempts, never hand-entered medians."""
from pathlib import Path
import hashlib, json, statistics, runpy, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
ASSETS=ROOT/'site/NodeLift/assets/benchmarks-2026-11-02'
ASSETS.mkdir(parents=True,exist_ok=True)
SUM=runpy.run_path(str(ROOT/'research/phone-tradeoffs-2026-11-02/summarize.py'))['summarize']
BG='#09141f'; INK='#edf3f7'; MUTED='#adbdca'; GRID='#2b3b49'; BLUE='#68bdff'; GOLD='#edbc68'
SOURCES={}
for prefix,folder in [('x','phone-tradeoffs'),('i','iphone-tradeoffs')]:
 for name in ['remote-fixed-32','remote-adaptive-32','remote-adaptive-128']+(['build15-fixed-128','build15-adaptive-32','remote-fixed-128'] if prefix=='i' else []):
  p=ROOT/f'research/{folder}-2026-11-02/{name}.json'
  raw=json.loads(p.read_text()); s=SUM(raw)
  SOURCES[prefix+':'+name]={'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'summary':s,'raw':raw}
FIX=['x:remote-fixed-32','i:remote-fixed-32','i:build15-fixed-128']
ADAPT=['x:remote-adaptive-32','x:remote-adaptive-128','i:remote-adaptive-32','i:remote-adaptive-128','i:build15-adaptive-32']
RELIABILITY=['i:remote-adaptive-32','i:remote-fixed-32','i:remote-adaptive-128','i:remote-fixed-128','i:build15-adaptive-32','i:build15-fixed-128']
TEXT={
'en':{
'scope':'Qwen2.5 target 1.5B / draft 0.5B · Q4_K_M · Xiaomi hotspot · 2 Nov 2026',
'ratio':'01 / Total response time with fixed delegation',
'ratio_axis':'Phone-assisted / paired Mac duration (logarithmic scale; lower is better)',
'baseline':'1x = Mac alone',
'key':'Small circles: individual pairs. Diamond: median. No confidence interval is established.',
'caveat':'Observed routes, not a controlled hardware ranking. Backends, topology and builds differ.',
'phone':'iPhone', 'xiaomi':'Xiaomi', 'budget':'token budget', 'build':'build',
'first':'02 / Extra time before the first token',
'first_axis':'Phone TTFT minus paired Mac TTFT (ms; lower is better)',
'zoom':'iPhone detail · same unit, expanded 0–450 ms scale',
'adaptive_title':'03 / Adaptive service time including fallback',
'adaptive_axis':'Phone-route duration minus paired Mac duration (ms)',
'adaptive_note':'Every request here fell back to the Mac; zero phone tokens were accepted.',
'adaptive_warning':'Negative differences are observed variation, not demonstrated phone acceleration.',
'zero':'0 = same duration',
'contribution':'04 / Useful proposals and request outcomes',
'accept_title':'Received proposals: accepted / not accepted',
'accepted':'Accepted', 'rejected':'Not accepted',
'count':'Share of received proposals (%)',
'outcomes':'iPhone candidate requests only · host-arm requests excluded',
'clean':'Completed, no fallback','fallback':'Completed, fallback','invalid':'Invalid','missing':'Missing',
'planned':'Candidate requests (count)',
'coverage_note':'The interrupted build-14 cell retains 1 invalid and 2 missing candidate requests.',
'coverage_extra':'Its 3 host-arm requests are also missing. Acceptance does not imply a speedup.',
'note':'Short correlated periods. Energy and sustained thermal performance are unmeasured.',
'fixed':'fixed','adaptive':'adaptive'
},
'it':{
'scope':'Qwen2.5 target 1.5B / draft 0.5B · Q4_K_M · hotspot Xiaomi · 2 nov 2026',
'ratio':'01 / Tempo totale con delega fissa',
'ratio_axis':'Durata con telefono / Mac abbinato (scala logaritmica; meno è meglio)',
'baseline':'1x = solo Mac',
'key':'Cerchi piccoli: singole coppie. Rombo: mediana. Nessun intervallo di confidenza.',
'caveat':'Percorsi osservati, non classifica hardware controllata. Backend, rete e build diversi.',
'phone':'iPhone','xiaomi':'Xiaomi','budget':'token massimi','build':'build',
'first':'02 / Attesa aggiuntiva prima del primo token',
'first_axis':'TTFT con telefono meno TTFT Mac abbinato (ms; meno è meglio)',
'zoom':'Dettaglio iPhone · stessa unità, scala ampliata 0–450 ms',
'adaptive_title':'03 / Tempo del servizio adattivo, fallback incluso',
'adaptive_axis':'Durata percorso telefono meno durata Mac abbinato (ms)',
'adaptive_note':'Ogni richiesta qui è tornata al Mac; zero token del telefono accettati.',
'adaptive_warning':'Le differenze negative sono variazioni osservate, non accelerazione dimostrata.',
'zero':'0 = stessa durata',
'contribution':'04 / Proposte utili ed esiti delle richieste',
'accept_title':'Proposte ricevute: accettate / non accettate',
'accepted':'Accettate','rejected':'Non accettate','count':'Quota delle proposte ricevute (%)',
'outcomes':'Solo richieste candidate iPhone · escluse le richieste del braccio Mac',
'clean':'Complete, senza fallback','fallback':'Complete, con fallback','invalid':'Non valide','missing':'Mancanti',
'planned':'Richieste candidate (numero)',
'coverage_note':'La cella interrotta della build 14 conserva 1 richiesta non valida e 2 mancanti.',
'coverage_extra':'Mancano anche le 3 richieste del braccio Mac. Accettare token non significa accelerare.',
'note':'Periodi brevi e correlati. Energia e prestazioni termiche prolungate non misurate.',
'fixed':'fissa','adaptive':'adattiva'
},
'zh-Hans':{
'scope':'Qwen2.5 主模型 1.5B / 草稿 0.5B · Q4_K_M · 小米热点 · 2026年11月2日',
'ratio':'01 / 固定委派的总响应时间',
'ratio_axis':'手机协同耗时 / 配对 Mac 耗时（对数刻度；越低越好）',
'baseline':'1x = Mac 单独运行',
'key':'小圆点：各配对试验。菱形：中位数。尚无可用置信区间。',
'caveat':'这是实测路径对比，不是受控硬件排名。后端、网络拓扑和版本不同。',
'phone':'iPhone','xiaomi':'小米','budget':'输出令牌上限','build':'构建',
'first':'02 / 首个令牌的额外等待时间',
'first_axis':'手机路径 TTFT 减去配对 Mac TTFT（毫秒；越低越好）',
'zoom':'iPhone 细节 · 单位不变，放大为 0–450 毫秒刻度',
'adaptive_title':'03 / 自适应服务时间，包含回退成本',
'adaptive_axis':'手机路径耗时减去配对 Mac 耗时（毫秒）',
'adaptive_note':'此处每个请求均回退至 Mac；没有手机令牌被接受。',
'adaptive_warning':'负差值是观测波动，不代表已证实的手机加速。',
'zero':'0 = 耗时相同',
'contribution':'04 / 有效建议与请求结果',
'accept_title':'已接收建议：接受 / 未接受',
'accepted':'接受','rejected':'未接受','count':'已接收建议占比（%）',
'outcomes':'仅 iPhone 候选请求 · 不含 Mac 基准组请求',
'clean':'完成，无回退','fallback':'完成，有回退','invalid':'无效','missing':'缺失',
'planned':'候选请求数',
'coverage_note':'构建 14 的中断测试保留了 1 个无效和 2 个缺失候选请求。',
'coverage_extra':'其 Mac 基准组另有 3 个请求缺失。接受令牌不等于加速。',
'note':'短时且相关的测量周期。未测量能耗及持续热性能。',
'fixed':'固定','adaptive':'自适应'
}}
CJK=os.environ.get('NODELIFT_CJK_FONT','/System/Library/Fonts/STHeiti Light.ttc')
if not Path(CJK).is_file(): raise SystemExit('Set NODELIFT_CJK_FONT to an installed Chinese font, such as Noto Sans CJK.')
font_manager.fontManager.addfont(CJK)
ZH=font_manager.FontProperties(fname=CJK).get_name()

def label(k,t,short=False):
 phone=t['xiaomi'] if k.startswith('x:') else t['phone']
 budget=k.rsplit('-',1)[1]
 build='0.2.8' if k.startswith('x:') else ('15' if ':build15-' in k else '14')
 if short:return f"{t['build']} {build} · {t['adaptive'] if 'adaptive' in k else t['fixed']} · {budget}"
 return f"{phone} · {('v' + build) if k.startswith('x:') else (t['build'] + ' ' + build)}\n{budget} {t['budget']} · n={len(SOURCES[k]['summary']['pairs'])}"

def theme(lang):
 plt.rcParams.update({'font.family':ZH if lang=='zh-Hans' else 'DejaVu Sans','font.size':12,'text.color':INK,'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':INK,'axes.facecolor':BG,'figure.facecolor':BG,'axes.edgecolor':GRID,'axes.unicode_minus':False,'savefig.facecolor':BG})

def finish(fig,axes,title,t,notes,name,lang):
 fig.text(.04,.958,'NODELIFT / MEASURED EVIDENCE',color=BLUE,fontsize=10,weight='bold')
 fig.text(.04,.915,title,fontsize=21,weight='bold')
 fig.text(.04,.87,t['scope'],fontsize=11,color=MUTED)
 for i,line in enumerate(notes):fig.text(.04,.102-i*.026,line,fontsize=10,color=MUTED)
 for ax in axes:
  ax.spines[['top','right']].set_visible(False);ax.set_axisbelow(True);ax.grid(axis='x',color=GRID,lw=.7)
 path=ASSETS/f'{name}.{lang}.png'
 fig.savefig(path,dpi=150);plt.close(fig)
 return path

def dots(ax,keys,field,t,ratio=False):
 for y,k in enumerate(keys):
  values=[p[field] for p in SOURCES[k]['summary']['pairs'] if p['equivalent']]
  color=GOLD if k.startswith('x:') else BLUE
  # Fixed deterministic offsets keep all observations visible; no sampling or random jitter.
  offsets=[(i-(len(values)-1)/2)*.055 for i in range(len(values))]
  ax.scatter(values,[y+d for d in offsets],s=40,facecolors='none',edgecolors=color,lw=1.2,zorder=3)
  med=statistics.median(values);ax.scatter([med],[y],s=95,marker='D',color=color,edgecolor=BG,zorder=4)
  ax.annotate(f'{med:.3f}'+('x' if ratio else ' ms'),(med,y),xytext=(0,-29),textcoords='offset points',ha='center',color=color,fontsize=12,weight='bold')
 ax.set_yticks(range(len(keys)),[label(k,t) for k in keys]);ax.set_ylim(len(keys)-.4,-.5);ax.tick_params(axis='y',length=0,pad=16)

for lang,t in TEXT.items():
 theme(lang)
 fig,ax=plt.subplots(figsize=(12,7.5));fig.subplots_adjust(left=.29,right=.96,bottom=.27,top=.78)
 dots(ax,FIX,'slowdown_ratio',t,True);ax.set_xscale('log');ax.set_xlim(.7,240)
 ax.set_xticks([1,2,5,10,50,100,200],['1x','2x','5x','10x','50x','100x','200x']);ax.xaxis.set_minor_locator(ticker.NullLocator());ax.axvline(1,color=INK,lw=1.3,ls='--');ax.text(1,-.42,t['baseline'],fontsize=10,color=MUTED,ha='left');ax.set_xlabel(t['ratio_axis'],labelpad=12)
 finish(fig,[ax],t['ratio'],t,[t['key'],t['caveat'],t['note']],'01-total-time',lang)
 fig,(ax,zoom)=plt.subplots(2,1,figsize=(12,10),gridspec_kw={'height_ratios':[1.4,1]});fig.subplots_adjust(left=.29,right=.96,bottom=.22,top=.80,hspace=.6)
 dots(ax,FIX,'ttft_change_ms',t);ax.set_xlim(0,10500);ax.set_xticks([0,2000,4000,6000,8000,10000]);ax.set_xlabel(t['first_axis'])
 dots(zoom,FIX[1:],'ttft_change_ms',t);zoom.set_xlim(0,450);zoom.set_title(t['zoom'],loc='left',color=MUTED,fontsize=12,pad=18);zoom.set_xlabel('ms')
 finish(fig,[ax,zoom],t['first'],t,[t['key'],t['caveat'],t['note']],'02-first-token',lang)
 fig,ax=plt.subplots(figsize=(12,9));fig.subplots_adjust(left=.30,right=.96,bottom=.25,top=.79)
 dots(ax,ADAPT,'added_ms',t);values=[p['added_ms'] for k in ADAPT for p in SOURCES[k]['summary']['pairs']];ax.set_xlim(min(-200,min(values)*1.15),max(200,max(values)*1.15));ax.axvline(0,color=INK,lw=1.3,ls='--');ax.set_xlabel(t['adaptive_axis']);ax.text(0,-.5,t['zero'],fontsize=10,color=MUTED)
 finish(fig,[ax],t['adaptive_title'],t,[t['adaptive_note'],t['adaptive_warning'],t['key']],'03-adaptive-fallback',lang)
 fig,(ax,cover)=plt.subplots(2,1,figsize=(12,12),gridspec_kw={'height_ratios':[1,1.4]});fig.subplots_adjust(left=.32,right=.96,bottom=.20,top=.78,hspace=.6)
 for y,k in enumerate(FIX):
  c=SOURCES[k]['summary']['counts'];a=c['accepted'];p=c['proposed'];pct=100*a/p
  ax.barh(y,pct,color=BLUE,height=.5,label=t['accepted'] if y==0 else None)
  ax.barh(y,100-pct,left=pct,color=GRID,edgecolor=MUTED,hatch='///',height=.5,label=t['rejected'] if y==0 else None)
  ax.text(pct/2,y,f'{a}/{p}\n{pct:.1f}%',ha='center',va='center',color=BG,fontsize=12,weight='bold')
  ax.text(pct+(100-pct)/2,y,str(p-a),ha='center',va='center',color=INK,fontsize=12)
 ax.set_yticks(range(3),[label(k,t) for k in FIX]);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel(t['count']);ax.set_title(t['accept_title'],loc='left',fontsize=13,pad=40);ax.legend(ncol=2,loc='lower left',bbox_to_anchor=(0,1.01),frameon=False,fontsize=10)
 colors=[BLUE,GOLD,'#9aabb8',BG];hatches=['','','xx','///']
 for y,k in enumerate(RELIABILITY):
  raw=SOURCES[k]['raw'];attempts=[a for s in raw['sessions'] for a in s['attempts'] if a['arm']=='candidate'];planned=sum(len(s['plan']) for s in raw['sessions']);counts=[sum(a['status']=='completed' and not a['fallback'] for a in attempts),sum(a['status']=='completed' and a['fallback'] for a in attempts),sum(a['status']!='completed' for a in attempts),planned-len(attempts)];assert sum(counts)==planned
  left=0
  for j,n in enumerate(counts):
   cover.barh(y,n,left=left,height=.6,color=colors[j],edgecolor=MUTED if j==3 else BG,hatch=hatches[j],label=t[['clean','fallback','invalid','missing'][j]] if y==0 else None)
   if n:cover.text(left+n/2,y,str(n),ha='center',va='center',color=INK if j==3 else BG,weight='bold')
   left+=n
 cover.set_yticks(range(len(RELIABILITY)),[label(k,t,True) for k in RELIABILITY]);cover.invert_yaxis();cover.set_xlim(0,6);cover.set_xticks(range(7));cover.set_xlabel(t['planned']);cover.set_title(t['outcomes'],loc='left',fontsize=12,pad=48);cover.legend(ncol=2,loc='lower left',bbox_to_anchor=(0,1.01),frameon=False,fontsize=10)
 finish(fig,[ax,cover],t['contribution'],t,[t['coverage_note'],t['coverage_extra'],t['note']],'04-contribution-outcomes',lang)

# Compact exact chart rows, source hashes and definitions travel with the figures.
rows={k:{'source':v['file'],'sha256':v['sha256'],'pairs':v['summary']['pairs'],'counts':v['summary']['counts']} for k,v in SOURCES.items()}
(OUT/'chart-data.json').write_text(json.dumps({'definitions':{'slowdown_ratio':'candidate duration / paired host duration','added_ms':'candidate duration minus paired host duration','ttft_change_ms':'candidate TTFT minus paired host TTFT','intervals':'none; circles are observed pairs, not confidence limits','coverage':'candidate requests only; full raw reports also retain missing host attempts'},'rows':rows},indent=2)+'\n')
manifest={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(ASSETS.glob('*.png'))}
(OUT/'figures.json').write_text(json.dumps({'matplotlib':matplotlib.__version__,'figures':manifest},indent=2)+'\n')
print(f'Rendered {len(manifest)} localized figures from {len(SOURCES)} retained raw cells.')
