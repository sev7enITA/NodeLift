'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const params = new URLSearchParams(location.search);
  const locale = window.NodeLiftSiteLocale;
  let savedLanguage = null;
  try { savedLanguage = localStorage.getItem('nodelift-site-language'); } catch (_) {}
  let language = locale.resolveLanguage(params.get('lang'), savedLanguage);
  const textNodes = [...document.querySelectorAll('[data-en]')].map(node => ({node,it:node.dataset.it,en:node.dataset.en,zh:node.dataset.zh}));
  const labelNodes = [...document.querySelectorAll('[data-en-label]')].map(node => ({node,it:node.dataset.itLabel,en:node.dataset.enLabel,zh:node.dataset.zhLabel}));
  const tr = (it,en,...args) => locale.translate(it,en,language,args);
  const make = (tag,text,className) => { const node=document.createElement(tag); if(text!==undefined)node.textContent=String(text); if(className)node.className=className; return node; };
  const safeText = value => typeof value === 'string' && value.trim() ? value : tr('Non documentato nel dataset.','Not documented in the dataset.');
  let dataset = null;
  let filtered = [];
  let page = 0;
  const pageSize = 10;
  let selectedProject = null;
  let priorFocus = null;
  let activeStep = 0;
  let fetching = false;
  let printing = false;
  let presentation = false;
  let chapterIndex = 0;
  let commandedChapter = null;
  let commandTimer;
  const chapters = [...document.querySelectorAll('main > .chapter')];
  const filterIds = ['project-search','category-filter','ecosystem-filter','capability-filter'];
  const filterParams = ['q','category','ecosystem','tag'];
  const uiLabels={
    category:{distributed:['Distribuiti','Distributed'],mobile:['Runtime mobili','Mobile runtimes'],runtime:['Runtime locali','Local runtimes'],serving:['Serving','Serving'],research:['Ricerca','Research'],baseline:['Baseline','Baseline']},
    ecosystem:{western:['Ecosistema occidentale','Western ecosystem'],asia:['Ecosistema asiatico','Asian ecosystem'],international:['Internazionale','International'],unverified:['Provenienza non verificata','Unverified provenance']}
  };
  const uiLabel=(group,code)=>uiLabels[group]?.[code]?tr(...uiLabels[group][code]):safeText(code);
  const fieldLabels = {
    architecture:['Architettura','Architecture'],host:['Host','Host'],android:['Android','Android'],ios:['iOS','iOS'],
    mobile_compute:['Ruolo compute mobile','Mobile compute role'],capacity:['Capacità / sharding','Capacity / sharding'],
    single_chat:['Latenza singola chat','Single-chat latency'],transport:['Trasporto','Transport'],api:['API / integrazione','API / integration'],
    security:['Sicurezza','Security'],evidence:['Evidenze e ambito','Evidence and scope'],limitations:['Limiti','Limitations'],lesson:['Lezione per NodeLift','Lesson for NodeLift'],
    stage:['Stato dichiarato','Reported stage'],license:['Licenza','License'],origin:['Origine / provenienza','Origin / provenance'],revision:['Revisione','Revision'],checked:['Verificato il','Checked']
  };
  const stepContent = [
    {label:'REMOTE DRAFT',it:'Il telefono riceve il contesto tokenizzato e propone un piccolo blocco di token. È un dispositivo fidato, non un nodo pubblico.',en:'The phone receives tokenized context and proposes a small block of tokens. It is a trusted device, not a public node.'},
    {label:'TARGET VERIFICATION',it:'Il target residente sul computer valuta le proposte. Accetta fino al primo disaccordo, poi corregge o produce il token successivo.',en:'The target resident on the computer evaluates the candidates. It accepts up to the first disagreement, then corrects or produces the next token.'},
    {label:'COMMITTED OUTPUT',it:'Solo i token confermati raggiungono il client. Il contesto viene risincronizzato; il draft non decide il testo finale.',en:'Only committed tokens reach the client. Context is resynchronized; the draft does not decide the final text.'},
    {label:'BOUNDED FALLBACK',it:'Una scadenza configurabile da 0,5 a 60 secondi limita ogni attesa remota. In caso di errore o timeout, il computer prosegue e registra il fallback.',en:'A configurable 0.5–60 second deadline bounds each remote wait. On error or timeout, the computer continues and records the fallback.'}
  ];
  function applyLanguage() {
    document.documentElement.lang=language;
    for(const item of textNodes)item.node.textContent=language==='zh-Hans'&&item.zh?item.zh:tr(item.it,item.en);
    for(const item of labelNodes)item.node.setAttribute('aria-label',language==='zh-Hans'&&item.zh?item.zh:tr(item.it,item.en));
    for(const lang of locale.languages)$('lang-'+lang).setAttribute('aria-pressed',String(language===lang));
    document.title=tr('NodeLift: Il tuo hardware ha ancora un futuro.','NodeLift: Your hardware still has a future.');
    document.querySelector('meta[name="description"]').content=tr('NodeLift: un laboratorio open source per delegare inferenza AI a dispositivi locali. Architettura, risultati riproducibili e atlante comparativo dei sistemi distribuiti.','NodeLift: an open-source laboratory for delegating AI inference to local devices. Architecture, reproducible results and a comparison atlas of distributed systems.');
    for(const selector of ['meta[property="og:title"]','meta[name="twitter:title"]'])document.querySelector(selector).content=document.title;
    for(const selector of ['meta[property="og:description"]','meta[name="twitter:description"]'])document.querySelector(selector).content=document.querySelector('meta[name="description"]').content;
    const localeCodes={en:'en_US','zh-Hans':'zh_CN',it:'it_IT'};
    document.querySelector('meta[property="og:locale"]').content=localeCodes[language];
    document.querySelectorAll('meta[property="og:locale:alternate"]').forEach((node,i)=>node.content=locale.languages.filter(lang=>lang!==language).map(lang=>localeCodes[lang])[i]);
    document.querySelector('.hero-emblem').alt=tr('Emblema originale NodeLift: una N luminosa composta da nodi interconnessi','Original NodeLift emblem: a luminous N formed from interconnected nodes');
    $('project-search').placeholder=tr('llama.cpp, Android, speculazione…','llama.cpp, Android, speculation…');
    document.querySelectorAll('[data-benchmark-image]').forEach(img=>{
      img.src='assets/benchmarks-2026-11-02/'+img.dataset.benchmarkImage+'.'+language+'.png';
      img.alt=language==='zh-Hans'?img.dataset.zhAlt:language==='it'?img.dataset.itAlt:img.dataset.enAlt;
    });
    document.querySelectorAll('[data-benchmark-open]').forEach(a=>{a.href='assets/benchmarks-2026-11-02/'+a.dataset.benchmarkOpen+'.'+language+'.png';});
    renderStep();
    if(dataset)renderAtlas();
    else if(!fetching&&!$('atlas-error').hidden)$('atlas-status').textContent=tr('Dataset non disponibile · nessuna riga simulata','Dataset unavailable · no simulated entries');
    if(selectedProject)renderProject(selectedProject);
    if(presentation)updateDeck();
  }
  function syncURL() {
    const url=new URL(location.href);
    filterIds.forEach((id,i)=>{ const value=$(id).value.trim(); if(value)url.searchParams.set(filterParams[i],value);else url.searchParams.delete(filterParams[i]); });
    url.searchParams.set('lang',language);
    if(selectedProject)url.searchParams.set('project',selectedProject.id);else url.searchParams.delete('project');
    history.replaceState(null,'',url);
  }
  for(const lang of locale.languages)$('lang-'+lang).addEventListener('click',()=>{language=lang;try{localStorage.setItem('nodelift-site-language',lang);}catch(_){}applyLanguage();syncURL();});
  function renderStep() {
    const step=stepContent[activeStep];$('step-label').textContent=tr(['DRAFT REMOTO','VERIFICA DEL TARGET','OUTPUT CONFERMATO','FALLBACK CON SCADENZA'][activeStep],step.label);$('step-copy').textContent=tr(step.it,step.en);
    document.querySelector('.architecture-stage').dataset.stage=String(activeStep);
    document.querySelectorAll('.step').forEach((button,i)=>{button.classList.toggle('active',i===activeStep);button.setAttribute('aria-pressed',String(i===activeStep));});
  }
  document.querySelectorAll('.step').forEach((button,i)=>{
    button.addEventListener('click',()=>{activeStep=i;renderStep();});
    button.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))return;event.preventDefault();event.stopPropagation();activeStep=(i+(['ArrowLeft','ArrowUp'].includes(event.key)?3:1))%4;renderStep();document.querySelectorAll('.step')[activeStep].focus();});
  });
  filterIds.forEach((id,i)=>{if(params.has(filterParams[i]))$(id).value=params.get(filterParams[i]);});
  const normalize = value => String(value).normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  function matches(project) {
    const q=normalize($('project-search').value.trim());
    const category=$('category-filter').value,ecosystem=$('ecosystem-filter').value,tag=$('capability-filter').value;
    if(category&&project.category!==category)return false;
    if(ecosystem&&project.ecosystem!==ecosystem)return false;
    if(tag&&!(Array.isArray(project.tags)&&project.tags.includes(tag)))return false;
    if(q){const haystack=normalize(Object.values(project).filter(v=>typeof v==='string').join(' '));if(!q.split(/\s+/).every(part=>haystack.includes(part)))return false;}
    return true;
  }
  function projectButton(project,className='project-name') {
    const button=make('button',project.name,className+(project.id==='nodelift'?' nodelift':''));
    button.type='button';button.append(make('span','↗'));button.setAttribute('aria-label',tr('Apri scheda di ','Open project details for ')+project.name);
    button.addEventListener('click',()=>openProject(project));return button;
  }
  function renderAtlas() {
    if(!dataset)return;
    filtered=printing?[...dataset.projects]:dataset.projects.filter(matches);
    page=Math.min(page,Math.max(0,Math.ceil(filtered.length/pageSize)-1));
    const start=printing?0:page*pageSize,end=printing?filtered.length:Math.min(start+pageSize,filtered.length);
    const rows=filtered.slice(start,end);
    $('comparison-body').replaceChildren();$('mobile-projects').replaceChildren();
    $('atlas-error').hidden=true;$('atlas-empty').hidden=filtered.length>0;
    document.querySelector('.table-scroll').hidden=filtered.length===0;
    $('table-instruction').hidden=filtered.length===0;
    const nodeUpdated=dataset.nodelift_updated || dataset.updated;
    $('atlas-status').textContent=language==='zh-Hans' ? `${filtered.length} / ${dataset.projects.length} 个项目 · 其他项目核查 ${dataset.updated} · NodeLift 更新 ${nodeUpdated}` : tr('{0} di {1} progetti · altre schede verificate {2} · NodeLift aggiornato {3}','{0} of {1} projects · other entries checked {2} · NodeLift updated {3}',filtered.length,dataset.projects.length,dataset.updated,nodeUpdated);
    $('page-summary').textContent=filtered.length?tr('{0}–{1} di {2} risultati','{0}–{1} of {2} results',start+1,end,filtered.length):tr('0 risultati','0 results');
    $('previous-page').disabled=page===0;$('next-page').disabled=end>=filtered.length;
    const scope=dataset.scope ? (language==='zh-Hans' && dataset.scope.zh ? dataset.scope.zh : tr(dataset.scope.it || dataset.scope.en || '',dataset.scope.en || '')) : '';
    $('dataset-scope').textContent=scope;
    for(const project of rows){
      const row=make('tr');const name=make('th');name.scope='row';name.append(projectButton(project),make('span',uiLabel('category',project.category),'project-category'));row.append(name);
      for(const key of ['architecture','mobile_compute','evidence','capacity','host','android','ios','license']){const cell=make('td');cell.append(make('span',safeText(project[key]),'cell-excerpt'));row.append(cell);}
      $('comparison-body').append(row);
      const mobile=make('article',undefined,'mobile-project');mobile.append(projectButton(project),make('span',uiLabel('category',project.category)+' / '+uiLabel('ecosystem',project.ecosystem),'project-category'));
      const fields=make('dl');for(const key of ['mobile_compute','capacity','evidence']){const item=make('div');item.append(make('dt',tr(...fieldLabels[key])),make('dd',safeText(project[key])));fields.append(item);}mobile.append(fields);
      const detail=make('button',tr('Scheda completa + fonti ↗','Full details + sources ↗'),'detail-button');detail.type='button';detail.addEventListener('click',()=>openProject(project));mobile.append(detail);$('mobile-projects').append(mobile);
    }
    requestAnimationFrame(updateTableCue);
  }
  function updateTableCue(){const table=document.querySelector('.table-scroll');document.querySelector('.table-viewport').classList.toggle('at-end',table.scrollLeft+table.clientWidth>=table.scrollWidth-2);}
  document.querySelector('.table-scroll').addEventListener('scroll',updateTableCue,{passive:true});
  window.addEventListener('resize',updateTableCue);
  function resetFilters(){filterIds.forEach(id=>$(id).value='');page=0;renderAtlas();syncURL();}
  $('atlas-filters').addEventListener('submit',event=>event.preventDefault());
  $('atlas-filters').addEventListener('reset',event=>{event.preventDefault();resetFilters();});
  $('empty-reset').addEventListener('click',resetFilters);
  for(const id of filterIds)$(id).addEventListener(id==='project-search'?'input':'change',()=>{page=0;renderAtlas();syncURL();});
  function changePage(change){page+=change;renderAtlas();$('atlas-filters').scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});}
  $('previous-page').addEventListener('click',()=>changePage(-1));$('next-page').addEventListener('click',()=>changePage(1));
  function sourceLink(source){
    if(!source||typeof source.url!=='string')return null;
    let url;try{url=new URL(source.url);}catch(_){return null;}
    if(!['https:','http:'].includes(url.protocol))return null;
    const anchor=make('a',typeof source.label==='string'?source.label:url.hostname);anchor.href=url.href;anchor.target='_blank';anchor.rel='noopener noreferrer';return anchor;
  }
  function renderProject(project){
    $('project-dialog-title').textContent=project.name;
    $('project-dialog-category').textContent=uiLabel('category',project.category)+' / '+uiLabel('ecosystem',project.ecosystem);
    $('project-dialog-meta').textContent=[project.stage,project.license,project.checked].filter(v=>typeof v==='string').join(' · ');
    $('project-dialog-fields').replaceChildren();
    for(const [key,labels] of Object.entries(fieldLabels)){const field=make('div');field.append(make('dt',tr(...labels)),make('dd',safeText(project[key])));$('project-dialog-fields').append(field);}
    $('project-dialog-sources').replaceChildren();
    for(const source of Array.isArray(project.sources)?project.sources:[]){const link=sourceLink(source);if(link){const item=make('li');item.append(link);$('project-dialog-sources').append(item);}}
    if(!$('project-dialog-sources').children.length)$('project-dialog-sources').append(make('li',tr('Nessun collegamento valido nel dataset.','No valid links in the dataset.')));
    $('copy-project-status').textContent='';
  }
  function openProject(project){
    selectedProject=project;priorFocus=document.activeElement;renderProject(project);
    if(!$('project-dialog').open)$('project-dialog').showModal();
    $('project-dialog').scrollTop=0;syncURL();
  }
  $('close-project').addEventListener('click',()=>$('project-dialog').close());
  $('project-dialog').addEventListener('close',()=>{selectedProject=null;syncURL();if(priorFocus?.isConnected)priorFocus.focus({preventScroll:true});});
  $('project-dialog').addEventListener('click',event=>{if(event.target!==$('project-dialog'))return;const rect=event.target.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)event.target.close();});
  $('copy-project-link').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(location.href);$('copy-project-status').textContent=tr('Link alla scheda copiato.','Project link copied.');}catch(_){$('copy-project-status').textContent=tr('Copia l’indirizzo dalla barra del browser: contiene già questa scheda.','Copy the address from your browser: it already includes this project.');}});
  async function loadAtlas(){
    if(fetching)return;fetching=true;$('atlas-error').hidden=true;$('atlas-empty').hidden=true;$('retry-atlas').disabled=true;
    $('atlas-status').textContent=tr('Caricamento dell’atlante documentato…','Loading the source-backed atlas…');$('comparison-table').setAttribute('aria-busy','true');
    try{
      const response=await fetch('data/comparison.json',{cache:'no-cache'});if(!response.ok)throw Error('Atlas unavailable');
      const data=await response.json();
      if(data.schema_version!==1||!Array.isArray(data.projects)||typeof data.updated!=='string'||!data.projects.every(p=>p&&typeof p.id==='string'&&typeof p.name==='string'))throw Error('Atlas format unsupported');
      if(new Set(data.projects.map(p=>p.id)).size!==data.projects.length)throw Error('Atlas ids are not unique');
      dataset=data;renderAtlas();
      const requested=new URLSearchParams(location.search).get('project');const project=dataset.projects.find(p=>p.id===requested);if(project)openProject(project);
    }catch(_){
      $('atlas-error').hidden=false;$('atlas-status').textContent=tr('Dataset non disponibile · nessuna riga simulata','Dataset unavailable · no simulated entries');
      document.querySelector('.table-scroll').hidden=true;$('table-instruction').hidden=true;$('page-summary').textContent='';
      $('previous-page').disabled=true;$('next-page').disabled=true;
    }finally{fetching=false;$('retry-atlas').disabled=false;$('comparison-table').setAttribute('aria-busy','false');}
  }
  $('retry-atlas').addEventListener('click',loadAtlas);
  function updateDeck(){
    $('deck-position').textContent=String(chapterIndex+1).padStart(2,'0')+' / '+String(chapters.length).padStart(2,'0');
    $('deck-previous').disabled=chapterIndex===0;$('deck-next').disabled=chapterIndex===chapters.length-1;
  }
  function moveChapter(delta){
    chapterIndex=Math.max(0,Math.min(chapters.length-1,chapterIndex+delta));commandedChapter=chapterIndex;
    clearTimeout(commandTimer);commandTimer=setTimeout(()=>{commandedChapter=null;},1400);
    updateDeck();chapters[chapterIndex].scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  }
  function enterPresentation(){chapterIndex=0;presentation=true;document.body.classList.add('presentation');$('deck-controls').hidden=false;$('presentation-toggle').setAttribute('aria-pressed','true');moveChapter(0);$('deck-next').focus({preventScroll:true});}
  function exitPresentation(){
    presentation=false;commandedChapter=null;clearTimeout(commandTimer);document.body.classList.remove('presentation');$('deck-controls').hidden=true;$('presentation-toggle').setAttribute('aria-pressed','false');
    const heading=chapters[chapterIndex].querySelector('h1,h2');if(heading){heading.setAttribute('tabindex','-1');heading.focus({preventScroll:true});}
  }
  const releaseChapterCommand=()=>{commandedChapter=null;clearTimeout(commandTimer);};
  window.addEventListener('wheel',releaseChapterCommand,{passive:true});window.addEventListener('touchstart',releaseChapterCommand,{passive:true});
  $('presentation-toggle').addEventListener('click',()=>presentation?exitPresentation():enterPresentation());
  $('deck-previous').addEventListener('click',()=>moveChapter(-1));$('deck-next').addEventListener('click',()=>moveChapter(1));$('deck-exit').addEventListener('click',exitPresentation);
  document.addEventListener('keydown',event=>{
    if(!presentation||$('project-dialog').open||event.target.closest('input,select,textarea,[contenteditable="true"],.step,.table-scroll'))return;
    if(event.key==='Escape'){exitPresentation();return;}
    if(['ArrowRight','ArrowDown','PageDown'].includes(event.key)){event.preventDefault();moveChapter(1);}
    if(['ArrowLeft','ArrowUp','PageUp'].includes(event.key)){event.preventDefault();moveChapter(-1);}
  });
  let scrollQueued=false;
  window.addEventListener('scroll',()=>{
    if(scrollQueued)return;scrollQueued=true;
    requestAnimationFrame(()=>{scrollQueued=false;const header=document.querySelector('.masthead').offsetHeight+30;let closest=0,distance=Infinity;chapters.forEach((chapter,i)=>{const d=Math.abs(chapter.getBoundingClientRect().top-header);if(d<distance){closest=i;distance=d;}});if(!presentation||commandedChapter===null)chapterIndex=closest;document.querySelectorAll('.primary-nav a').forEach(a=>a.classList.toggle('active',a.hash==='#'+chapters[chapterIndex].id));if(presentation)updateDeck();});
  },{passive:true});
  function buildPrintDetails(){
    document.querySelector('.print-projects')?.remove();if(!dataset)return;
    const appendix=make('section',undefined,'print-projects print-only');appendix.append(make('h2',tr('Atlante completo · campi e fonti','Full atlas · fields and sources')),make('p',language==='zh-Hans' ? `条目为英文。其他项目核查：${dataset.updated}；NodeLift 更新：${dataset.nodelift_updated || dataset.updated}` : tr('Schede in inglese. Altre schede verificate: ','Entries in English. Other entries checked: ')+dataset.updated+' · NodeLift: '+(dataset.nodelift_updated || dataset.updated)));
    for(const project of dataset.projects){const article=make('article',undefined,'print-project');article.append(make('h3',project.name),make('p',uiLabel('category',project.category)+' / '+uiLabel('ecosystem',project.ecosystem)));const fields=make('dl');for(const [key,labels] of Object.entries(fieldLabels)){const item=make('div');item.append(make('dt',tr(...labels)),make('dd',safeText(project[key])));fields.append(item);}article.append(fields);const sources=make('ul');for(const source of project.sources||[]){const link=sourceLink(source);if(link){const item=make('li');item.append(link);sources.append(item);}}article.append(sources);appendix.append(article);}
    $('main').append(appendix);
  }
  let wasMethodOpen=false;
  const printMedia=matchMedia('print');
  function restoreScreenAfterPrint(){
    if(!printing)return;
    printing=false;document.querySelector('.methodology-summary').open=wasMethodOpen;
    document.querySelector('.print-projects')?.remove();renderAtlas();
  }
  function restoreIfScreen(){if(printing&&!printMedia.matches)restoreScreenAfterPrint();}
  $('print-page').addEventListener('click',()=>{try{window.print();}finally{restoreIfScreen();}});
  window.addEventListener('beforeprint',()=>{if(printing)return;printing=true;wasMethodOpen=document.querySelector('.methodology-summary').open;document.querySelector('.methodology-summary').open=true;renderAtlas();buildPrintDetails();});
  window.addEventListener('afterprint',restoreScreenAfterPrint);
  printMedia.addEventListener('change',event=>{if(!event.matches)restoreScreenAfterPrint();});
  window.addEventListener('focus',restoreIfScreen);
  window.addEventListener('pageshow',restoreIfScreen);
  document.addEventListener('pointerdown',restoreIfScreen,{capture:true});
  window.addEventListener('popstate',()=>{const state=new URLSearchParams(location.search);language=locale.resolveLanguage(state.get('lang'),null);applyLanguage();filterIds.forEach((id,i)=>$(id).value=state.get(filterParams[i])||'');page=0;renderAtlas();if(dataset){const p=dataset.projects.find(p=>p.id===state.get('project'));if(p)openProject(p);else if($('project-dialog').open)$('project-dialog').close();}});
  const initialURL=new URL(location.href);initialURL.searchParams.set('lang',language);history.replaceState(null,'',initialURL);
  applyLanguage();loadAtlas();
})();
