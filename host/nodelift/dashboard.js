'use strict';
const $ = id => document.getElementById(id);
const isSessionFragment = value => /^[A-Za-z0-9_-]{32,}$/.test(value);
let key = isSessionFragment(location.hash.slice(1)) ? location.hash.slice(1) : '';
try {
  key = key || sessionStorage.getItem('nodelift-admin') || '';
  if (key) sessionStorage.setItem('nodelift-admin', key);
} catch (_) { /* A fragment session still works when storage is unavailable. */ }
if(isSessionFragment(location.hash.slice(1)))history.replaceState(null, '', '/');
window.addEventListener('hashchange', () => { if (isSessionFragment(location.hash.slice(1))) location.reload(); });
let snapshot = null;
let engineSnapshot = null;
let authenticated = false;
let refreshing = false;
let configurationDirty = false;
let actionPending = false;
let engineSignature = '';
let nodeSignature = '';
let jobSignature = '';
let clientAccess = null;
let clientAccessEpoch = 0;
let clientAccessTimer;
let clientRevealTimer;
let clientKeyVisible = false;
const configFields = [['target-model','target_model'],['draft-model','draft_model'],['context-size','n_ctx'],['threads','threads'],['gpu-layers','gpu_layers']];
const sessionMessage = 'Questa scheda non ha una sessione NodeLift valida. Sul Mac apri scripts/open-dashboard.command dalla cartella del progetto per riaprire la dashboard con accesso. Non serve reinstallare l’app sul telefono.';
const modeNames = {host: 'Solo computer', local_draft: 'Proposte locali', remote_draft: 'Proposte dal telefono'};
const stateNames = {completed:'Completata', running:'In corso', queued:'In attesa', failed:'Non riuscita', cancelled:'Interrotta', timed_out:'Tempo scaduto', expired:'Scaduta', thermal_pause:'Pausa termica', loading:'Caricamento', stopped:'Interrotta'};
function el(tag, text, cls) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; }
function showError(error, id='error') { $(id).textContent = error.message || String(error); $(id).hidden = false; }
function clearError(id='error') { $(id).hidden = true; $(id).textContent = ''; }
function number(value, digits=2) { return typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString('it-IT',{minimumFractionDigits:digits,maximumFractionDigits:digits}) : '—'; }
function gib(value) { return typeof value === 'number' ? number(value / 1073741824,1) + ' GiB' : 'Non rilevata'; }
function quantile(values,q) { const a=[...values].filter(Number.isFinite).sort((x,y)=>x-y); return a.length ? a[Math.ceil(q*a.length)-1] : null; }
function when(epoch) { const d=new Date(epoch*1000); return Number.isFinite(d.getTime()) ? d.toLocaleString('it-IT',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'}) : '—'; }
function empty(title, detail) { const box=el('div',undefined,'empty'); box.append(el('span','⌁','empty-symbol'),el('h3',title),el('p',detail)); return box; }
function metric(list,label,value,small=false) { const wrap=el('div',undefined,'metric'); wrap.append(el('dt',label),el('dd',value,small?'small':''));list.append(wrap); }
function action(label,fn,{quiet=false,disabled=false,danger=false}={}) { const b=el('button',label,quiet?'quiet':''); if(danger)b.classList.add('danger');b.disabled=disabled;b.onclick=async()=>{b.disabled=true;clearError();try{await fn();}catch(e){showError(e);}finally{b.disabled=disabled;}};return b; }
function sessionReady(ready) {
  authenticated=ready;
  $('invite').disabled=!ready;
  $('export').disabled=!ready || !snapshot;
  $('job-filter').disabled=!ready || !snapshot;
  $('open-client-access').disabled=!ready;
  $('session-dot').className='status-dot '+(ready?'ready':'error');
  $('session-label').textContent=ready?'Sessione locale attiva':'Accesso richiesto';
  if(!ready){
    hideClientAccess();
    $('pairing').hidden=true;$('ticket').value='';snapshot=null;engineSnapshot=null;
    $('online').textContent='—';$('registered-label').textContent='Sessione non disponibile';
    $('engine-summary').textContent='Accesso richiesto';$('engine-backend').textContent='Sessione locale necessaria';
    $('engine-state').textContent='ACCESSO RICHIESTO';$('engine-state').className='chip neutral';
    $('engine-notice').textContent='Apri la dashboard con il collegamento di sessione per usare i controlli del laboratorio.';
    $('nodes').replaceChildren(empty('Accedi alla tua sessione','Usa il collegamento completo generato da NodeLift sul computer.'));
    $('topology-nodes').replaceChildren(el('p','La topologia sarà visibile dopo l’accesso.','muted'));
    $('jobs').replaceChildren(el('p','Le misure saranno visibili dopo l’accesso.','muted'));
    $('engine-runs').replaceChildren(el('p','Le esecuzioni saranno visibili dopo l’accesso.','muted'));
    $('completed-count').textContent='—';$('nav-count').textContent='—';
    nodeSignature='';jobSignature='';engineSignature='';
  }
  updateEngineControls();
}
async function api(path, body) {
  if(!key){sessionReady(false);throw Error(sessionMessage);}
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),body===undefined?9000:60000);
  try {
    const r=await fetch('/admin/'+path,{method:body===undefined?'GET':'POST',headers:{Authorization:'Bearer '+key,'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:controller.signal});
    if(r.status===401){sessionReady(false);throw Error(sessionMessage);}
    let value;try{value=await r.json();}catch(_){throw Error('Il server non ha restituito una risposta leggibile.');}
    if(!r.ok){const error=Error(value.error||'Richiesta non riuscita');error.status=r.status;throw error;}
    return value;
  } catch(e) { if(e.name==='AbortError')throw Error('Il computer non ha risposto in tempo. Verifica che NodeLift sia attivo.');throw e; }
  finally {clearTimeout(timer);}
}
function renderNodes() {
  const nodes=snapshot.nodes||[];
  const online=nodes.filter(n=>n.online&&!n.revoked).length;
  $('online').textContent=online;
  $('nav-count').textContent=nodes.length;
  $('registered-label').textContent=nodes.length+' dispositiv'+(nodes.length===1?'o associato':'i associati');
  $('cluster-caption').textContent=online?'Disponibilità e capacità rilevate':'Dispositivi in attesa di connessione';
  const signature=JSON.stringify(nodes.map(n=>({id:n.id,name:n.name,online:n.online,revoked:n.revoked,capabilities:n.capabilities})))+JSON.stringify((snapshot.jobs||[]).filter(j=>['queued','running'].includes(j.state)).map(j=>j.node));
  if(signature===nodeSignature)return;
  nodeSignature=signature;
  const container=$('nodes');container.replaceChildren();
  const peers=$('topology-nodes');peers.replaceChildren();
  if(!nodes.length){container.append(empty('Il primo nodo cambia la prospettiva','Crea un invito, apri la companion sul telefono e associa il dispositivo.'));peers.append(el('p','Nessun nodo associato.','muted'));}
  for(const n of nodes){
    const c=n.capabilities||{};
    const peer=el('div',undefined,'peer '+(n.online&&!n.revoked?'online':''));const dot=el('span',undefined,'status-dot '+(n.online&&!n.revoked?'ready':''));dot.setAttribute('aria-hidden','true');peer.append(dot,el('span',n.name,'peer-name'),el('span',n.revoked?'REVOCATO':n.online?'ONLINE':'OFFLINE','peer-state'));peers.append(peer);
    const card=el('article',undefined,'node '+(n.online&&!n.revoked?'online-node':''));
    const heading=el('div',undefined,'node-head'),icon=el('span',undefined,'device-symbol');icon.setAttribute('aria-hidden','true');
    const label=el('div',undefined,'node-heading');label.append(el('h3',n.name),el('small',c.os||'Sistema non rilevato'));
    const state=el('div',undefined,'node-status');state.append(el('span',n.revoked?'REVOCATO':n.online?'● CONNESSO':'○ OFFLINE','state '+(n.online&&!n.revoked?'':'offline')),el('span',c.engine_ready?'LLM PRONTO':'QUALIFICAZIONE','chip '+(c.engine_ready?'':'neutral')));heading.append(icon,label,state);card.append(heading);
    const d=el('dl');metric(d,'RAM fisica',gib(c.physical_memory_bytes));metric(d,'Disponibile al sistema¹',gib(c.available_memory_bytes));metric(d,'Stato termico',c.thermal||'Non rilevato');metric(d,'Collegamento',c.transport||'Non rilevato',true);metric(d,'Batteria',typeof c.battery_percent==='number'?number(c.battery_percent,0)+'%':'Non rilevata');metric(d,'Companion',c.app_version||'Non rilevata');card.append(d);
    const footer=el('div',undefined,'node-footer'),buttons=el('div',undefined,'actions');
    const pending=(snapshot.jobs||[]).some(j=>j.node===n.id&&['queued','running'].includes(j.state));
    for(const [label,kind] of [['Rete rapida','network'],['Rete con pause','network_paced'],['Test CPU','cpu']])buttons.append(action(label,async()=>{await api('job',{node_id:n.id,kind});await refresh();},{disabled:!n.online||!!n.revoked||pending||!(c.supported_jobs||[]).includes(kind)}));
    const revoke=action('Revoca associazione',async()=>{await api('revoke',{node_id:n.id});await refresh();},{quiet:true,danger:true,disabled:!!n.revoked});revoke.classList.add('revoke-action');footer.append(buttons,revoke);card.append(footer,el('p','¹ Indicatore del sistema operativo. Non è RAM già assegnata al modello.','node-footnote'));container.append(card);
  }
  renderRemoteNodes();
}
function renderRemoteNodes() {
  const select=$('remote-node'),selected=select.value;
  const nodes=(snapshot?.nodes||[]).filter(n=>n.online&&!n.revoked&&n.capabilities?.engine_ready);
  select.replaceChildren();const placeholder=el('option',nodes.length?'Seleziona un nodo':'Nessun nodo LLM pronto');placeholder.value='';select.append(placeholder);
  for(const n of nodes){const o=el('option',n.name);o.value=n.id;select.append(o);}
  if(nodes.some(n=>n.id===selected))select.value=selected;
  else if(nodes.length===1)select.value=nodes[0].id;
  updateEngineControls();
}
function renderJobs() {
  if(!snapshot){$('job-filter').disabled=true;return;}
  const jobs=snapshot.jobs||[],filter=$('job-filter').value;
  $('completed-count').textContent=jobs.filter(j=>j.state==='completed').length;
  const signature=JSON.stringify(jobs)+filter;if(signature===jobSignature)return;jobSignature=signature;
  const container=$('jobs');container.replaceChildren();
  const visible=jobs.filter(j=>filter==='all'||(filter==='network'?j.kind.startsWith('network'):j.kind==='cpu'));
  if(!visible.length){container.append(empty('Nessuna misura in questa vista','Avvia una prova dal dispositivo per raccogliere i primi campioni.'));return;}
  for(const j of visible){
    const node=(snapshot.nodes||[]).find(n=>n.id===j.node),kind=j.kind==='network_paced'?'Rete con pause':j.kind==='network'?'Rete rapida':'CPU sintetica';
    const box=el('article',undefined,'job'),heading=el('div',undefined,'job-summary'),title=el('h3',kind,'job-title');title.append(el('span',' / '+(node?.name||j.node)));
    const meta=el('div',undefined,'job-meta');meta.append(el('span',stateNames[j.state]||j.state,'chip '+(j.state==='completed'?'':['failed','timed_out','thermal_pause'].includes(j.state)?'warn':'neutral')),el('time',when(j.created)));heading.append(title,meta);box.append(heading);
    const samples=j.result?.samples||[];
    if(j.kind.startsWith('network')&&samples.length){
      const groups=el('div',undefined,'job-metrics');
      for(const pace of [...new Set(samples.filter(s=>s.kind==='rtt').map(s=>s.pace_ms||0))].sort((a,b)=>a-b)){
        const rows=samples.filter(s=>s.kind==='rtt'&&(s.pace_ms||0)===pace),times=rows.map(s=>s.ms),connections=new Set(rows.map(s=>s.connection_id).filter(Boolean));
        const group=el('div',undefined,'rtt-group');group.append(el('span','PAUSA '+pace+' MS','micro'));const values=el('div',undefined,'rtt-values');
        for(const [q,label] of [[.5,'p50'],[.95,'p95']]){const tuple=el('div',undefined,'rtt-tuple');tuple.append(el('strong',number(quantile(times,q))),el('span','ms','rtt-unit'),el('span',label,'rtt-label'));values.append(tuple);}
        group.append(values,el('small',times.length+' campioni · '+connections.size+' connession'+(connections.size===1?'e':'i')));groups.append(group);
      }
      box.append(groups);const transfers=el('div',undefined,'transfer-summary');
      for(const transfer of ['download','upload'])for(const size of [...new Set(samples.filter(s=>s.kind===transfer).map(s=>s.bytes))].sort((a,b)=>a-b)){
        const rows=samples.filter(s=>s.kind===transfer&&s.bytes===size),ms=rows.reduce((a,s)=>a+s.ms,0),bytes=rows.reduce((a,s)=>a+s.bytes,0);if(ms>0){const line=el('span',(transfer==='download'?'Mac → nodo':'Nodo → Mac')+' · '+number(size/1024,0)+' KiB: ');line.append(el('strong',number(bytes/ms/1000)+' MB/s'));transfers.append(line);}
      }
      if(transfers.children.length)box.append(transfers);
    }
    if(j.kind==='cpu'&&samples.length){const row=samples.find(s=>s.kind==='cpu');if(row){const cpu=el('p',number(row.iterations,0)+' iterazioni / '+number(row.ms,0)+' ms','cpu-result');cpu.append(el('small','Kernel sintetico FP32. Non è una misura di prestazioni LLM.'));box.append(cpu);}}
    if(j.result?.note)box.append(el('p',j.result.note,'job-note'));container.append(box);
  }
}
function optionsForModels(select,models,placeholder) {
  const selected=select.value;
  const signature=JSON.stringify(models.map(m=>[m.path||m.id,m.name,m.bytes]));
  if(select.dataset.models===signature)return;
  select.dataset.models=signature;select.replaceChildren();const blank=el('option',placeholder);blank.value='';select.append(blank);
  for(const m of models){const option=el('option',(m.name||m.id)+(typeof m.bytes==='number'?' · '+gib(m.bytes):''));option.value=m.path||m.id;select.append(option);}
  if(models.some(m=>(m.path||m.id)===selected))select.value=selected;
}
function firstNumber(object,keys){for(const key of keys)if(typeof object[key]==='number'&&Number.isFinite(object[key]))return object[key];return null;}
function renderRuns(runs) {
  const signature=JSON.stringify(runs);if(signature===engineSignature)return;engineSignature=signature;
  $('run-count').textContent=runs.length?runs.length+' ESECUZION'+(runs.length===1?'E':'I'):'NESSUNA ESECUZIONE';
  const box=$('engine-runs');box.replaceChildren();if(!runs.length){box.append(el('p','L’output e i tempi misurati appariranno dopo un’esecuzione. Nessun risultato simulato.','muted'));return;}
  for(const r of [...runs].sort((a,b)=>(b.created||0)-(a.created||0))){
    const card=el('article',undefined,'engine-run'),head=el('div',undefined,'run-heading');
    head.append(el('span',(modeNames[r.mode]||r.mode||'Generazione')+' · '+(stateNames[r.status]||r.status||'Stato non disponibile'),'run-title'),el('time',when(r.created)));card.append(head);
    const m=r.metrics||{},metrics=el('div',undefined,'run-metrics');
    const tps=firstNumber(m,['tokens_per_second','decode_tps','decode_tokens_per_second','tps']);
    const tokens=firstNumber(m,['generated_tokens','output_tokens','tokens']);
    const accepted=firstNumber(m,['accepted_tokens','accepted']),proposed=firstNumber(m,['proposed_tokens','proposed','draft_tokens']);
    const seconds=firstNumber(m,['elapsed_seconds','total_seconds','elapsed_s']),totalMs=firstNumber(m,['total_ms','elapsed_ms']);
    const ttft=firstNumber(m,['ttft_ms','time_to_first_token_ms']);
    const remoteWait=r.mode==='remote_draft'?firstNumber(m,['remote_wait_ms']):null;
    for(const [value,label,digits] of [[tps,'token/s',2],[tokens,'token generati',0],[seconds!==null?seconds:totalMs!==null?totalMs/1000:null,'s totali',2],[ttft,'ms primo token',1],[remoteWait!==null?remoteWait/1000:null,'s attesa remota totale',2]])if(value!==null){const item=el('span',undefined,'run-metric');item.append(el('strong',number(value,digits)),document.createTextNode(label));metrics.append(item);}
    if(accepted!==null&&proposed!==null){const item=el('span',undefined,'run-metric');item.append(el('strong',number(accepted,0)+' / '+number(proposed,0)),document.createTextNode('proposte accettate'));metrics.append(item);}
    if(metrics.children.length)card.append(metrics);
    if(r.error)card.append(el('p',r.error,'run-error'));
    if(r.text)card.append(el('pre',r.text,'output-text'));else if(['queued','running','loading'].includes(r.status))card.append(el('p','Elaborazione in corso…','muted'));
    if(r.prompt){
      const details=el('details',undefined,'run-prompt');details.append(el('summary','Prompt e parametri'),el('p',r.prompt),el('p','Limite output: '+(r.max_tokens??'—')+' token · blocco draft: '+(r.draft_k??'—')));
      if(r.mode==='remote_draft')details.append(el('p','Timeout per proposta: '+number((r.remote_timeout_ms??30000)/1000,3)+' s. L’attesa remota totale include lavoro del nodo e trasferimento; non è una misura della velocità di rete.'));
      const widths=(Array.isArray(r.blocks)?r.blocks:[]).map(b=>b.verification_batch_width).filter(w=>Number.isInteger(w)&&w>0);
      if(widths.length){const minimum=Math.min(...widths),maximum=Math.max(...widths);details.append(el('p','Larghezza batch di verifica: '+(minimum===maximum?minimum:minimum+'–'+maximum)+' posizioni (proposte + una posizione di controllo).'));}
      card.append(details);
    }
    box.append(card);
  }
}
function formConfiguration(){return {target_model:$('target-model').value,draft_model:$('draft-model').value||'',n_ctx:Number($('context-size').value),threads:Number($('threads').value),gpu_layers:Number($('gpu-layers').value)};}
function writeAppliedConfiguration(){
  const c=engineSnapshot?.config||{};
  for(const [id,name] of configFields)if(c[name]!==undefined)$(id).value=c[name]??'';
  configurationDirty=false;
}
function modelName(path){return (engineSnapshot?.models||[]).find(m=>(m.path||m.id)===path)?.name||path?.split(/[\\/]/).pop()||'Nessuno';}
function updateConfigurationState(){
  const applied=engineSnapshot?.config,form=formConfiguration();
  configurationDirty=!!applied&&configFields.some(([,name])=>String(form[name]??'')!==String(applied[name]??''));
  const hasTarget=!!applied?.target_model;
  $('configuration-status').textContent=configurationDirty?'Modifiche non applicate. Applica o ripristina prima di avviare.':hasTarget?'La configurazione visibile è applicata.':'Seleziona e applica un modello per iniziare.';
  $('configuration-status').className='configuration-status '+(configurationDirty?'dirty':'');
  $('configure').classList.toggle('needs-apply',configurationDirty);
  $('configure').textContent=configurationDirty?'Applica modifiche':hasTarget?'Configurazione applicata':'Applica configurazione';
  $('revert-config').hidden=!configurationDirty;
  $('applied-config-description').textContent=hasTarget?modelName(applied.target_model)+' · draft: '+modelName(applied.draft_model)+' · contesto '+applied.n_ctx+' · '+applied.threads+' thread · GPU '+applied.gpu_layers+' layer':'Nessun modello configurato.';
}
function updateEngineControls() {
  updateConfigurationState();
  const available=authenticated&&!!engineSnapshot?.available;
  const busy=!!engineSnapshot?.busy||actionPending;
  const configured=!!engineSnapshot?.config?.target_model;
  const mode=$('run-mode').value;
  for(const id of ['target-model','draft-model','context-size','threads','gpu-layers'])$(id).disabled=!available||busy;
  $('configure').disabled=!available||busy||!$('target-model').value||!configurationDirty;
  $('revert-config').disabled=!available||busy;
  $('run-mode').disabled=!available||busy;
  $('remote-node').disabled=!available||busy||mode!=='remote_draft';
  $('remote-timeout').disabled=!available||busy||mode!=='remote_draft';
  $('draft-k').disabled=!available||busy||mode==='host';
  $('max-tokens').disabled=!available||busy;
  $('prompt').disabled=!available||busy;
  const ready=mode==='host'||(mode==='local_draft'?!!engineSnapshot?.config?.draft_model:!!$('remote-node').value);
  $('start-run').disabled=!available||busy||!configured||!ready||configurationDirty||!$('prompt').value.trim();
  $('stop-run').disabled=!authenticated||!engineSnapshot?.busy||actionPending;
  $('mode-help').textContent=mode==='host'?'Baseline sul computer. Nessun lavoro LLM inviato ai telefoni.':mode==='local_draft'?'Target e draft sul computer: confronto necessario prima di attribuire un vantaggio alla rete.':'Il nodo genera proposte a blocchi; il target sul computer le verifica. Richiede una companion con motore LLM pronto.';
}
function remoteTimeoutMs(){
  const value=$('remote-timeout').value.trim();
  const seconds=value===''?30:Number(value);
  if(!Number.isFinite(seconds)||seconds<0.5||seconds>60)throw Error('Il timeout remoto deve essere compreso tra 0,5 e 60 secondi.');
  return Math.round(seconds*1000);
}
async function refreshEngine() {
  if(!authenticated)return;
  try {
    engineSnapshot=await api('engine/status');
    const available=!!engineSnapshot.available,busy=!!engineSnapshot.busy;
    $('engine-summary').textContent=busy?'In esecuzione':available?'Disponibile':'Non disponibile';
    $('engine-backend').textContent=engineSnapshot.backend||'Backend locale';
    $('engine-state').textContent=busy?'IN ESECUZIONE':available?'SPERIMENTALE':'NON DISPONIBILE';
    $('engine-state').className='chip '+(available?'':'neutral');
    $('engine-notice').className='notice '+(available?'good':'');
    $('engine-notice').textContent=available?'Motore sperimentale. Seleziona i modelli locali e confronta le strategie sullo stesso prompt. La disponibilità del motore non dimostra un’accelerazione.':'Il motore non è ancora disponibile in questa sessione. Associazione e diagnostica dei dispositivi restano utilizzabili.';
    optionsForModels($('target-model'),engineSnapshot.models||[],'Seleziona un modello target');
    optionsForModels($('draft-model'),engineSnapshot.models||[],'Nessun draft selezionato');
    if(!configurationDirty)writeAppliedConfiguration();
    renderRuns(engineSnapshot.runs||[]);updateEngineControls();
  } catch(e) {
    engineSnapshot=null;$('engine-summary').textContent='Non disponibile';$('engine-backend').textContent='Configurazione richiesta';$('engine-state').textContent='NON DISPONIBILE';$('engine-state').className='chip neutral';
    $('engine-notice').className='notice';$('engine-notice').textContent=e.status===404?'Questa versione del server offre associazione e diagnostica. I controlli LLM si attiveranno quando il motore sarà disponibile.':e.message;
    if(authenticated&&engineSignature==='')$('engine-runs').replaceChildren(el('p','L’output apparirà dopo la configurazione del motore e la prima esecuzione.','muted'));
    updateEngineControls();
  }
}
async function refresh() {
  if(refreshing)return;refreshing=true;
  try{snapshot=await api('status');sessionReady(true);renderNodes();renderJobs();$('updated-at').textContent=new Date().toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit',second:'2-digit'});await refreshEngine();}
  catch(e){$('session-label').textContent=authenticated?'Connessione da verificare':'Accesso richiesto';$('session-dot').className='status-dot error';showError(e);}
  finally{refreshing=false;}
}
$('invite').onclick=async()=>{clearError();$('invite').disabled=true;try{const ticket=await api('invite',{});$('ticket').value=JSON.stringify(ticket);$('pairing').hidden=false;$('expiry').textContent='Scade alle '+new Date(ticket.expires_at*1000).toLocaleTimeString('it-IT');$('pairing').scrollIntoView({behavior:'smooth',block:'center'});$('copy').focus({preventScroll:true});}catch(e){showError(e);}finally{$('invite').disabled=!authenticated;}};
$('copy').onclick=async()=>{try{await navigator.clipboard.writeText($('ticket').value);$('copy').textContent='Copiato';setTimeout(()=>$('copy').textContent='Copia invito',2000);}catch(e){$('ticket').select();showError(Error('Seleziona e copia manualmente l’invito.'));}};
$('hide').onclick=()=>{$('pairing').hidden=true;$('ticket').value='';$('invite').focus();};
$('export').onclick=()=>{if(!snapshot)return;const data={...snapshot,engine:engineSnapshot,exported_at:new Date().toISOString()};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download='nodelift-laboratory.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('job-filter').onchange=renderJobs;
for(const [id] of configFields)$(id).addEventListener('input',updateEngineControls);
$('revert-config').onclick=()=>{writeAppliedConfiguration();updateEngineControls();};
for(const id of ['run-mode','remote-node','prompt'])$(id).addEventListener('input',updateEngineControls);
$('configuration-form').onsubmit=async event=>{event.preventDefault();if($('configure').disabled)return;clearError('engine-error');actionPending=true;updateEngineControls();try{await api('engine/configure',{target_model:$('target-model').value,draft_model:$('draft-model').value||null,n_ctx:Number($('context-size').value),threads:Number($('threads').value),gpu_layers:Number($('gpu-layers').value)});configurationDirty=false;await refreshEngine();}catch(e){showError(e,'engine-error');}finally{actionPending=false;updateEngineControls();}};
$('run-form').onsubmit=async event=>{event.preventDefault();if($('start-run').disabled)return;clearError('engine-error');actionPending=true;updateEngineControls();try{await api('engine/run',{prompt:$('prompt').value.trim(),mode:$('run-mode').value,node_id:$('run-mode').value==='remote_draft'?$('remote-node').value:undefined,max_tokens:Number($('max-tokens').value),draft_k:Number($('draft-k').value),remote_timeout_ms:$('run-mode').value==='remote_draft'?remoteTimeoutMs():undefined});await refreshEngine();}catch(e){showError(e,'engine-error');}finally{actionPending=false;updateEngineControls();}};
$('stop-run').onclick=async()=>{clearError('engine-error');actionPending=true;updateEngineControls();try{await api('engine/stop',{});await refreshEngine();}catch(e){showError(e,'engine-error');}finally{actionPending=false;updateEngineControls();}};
function hideClientAccess(){
  clientAccessEpoch++;clientAccess=null;clientKeyVisible=false;clearTimeout(clientAccessTimer);clearTimeout(clientRevealTimer);
  $('client-access').hidden=true;$('client-base-url').value='';$('client-model').value='';$('client-key-display').textContent='Chiave nascosta';
  $('reveal-client-key').textContent='Mostra chiave';$('reveal-client-key').disabled=true;$('copy-client-key').disabled=true;
  $('client-access-status').textContent='';$('open-client-access').disabled=!authenticated;
}
$('open-client-access').onclick=async()=>{
  hideClientAccess();const epoch=clientAccessEpoch;$('client-access').hidden=false;$('open-client-access').disabled=true;$('client-access-status').textContent='Recupero accesso locale…';
  try{const access=await api('client-access');if(epoch!==clientAccessEpoch||!authenticated)return;
    if(typeof access.api_key!=='string'||typeof access.base_url!=='string'||typeof access.model!=='string')throw Error('Accesso API non disponibile.');
    clientAccess=access;$('client-base-url').value=access.base_url;$('client-model').value=access.model;
    $('reveal-client-key').disabled=false;$('copy-client-key').disabled=false;$('client-access-status').textContent='Chiave nascosta e assente dagli export. Questo pannello si chiude dopo due minuti o quando cambi scheda.';
    clientAccessTimer=setTimeout(hideClientAccess,120000);
  }catch(e){if(epoch===clientAccessEpoch)$('client-access-status').textContent=e.status===404?'Accesso API non disponibile in questa sessione del server.':'Accesso API non disponibile: '+e.message;}
  finally{if(epoch===clientAccessEpoch)$('open-client-access').disabled=!authenticated;}
};
$('close-client-access').onclick=hideClientAccess;
$('reveal-client-key').onclick=()=>{
  if(!clientAccess)return;clientKeyVisible=!clientKeyVisible;clearTimeout(clientRevealTimer);
  $('client-key-display').textContent=clientKeyVisible?clientAccess.api_key:'Chiave nascosta';$('reveal-client-key').textContent=clientKeyVisible?'Nascondi chiave':'Mostra chiave';
  if(clientKeyVisible)clientRevealTimer=setTimeout(()=>{clientKeyVisible=false;$('client-key-display').textContent='Chiave nascosta';$('reveal-client-key').textContent='Mostra chiave';},30000);
};
$('copy-client-key').onclick=async()=>{if(!clientAccess)return;try{await navigator.clipboard.writeText(clientAccess.api_key);$('client-access-status').textContent='Chiave copiata negli appunti. Incollala nel client locale che vuoi collegare.';}catch(_){$('client-access-status').textContent='Copia non disponibile. Usa Mostra chiave per copiarla manualmente.';}};
document.addEventListener('visibilitychange',()=>{if(document.hidden)hideClientAccess();});
const sections=[...document.querySelectorAll('main>section[id]')];
if('IntersectionObserver' in window){const observer=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){document.querySelectorAll('.rail nav a').forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+entry.target.id));}},{rootMargin:'-15% 0px -65% 0px'});sections.forEach(section=>observer.observe(section));}
sessionReady(false);refresh();setInterval(refresh,3000);
