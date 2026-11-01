'use strict';
const t = (key, ...args) => {const match=typeof key==='string'&&key.match(/^Provider request failed \(HTTP (\d{3})\)$/);return match?NodeLiftI18n.t('Provider request failed (HTTP {0})',match[1]):NodeLiftI18n.t(key,...args);};
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
let aboutMetadata = null;
let aboutVersionRequested = false;
let aboutVersionLoading = false;
let aboutVersionEpoch = 0;
let authenticated = false;
let refreshing = false;
let configurationDirty = false;
let actionPending = false;
const busyControls = new Map();
const pendingNodeActions = new Map();
const nodeActionFeedback = new Map();
let engineActionFeedback = null;
let configurationActionFeedback = null;
let nodeAnnouncement = null;
function setButtonLabel(button,message){
  const label=button.querySelector('[data-i18n]')||button;
  label.textContent=t(message);label.dataset.i18n=message;
}
function setControlBusy(id, busy, label, idleLabel) {
  const button=$(id);
  if(busy){const labelNode=button.querySelector('[data-i18n]')||button;busyControls.set(id,{label,idleLabel:busyControls.get(id)?.idleLabel||labelNode.dataset.i18n||idleLabel});}
  else{
    const previous=busyControls.get(id);busyControls.delete(id);
    button.removeAttribute('aria-busy');
    if(previous)setButtonLabel(button,previous.idleLabel);
  }
  renderBusyControls();
}
function renderBusyControls(){
  for(const [id,state] of busyControls){const button=$(id);button.disabled=true;button.setAttribute('aria-busy','true');setButtonLabel(button,state.label);}
}
function renderEngineFeedback(){
  const status=$('engine-action-status');
  status.hidden=!authenticated||!engineActionFeedback||engineActionFeedback.state==='busy';
  status.textContent=status.hidden?'':t(engineActionFeedback.message);
  if(engineActionFeedback)status.dataset.state=engineActionFeedback.state;
}

let engineSignature = '';
let nodeSignature = '';
let jobSignature = '';
let clientAccess = null;
let clientAccessEpoch = 0;
let clientAccessTimer;
let clientRevealTimer;
let clientKeyVisible = false;
const configFields = [['target-model','target_model'],['draft-model','draft_model'],['context-size','n_ctx'],['threads','threads'],['gpu-layers','gpu_layers']];
const sessionMessage = () => "This tab needs a new local session. Select Restore local session to reconnect.";
let restoringSession = false;
async function restoreSession() {
  if(restoringSession)return;
  restoringSession=true;
  const button=$('restore-session'),status=$('session-recovery-status');
  button.disabled=true;button.setAttribute('aria-busy','true');
  setButtonLabel(button,"Restoring session…");status.textContent='';
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);
  try {
    const response=await fetch('/admin/session/restore',{method:'POST',headers:{'Content-Type':'application/json','X-NodeLift-Session':'restore'},body:'{}',signal:controller.signal,credentials:'omit',cache:'no-store',redirect:'error'});
    if(!response.ok)throw Error('recovery failed');
    const value=await response.json();
    if(typeof value.token!=='string'||!isSessionFragment(value.token))throw Error('invalid session');
    // Reload discards requests that still use an expired key.
    try {sessionStorage.setItem('nodelift-admin',value.token);location.reload();}
    catch (_) {location.replace('/#'+value.token);location.reload();}
  } catch (_) {
    status.textContent=t("Session could not be restored. Check that NodeLift is running on this Mac, then try again.");
  } finally {
    clearTimeout(timer);restoringSession=false;button.disabled=false;
    button.removeAttribute('aria-busy');setButtonLabel(button,"Restore local session");
  }
}
$('restore-session').addEventListener('click',restoreSession);
const modeNames = {host: "Computer only", local_draft: "Local proposals", remote_draft: "Phone proposals", lookup: "Context reuse"};
const draftReasons = {no_measured_gain:"no measured gain",probe_cost_exceeded:"probe cost exceeded",remote_probe_timeout:"remote probe timed out: speed unknown",remote_failure:"remote draft unavailable",local_draft_failure:"draft model unavailable"};
const stateNames = {completed:"Completed", running:"Running", queued:"Queued", failed:"Failed", cancelled:"Stopped", timed_out:"Timed out", expired:"Expired", thermal_pause:"Thermal pause", loading:"Loading", stopped:"Stopped"};
function el(tag, text, cls) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; }
function showError(error, id='error') { $(id).dataset.message=error?.message || String(error ?? 'Request failed'); $(id).textContent = t($(id).dataset.message); $(id).hidden = false; }
function clearError(id='error') { $(id).hidden = true; $(id).textContent = ''; delete $(id).dataset.message; }
function number(value, digits=2) { return typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString(NodeLiftI18n.locale,{minimumFractionDigits:digits,maximumFractionDigits:digits}) : '-'; }
function gib(value) { return typeof value === 'number' ? number(value / 1073741824,1) + ' GiB' : t("Not detected"); }
function modelSize(bytes){return typeof bytes==='number'&&bytes>=0&&bytes<1073741824?number(bytes/1048576,1)+' MiB':gib(bytes);}
function quantile(values,q) { const a=[...values].filter(Number.isFinite).sort((x,y)=>x-y); return a.length ? a[Math.ceil(q*a.length)-1] : null; }
function when(epoch) { const d=new Date(epoch*1000); return Number.isFinite(d.getTime()) ? d.toLocaleString(NodeLiftI18n.locale,{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'}) : '-'; }
function empty(title, detail) { const box=el('div',undefined,'empty'); box.append(el('span','⌁','empty-symbol'),el('h3',title),el('p',detail)); return box; }
function metric(list,label,value,small=false) { const wrap=el('div',undefined,'metric'); wrap.append(el('dt',label),el('dd',value,small?'small':''));list.append(wrap); }
function announceNodeAction(nodeId,message){
  nodeAnnouncement=message?{nodeId,message}:null;
  const name=(snapshot?.nodes||[]).find(node=>node.id===nodeId)?.name;
  $('device-action-announcement').textContent=message?(name?name+': ':'')+t(message):'';
}
function action(label,fn,{quiet=false,disabled=false,danger=false,nodeId,kind,busyLabel}={}) {
  const pending=nodeId ? pendingNodeActions.get(nodeId) : null;
  const matchesPending=!!pending&&pending.kind===kind;
  const b=el('button',t(matchesPending?pending.message:label),quiet?'quiet':'');
  b.type='button';b.dataset.node=nodeId;b.dataset.action=kind;b.dataset.idleLabel=label;b.dataset.i18n=matchesPending?pending.message:label;
  if(danger)b.classList.add('danger');
  b.disabled=disabled||!authenticated||!!pending;
  if(matchesPending)b.setAttribute('aria-busy','true');
  b.onclick=async()=>{
    if(b.disabled||!authenticated||pendingNodeActions.has(nodeId))return;
    const requestedAt=Date.now()/1000,priorJobs=(snapshot?.jobs||[]).filter(job=>job.node===nodeId&&job.kind===kind).map(job=>job.id??job.created);
    pendingNodeActions.set(nodeId,{kind,message:busyLabel});
    nodeActionFeedback.set(nodeId,{state:'busy',message:busyLabel});clearError();renderNodes();
    try{
      await fn();
      if(authenticated){const message=kind==='revoke'?'Pairing revoked.':'Test requested. Follow its result in Measurements.';nodeActionFeedback.set(nodeId,{state:'success',kind,requestedAt,priorJobs,message});announceNodeAction(nodeId,message);}
    }catch(e){
      if(authenticated){const message='Request failed. Review the error and try again.';nodeActionFeedback.set(nodeId,{state:'error',message});announceNodeAction(nodeId,message);}
      showError(e);
    }finally{
      pendingNodeActions.delete(nodeId);
      if(authenticated&&snapshot)renderNodes();
      else for(const button of $('nodes').querySelectorAll('button'))if(button.dataset.node===nodeId){button.removeAttribute('aria-busy');setButtonLabel(button,button.dataset.idleLabel);button.disabled=true;}
    }
  };
  return b;
}
function updateSessionControls(){
  const pairingBusy=busyControls.has('invite')||busyControls.has('renew-invite');
  $('invite').disabled=!authenticated||pairingBusy;
  $('renew-invite').disabled=!authenticated||pairingBusy;
  $('export').disabled=!authenticated||!snapshot;
  $('job-filter').disabled=!authenticated||!snapshot;
  $('open-client-access').disabled=!authenticated||busyControls.has('open-client-access');
}
function sessionReady(ready) {
  authenticated=ready;
  $('session-recovery').hidden=ready;
  updateSessionControls();
  $('session-dot').className='status-dot '+(ready?'ready':'error');
  $('session-label').textContent=ready?t("Local session active"):t("Access required");
  if(!ready){
    hideClientAccess();nodeActionFeedback.clear();announceNodeAction(null,null);engineActionFeedback=null;configurationActionFeedback=null;
    aboutMetadata=null;aboutVersionRequested=false;aboutVersionLoading=false;aboutVersionEpoch++;
    pairing.clear();snapshot=null;engineSnapshot=null;
    $('online').textContent='-';$('registered-label').textContent=t("Session unavailable");
    $('engine-summary').textContent=t("Access required");$('engine-backend').textContent=t("Local session required");
    $('engine-state').textContent=t("ACCESS REQUIRED");$('engine-state').className='chip neutral';
    $('engine-notice').textContent=t("Open the dashboard using the session link to access laboratory controls.");
    $('nodes').replaceChildren(empty(t("Access your session"),t("Use the complete link generated by NodeLift on your computer.")));
    NodeLiftGraph.clear();
    $('jobs').replaceChildren(el('p',t("Measurements appear after access is established."),'muted'));
    $('engine-runs').replaceChildren(el('p',t("Runs appear after access is established."),'muted'));
    $('completed-count').textContent='-';$('nav-count').textContent='-';
    nodeSignature='';jobSignature='';engineSignature='';
  }
  renderAboutVersion();
  updateEngineControls();
  if(typeof updateLibraryControls==='function')updateLibraryControls();
}
async function api(path, body) {
  if(!key){sessionReady(false);throw Error(sessionMessage());}
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),body===undefined?(path.startsWith('models/')?30000:9000):60000);
  try {
    const r=await fetch('/admin/'+path,{method:body===undefined?'GET':'POST',headers:{Authorization:'Bearer '+key,'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:controller.signal});
    if(r.status===401){sessionReady(false);throw Error(sessionMessage());}
    let value;try{value=await r.json();}catch(_){throw Error("The server returned an unreadable response.");}
    if(!r.ok){const error=Error(value.error||t("Request failed"));error.status=r.status;throw error;}
    return value;
  } catch(e) { if(e.name==='AbortError')throw Error("The computer did not respond in time. Check that NodeLift is running.");throw e; }
  finally {clearTimeout(timer);}
}
function renderNodes() {
  const nodes=snapshot.nodes||[];
  for(const [id,feedback] of nodeActionFeedback){
    const finished=feedback.state==='success'&&feedback.kind!=='revoke'&&(snapshot.jobs||[]).some(job=>job.node===id&&job.kind===feedback.kind&&job.created>=feedback.requestedAt-1&&!(feedback.priorJobs||[]).includes(job.id??job.created)&&!['queued','running'].includes(job.state));
    if(!nodes.some(node=>node.id===id)||finished){nodeActionFeedback.delete(id);if(nodeAnnouncement?.nodeId===id)announceNodeAction(null,null);}
  }
  const online=nodes.filter(n=>n.online&&!n.revoked).length;
  $('online').textContent=online;
  $('nav-count').textContent=nodes.length;
  $('registered-label').textContent=nodes.length===1?t('1 paired device'):t('{0} paired devices',nodes.length);
  $('cluster-caption').textContent=online?t("Detected availability and capabilities"):t("Devices waiting to connect");
  const signature=JSON.stringify(nodes.map(n=>({id:n.id,name:n.name,online:n.online,revoked:n.revoked,capabilities:n.capabilities})))+JSON.stringify((snapshot.jobs||[]).filter(j=>['queued','running'].includes(j.state)).map(j=>j.node))+JSON.stringify([...pendingNodeActions])+JSON.stringify([...nodeActionFeedback]);
  if(signature===nodeSignature)return;
  nodeSignature=signature;
  const container=$('nodes'),focused=document.activeElement;
  const focusNode=container.contains(focused)?focused.dataset.node:null,focusAction=focusNode?focused.dataset.action:null;
  container.replaceChildren();
  if(!nodes.length){container.append(empty(t("Your first node opens new possibilities"),t("Create an invitation, open the companion on your phone and pair the device.")));}
  for(const n of nodes){
    const c=n.capabilities||{};
    const card=el('article',undefined,'node '+(n.online&&!n.revoked?'online-node':''));
    card.dataset.node=n.id;card.tabIndex=-1;
    const heading=el('div',undefined,'node-head'),icon=el('span',undefined,'device-symbol');icon.setAttribute('aria-hidden','true');
    const label=el('div',undefined,'node-heading');label.append(el('h3',n.name),el('small',c.os||t("System not detected")));
    const state=el('div',undefined,'node-status');state.append(el('span',n.revoked?t("REVOKED"):n.online?t("● CONNECTED"):t("○ OFFLINE"),'state '+(n.online&&!n.revoked?'':'offline')),el('span',c.engine_ready?t("LLM READY"):t("QUALIFICATION"),'chip '+(c.engine_ready?'':'neutral')));heading.append(icon,label,state);card.append(heading);
    const d=el('dl');metric(d,t("Physical RAM"),gib(c.physical_memory_bytes));metric(d,t(NodeLiftGraph.memoryScope(c))+"¹",gib(c.available_memory_bytes));metric(d,t("Thermal status"),t(c.thermal||"Not detected"));metric(d,t("Connection"),t(c.transport||"Not detected"),true);metric(d,t("Battery"),typeof c.battery_percent==='number'?number(c.battery_percent,0)+'%':t("Not detected"));metric(d,t('Companion'),c.app_version||t("Not detected"));card.append(d);
    const footer=el('div',undefined,'node-footer'),buttons=el('div',undefined,'actions');
    const pending=(snapshot.jobs||[]).some(j=>j.node===n.id&&['queued','running'].includes(j.state));
    for(const [label,kind] of [["Quick network test",'network'],["Paced network test",'network_paced'],["CPU test",'cpu']])buttons.append(action(label,async()=>{await api('job',{node_id:n.id,kind});await refresh();},{nodeId:n.id,kind,busyLabel:"Requesting test…",disabled:!n.online||!!n.revoked||pending||!(c.supported_jobs||[]).includes(kind)}));
    const revoke=action("Revoke pairing",async()=>{await api('revoke',{node_id:n.id});await refresh();},{nodeId:n.id,kind:'revoke',busyLabel:"Revoking pairing…",quiet:true,danger:true,disabled:!!n.revoked});revoke.classList.add('revoke-action');footer.append(buttons,revoke);card.append(footer);
    const feedback=nodeActionFeedback.get(n.id);
    if(pending||(feedback&&feedback.state!=='busy')){const status=el('p',t(pending?"A test is queued or running. Follow its result in Measurements.":feedback.message),'control-feedback');status.dataset.state=pending?'busy':feedback.state;status.setAttribute('role','status');card.append(status);}
    card.append(el('p',t("¹ Operating system indicator. This is not RAM already allocated to the model."),'node-footnote'));container.append(card);
  }
  if(focusNode){const card=[...container.children].find(item=>item.dataset.node===focusNode);const button=card&&[...card.querySelectorAll('button')].find(item=>item.dataset.action===focusAction);if(card){card.dataset.action=focusAction;(button&&!button.disabled?button:card).focus({preventScroll:true});}}
  renderRemoteNodes();
}
function renderRemoteNodes() {
  const select=$('remote-node'),selected=select.value;
  const nodes=(snapshot?.nodes||[]).filter(n=>n.online&&!n.revoked&&n.capabilities?.engine_ready);
  select.replaceChildren();const placeholder=el('option',nodes.length?t("Select a node"):t("No LLM node ready"));placeholder.value='';select.append(placeholder);
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
  if(!visible.length){container.append(empty(t("No measurements in this view"),t("Start a device test to collect the first samples.")));return;}
  for(const j of visible){
    const node=(snapshot.nodes||[]).find(n=>n.id===j.node),kind=j.kind==='network_paced'?t("Paced network test"):j.kind==='network'?t("Quick network test"):t("Synthetic CPU");
    const box=el('article',undefined,'job'),heading=el('div',undefined,'job-summary'),title=el('h3',kind,'job-title');title.append(el('span',' / '+(node?.name||j.node)));
    const meta=el('div',undefined,'job-meta');meta.append(el('span',t(stateNames[j.state]||j.state),'chip '+(j.state==='completed'?'':['failed','timed_out','thermal_pause'].includes(j.state)?'warn':'neutral')),el('time',when(j.created)));heading.append(title,meta);box.append(heading);
    const samples=j.result?.samples||[];
    if(j.kind.startsWith('network')&&samples.length){
      const groups=el('div',undefined,'job-metrics');
      for(const pace of [...new Set(samples.filter(s=>s.kind==='rtt').map(s=>s.pace_ms||0))].sort((a,b)=>a-b)){
        const rows=samples.filter(s=>s.kind==='rtt'&&(s.pace_ms||0)===pace),times=rows.map(s=>s.ms),connections=new Set(rows.map(s=>s.connection_id).filter(Boolean));
        const group=el('div',undefined,'rtt-group');group.append(el('span',t('PAUSE {0} MS',pace),'micro'));const values=el('div',undefined,'rtt-values');
        for(const [q,label] of [[.5,'p50'],[.95,'p95']]){const tuple=el('div',undefined,'rtt-tuple');tuple.append(el('strong',number(quantile(times,q))),el('span','ms','rtt-unit'),el('span',label,'rtt-label'));values.append(tuple);}
        group.append(values,el('small',connections.size===1?t('{0} samples · 1 connection',times.length):t('{0} samples · {1} connections',times.length,connections.size)));groups.append(group);
      }
      box.append(groups);const transfers=el('div',undefined,'transfer-summary');
      for(const transfer of ['download','upload'])for(const size of [...new Set(samples.filter(s=>s.kind===transfer).map(s=>s.bytes))].sort((a,b)=>a-b)){
        const rows=samples.filter(s=>s.kind===transfer&&s.bytes===size),ms=rows.reduce((a,s)=>a+s.ms,0),bytes=rows.reduce((a,s)=>a+s.bytes,0);if(ms>0){const line=el('span',(transfer==='download'?t("Mac → node"):t("Node → Mac"))+' · '+number(size/1024,0)+' KiB: ');line.append(el('strong',number(bytes/ms/1000)+' MB/s'));transfers.append(line);}
      }
      if(transfers.children.length)box.append(transfers);
    }
    if(j.kind==='cpu'&&samples.length){const row=samples.find(s=>s.kind==='cpu');if(row){const cpu=el('p',t('{0} iterations / {1} ms',number(row.iterations,0),number(row.ms,0)),'cpu-result');cpu.append(el('small',t("Synthetic FP32 kernel. This is not an LLM performance measurement.")));box.append(cpu);}}
    if(j.result?.note)box.append(el('p',t(j.result.note),'job-note'));container.append(box);
  }
}
function optionsForModels(select,models,placeholder) {
  const selected=select.value;
  const signature=NodeLiftI18n.language+JSON.stringify(models.map(m=>[m.path||m.id,m.name,m.bytes,m.source]));
  if(select.dataset.models===signature)return;
  select.dataset.models=signature;select.replaceChildren();const blank=el('option',placeholder);blank.value='';select.append(blank);
  for(const m of models){const option=el('option',(m.name||m.id)+(m.source==='huggingface'?' · Hugging Face':m.source==='upload'?' · '+t('Imported file'):'')+(typeof m.bytes==='number'?' · '+modelSize(m.bytes):''));option.value=m.path||m.id;select.append(option);}
  if(models.some(m=>(m.path||m.id)===selected))select.value=selected;
}
function firstNumber(object,keys){for(const key of keys)if(typeof object[key]==='number'&&Number.isFinite(object[key]))return object[key];return null;}
function renderRuns(runs) {
  const signature=JSON.stringify(runs);if(signature===engineSignature)return;engineSignature=signature;
  $('run-count').textContent=runs.length?(runs.length===1?t('1 RUN'):t('{0} RUNS',runs.length)):t("NO RUNS");
  const box=$('engine-runs');box.replaceChildren();if(!runs.length){box.append(el('p',t("Output and measured timings appear after a run. No simulated results."),'muted'));return;}
  for(const r of [...runs].sort((a,b)=>(b.created||0)-(a.created||0))){
    const card=el('article',undefined,'engine-run'),head=el('div',undefined,'run-heading');
    head.append(el('span',(r.backend&&r.backend!=='native'?(r.backend==='openrouter'?'OpenRouter · '+t('Cloud'):'Local API')+' · '+r.provider_model:t(modeNames[r.mode]||r.mode||"Generation"))+' · '+(t(stateNames[r.status]||r.status||"Status unavailable")),'run-title'),el('time',when(r.created)));card.append(head);
    const m=r.metrics||{},metrics=el('div',undefined,'run-metrics');
    const tps=firstNumber(m,['tokens_per_second','decode_tps','decode_tokens_per_second','tps']);
    const tokens=firstNumber(m,['generated_tokens','output_tokens','tokens']);
    const accepted=firstNumber(m,['accepted_tokens','accepted']),proposed=firstNumber(m,['proposed_tokens','proposed','draft_tokens']);
    const seconds=firstNumber(m,['elapsed_seconds','total_seconds','elapsed_s']),totalMs=firstNumber(m,['total_ms','elapsed_ms']);
    const ttft=firstNumber(m,['ttft_ms','time_to_first_token_ms']);
    const remoteWait=r.mode==='remote_draft'?firstNumber(m,['remote_wait_ms']):null;
    for(const [value,label,digits] of [[tps,'token/s',2],[tokens,t("tokens generated"),0],[seconds!==null?seconds:totalMs!==null?totalMs/1000:null,t("s total"),2],[ttft,t("ms to first token"),1],[remoteWait!==null?remoteWait/1000:null,t("s total remote wait"),2]])if(value!==null){const item=el('span',undefined,'run-metric');item.append(el('strong',number(value,digits)),document.createTextNode(t(label)));metrics.append(item);}
    if(accepted!==null&&proposed!==null){const item=el('span',undefined,'run-metric');item.append(el('strong',number(accepted,0)+' / '+number(proposed,0)),document.createTextNode(t("accepted proposals")));metrics.append(item);}
    if(metrics.children.length)card.append(metrics);
    if(r.error)card.append(el('p',t(r.error),'run-error'));
    if(r.fallback_reason)card.append(el('p',t('Returned to computer: {0}',t(r.fallback_reason)),'run-error'));
    if(r.text)card.append(el('pre',r.text,'output-text'));else if(['queued','running','loading'].includes(r.status))card.append(el('p',t("Processing…"),'muted'));
    if(r.status==='completed'&&!r.text&&r.backend&&r.backend!=='native')card.append(el('p',t('Completed without visible text. Try a larger output budget or a text model.'),'muted'));
    if(r.prompt&&(!r.backend||r.backend==='native')){
      const details=el('details',undefined,'run-prompt');details.append(el('summary',t("Prompt and parameters")),el('p',r.prompt),el('p',t('Output limit: {0} tokens · draft block: {1}',r.max_tokens??'-',r.draft_k??'-')));
      details.append(el('p',t('Delegation control: {0}',r.draft_policy==='adaptive'?t('adaptive'):t('fixed'))+(m.draft_disabled_reason?' · '+t('Return to computer: {0}',t(draftReasons[m.draft_disabled_reason]||m.draft_disabled_reason)):'')));
      if(r.mode==='remote_draft')details.append(el('p',t('Per-proposal timeout: {0} s. Total remote wait includes node work and transfer; it does not measure network speed.',number((r.remote_timeout_ms??30000)/1000,3))));
      const widths=(Array.isArray(r.blocks)?r.blocks:[]).map(b=>b.verification_batch_width).filter(w=>Number.isInteger(w)&&w>0);
      if(widths.length){const minimum=Math.min(...widths),maximum=Math.max(...widths);details.append(el('p',t('Verification batch width: {0} positions (proposals + one control position).',minimum===maximum?minimum:minimum+'–'+maximum)));}
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
function modelName(path){return (engineSnapshot?.models||[]).find(m=>(m.path||m.id)===path)?.name||path?.split(/[\\/]/).pop()||t("None");}
function updateConfigurationState(){
  const applied=engineSnapshot?.config,form=formConfiguration();
  configurationDirty=!!applied&&configFields.some(([,name])=>String(form[name]??'')!==String(applied[name]??''));
  const hasTarget=!!applied?.target_model;
  const feedback=authenticated?configurationActionFeedback:null;
  $('configuration-status').hidden=feedback?.state==='busy';
  $('configuration-status').textContent=feedback?(feedback.state==='busy'?'':t(feedback.message)):configurationDirty?t("Unapplied changes. Apply or revert before running."):hasTarget?t("The visible configuration is applied."):t("Select and apply a model to begin.");
  $('configuration-status').dataset.state=feedback?.state||'';
  $('configuration-status').className='configuration-status '+(configurationDirty?'dirty':'');
  $('configure').classList.toggle('needs-apply',configurationDirty);
  $('configure').dataset.state=hasTarget&&!configurationDirty?'applied':'unapplied';
  setButtonLabel($('configure'),configurationDirty?"Apply changes":hasTarget?"Configuration applied":"Apply configuration");
  $('revert-config').hidden=!configurationDirty;
  $('applied-config-description').textContent=hasTarget?t('{0} · draft: {1} · context {2} · {3} threads · GPU {4} layers',modelName(applied.target_model),modelName(applied.draft_model),applied.n_ctx,applied.threads,applied.gpu_layers):t("No model configured.");
}
function updateEngineControls() {
  updateConfigurationState();
  const external=$('run-backend').value!=='native';
  const available=authenticated&&(external||!!engineSnapshot?.available);
  const busy=!!engineSnapshot?.busy||actionPending;
  const configured=external?(!!$('provider-model').value&&($('run-backend').value!=='openrouter'||!!engineSnapshot?.providers?.openrouter_key_set)):!!engineSnapshot?.config?.target_model;
  const mode=external?'host':$('run-mode').value;
  for(const id of ['target-model','draft-model','context-size','threads','gpu-layers'])$(id).disabled=!available||busy;
  $('configure').disabled=!available||busy||!$('target-model').value||!configurationDirty;
  $('revert-config').disabled=!available||busy;
  $('run-backend').disabled=!authenticated||busy;
  $('provider-model').disabled=!authenticated||busy;
  $('provider-model-field').hidden=!external;
  $('provider-model-info').hidden=!external;
  $('run-mode').disabled=!available||busy||external;
  if(external)$('run-mode').value='host';
  $('remote-node').disabled=!available||busy||mode!=='remote_draft';
  $('remote-timeout').disabled=!available||busy||mode!=='remote_draft';
  $('draft-k').disabled=!available||busy||mode==='host';
  $('draft-policy').disabled=!available||busy||mode==='host';
  $('max-tokens').disabled=!available||busy;
  $('prompt').disabled=!available||busy;
  const ready=mode==='host'||mode==='lookup'||(mode==='local_draft'?!!engineSnapshot?.config?.draft_model:!!$('remote-node').value);
  $('start-run').disabled=!available||busy||!configured||!ready||(!external&&configurationDirty)||!$('prompt').value.trim();
  $('stop-run').disabled=!authenticated||!engineSnapshot?.busy||actionPending;
  setButtonLabel($('start-run'),engineSnapshot?.busy?'Run in progress':'Run');
  $('start-run').dataset.state=engineSnapshot?.busy?'running':'idle';
  renderEngineFeedback();renderBusyControls();
  $('mode-help').textContent=external?t($('run-backend').value==='openrouter'?'Cloud request to the selected OpenRouter model. Charges depend on the provider. No phone acceleration is measured.':'Text request to the selected local server. This does not use NodeLift phone drafting.'):mode==='host'?t("Computer baseline. No LLM work is sent to phones."):mode==='lookup'?t("Proposes sequences already in the context and verifies them with the target. No second model is required; it may help with repetitive text."):mode==='local_draft'?t("Target and draft on the computer: compare this before attributing a gain to the network."):t("The node proposes token blocks; the target on the computer verifies them. Requires a companion with an LLM engine ready.");
}
function remoteTimeoutMs(){
  const value=$('remote-timeout').value.trim();
  const seconds=value===''?30:Number(value);
  if(!Number.isFinite(seconds)||seconds<0.5||seconds>60)throw Error("Remote timeout must be between 0.5 and 60 seconds.");
  return Math.round(seconds*1000);
}
async function refreshEngine() {
  if(!authenticated)return false;
  try {
    engineSnapshot=await api('engine/status');
    if(engineActionFeedback?.state==='warning')engineActionFeedback={state:'success',message:engineActionFeedback.acceptedMessage};
    if(configurationActionFeedback?.state==='warning')configurationActionFeedback={state:'success',message:configurationActionFeedback.acceptedMessage};
    const available=!!engineSnapshot.available,busy=!!engineSnapshot.busy;
    $('engine-summary').textContent=busy?t("Running"):available?t("Available"):t("Unavailable");
    $('engine-backend').textContent=engineSnapshot.backend||t("Local backend");
    $('engine-state').textContent=busy?t("RUNNING"):available?t("EXPERIMENTAL"):t("UNAVAILABLE");
    $('engine-state').className='chip '+(available?'':'neutral');
    $('engine-notice').className='notice '+(available?'good':'');
    $('engine-notice').textContent=available?t("Experimental engine. Select local models and compare strategies using the same prompt. Engine availability does not demonstrate acceleration."):t("The engine is not yet available in this session. Device pairing and diagnostics remain available.");
    optionsForModels($('target-model'),engineSnapshot.models||[],t("Select a target model"));
    optionsForModels($('draft-model'),engineSnapshot.models||[],t("No draft selected"));
    if(!configurationDirty)writeAppliedConfiguration();
    if(window.renderModelLibrary)renderModelLibrary();
    renderRuns(engineSnapshot.runs||[]);updateEngineControls();NodeLiftGraph.update(snapshot,engineSnapshot);return true;
  } catch(e) {
    engineSnapshot=null;$('engine-summary').textContent=t("Unavailable");$('engine-backend').textContent=t("Configuration required");$('engine-state').textContent=t("UNAVAILABLE");$('engine-state').className='chip neutral';
    $('engine-notice').className='notice';$('engine-notice').textContent=e.status===404?t("This server version offers pairing and diagnostics. LLM controls become active when the engine is available."):e.message;
    if(authenticated&&engineSignature==='')$('engine-runs').replaceChildren(el('p',t("Output appears after configuring the engine and completing the first run."),'muted'));
    updateEngineControls();if(authenticated&&snapshot)NodeLiftGraph.update(snapshot,null);return false;
  }
}
function renderAboutVersion() {
  const value=$('about-host-version'),note=$('about-version-note');
  if(aboutMetadata){
    value.textContent=aboutMetadata.version;value.dataset.state='loaded';
    note.textContent=t("Version reported by this running host.");
  }else{
    value.textContent=t(aboutVersionLoading?"Reading installed version…":"Version unavailable");
    value.dataset.state=aboutVersionLoading?'loading':'unavailable';
    note.textContent=t(!authenticated?"Open a local session to read the installed host version.":aboutVersionLoading?"Reading from your local NodeLift service.":"This host did not return version metadata. The release links remain available.");
  }
}
async function refreshAboutVersion() {
  if(aboutVersionRequested||!authenticated)return;
  aboutVersionRequested=true;aboutVersionLoading=true;const epoch=++aboutVersionEpoch;renderAboutVersion();
  try{
    const metadata=await api('about');
    if(epoch!==aboutVersionEpoch||!authenticated)return;
    if(metadata.component!=='host'||typeof metadata.version!=='string'||!/^[0-9A-Za-z.+-]{1,64}$/.test(metadata.version))throw Error('Invalid host version metadata');
    aboutMetadata={version:metadata.version};
  }catch(_){if(epoch===aboutVersionEpoch)aboutMetadata=null;}
  finally{if(epoch===aboutVersionEpoch){aboutVersionLoading=false;renderAboutVersion();}}
}
async function refresh() {
  if(refreshing)return;refreshing=true;
  try{snapshot=await api('status');sessionReady(true);refreshAboutVersion();renderNodes();renderJobs();NodeLiftGraph.update(snapshot,engineSnapshot,true);$('updated-at').textContent=new Date().toLocaleTimeString(NodeLiftI18n.locale,{hour:'2-digit',minute:'2-digit',second:'2-digit'});await refreshEngine();}
  catch(e){if(authenticated)NodeLiftGraph.disconnected();$('session-label').textContent=authenticated?t("Connection needs checking"):t("Access required");$('session-dot').className='status-dot error';showError(e);}
  finally{refreshing=false;}
}
const pairing = NodeLiftPairing.mount({api, t, authenticated:()=>authenticated, error:showError});
async function openPairing(){
  if(!authenticated||busyControls.has('invite')||busyControls.has('renew-invite'))return;
  clearError();setControlBusy('invite',true,'Creating QR code…','Add device');setControlBusy('renew-invite',true,'Creating QR code…','New QR code');
  try{await pairing.open();if(!$('pairing').hidden)$('pairing').scrollIntoView({behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});}
  catch(error){showError(error);}
  finally{setControlBusy('invite',false);setControlBusy('renew-invite',false);updateSessionControls();}
}
$('invite').onclick=openPairing;
$('renew-invite').onclick=openPairing;
$('hide').onclick=()=>pairing.close();
$('copy').onclick=()=>pairing.copy();
$('export').onclick=()=>{if(!snapshot)return;const data={...snapshot,engine:engineSnapshot,exported_at:new Date().toISOString()};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download='nodelift-laboratory.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('job-filter').onchange=renderJobs;
for(const [id] of configFields)$(id).addEventListener('input',()=>{configurationActionFeedback=null;updateEngineControls();});
$('revert-config').onclick=()=>{configurationActionFeedback=null;writeAppliedConfiguration();updateEngineControls();};
for(const id of ['run-mode','remote-node','prompt','run-backend','provider-model'])$(id).addEventListener('input',updateEngineControls);
async function submitEngineAction(id,busyLabel,acceptedLabel,request){
  if(actionPending||$(id).disabled||!authenticated)return;
  const isConfiguration=id==='configure';
  if(isConfiguration)engineActionFeedback=null;
  const feedback=value=>{if(isConfiguration)configurationActionFeedback=value;else engineActionFeedback=value;};
  clearError('engine-error');actionPending=true;
  feedback({state:'busy',message:busyLabel});
  setControlBusy(id,true,busyLabel,isConfiguration?'Apply configuration':id==='start-run'?'Run':'Stop');updateEngineControls();
  try{
    try{await request();}
    catch(e){
      if(authenticated)feedback({state:'error',message:'Request failed. Review the error and try again.'});
      showError(e,'engine-error');return;
    }
    if(!authenticated)return;
    feedback({state:'success',message:acceptedLabel});
    // A failed follow-up read must not turn an accepted mutation into a failure.
    let refreshed=false;
    try{refreshed=(await refreshEngine())!==false;}catch(_){engineSnapshot=null;}
    if(!refreshed&&authenticated)feedback({state:'warning',acceptedMessage:acceptedLabel,message:isConfiguration?'Configuration saved. Status is temporarily unavailable.':'Request accepted. Status is temporarily unavailable.'});
  }finally{actionPending=false;setControlBusy(id,false);updateEngineControls();}
}
$('configuration-form').onsubmit=event=>{event.preventDefault();return submitEngineAction('configure','Applying configuration…','Configuration saved. Check the applied configuration.',async()=>{await api('engine/configure',{target_model:$('target-model').value,draft_model:$('draft-model').value||null,n_ctx:Number($('context-size').value),threads:Number($('threads').value),gpu_layers:Number($('gpu-layers').value)});configurationDirty=false;});};
$('run-form').onsubmit=event=>{event.preventDefault();return submitEngineAction('start-run','Requesting run…','Run requested. Follow its state and output below.',()=>api('engine/run',{backend:$('run-backend').value,provider_model:$('provider-model').value||undefined,prompt:$('prompt').value.trim(),mode:$('run-mode').value,draft_policy:$('draft-policy').value,node_id:$('run-mode').value==='remote_draft'?$('remote-node').value:undefined,max_tokens:Number($('max-tokens').value),draft_k:Number($('draft-k').value),remote_timeout_ms:$('run-mode').value==='remote_draft'?remoteTimeoutMs():undefined}));};
$('stop-run').onclick=()=>submitEngineAction('stop-run','Requesting stop…','Stop requested. Wait for the run state to update.',()=>api('engine/stop',{}));
function hideClientAccess(){
  clientAccessEpoch++;setControlBusy('open-client-access',false);setControlBusy('copy-client-key',false);clientAccess=null;clientKeyVisible=false;clearTimeout(clientAccessTimer);clearTimeout(clientRevealTimer);
  $('client-access').hidden=true;$('client-base-url').value='';$('client-model').value='';$('client-key-display').textContent=t("Key hidden");
  $('reveal-client-key').textContent=t("Reveal key");$('reveal-client-key').setAttribute('aria-pressed','false');$('reveal-client-key').disabled=true;$('copy-client-key').disabled=true;
  $('client-access-status').textContent='';$('open-client-access').disabled=!authenticated;
}
$('open-client-access').onclick=async()=>{
  if($('open-client-access').disabled||!authenticated)return;
  hideClientAccess();setControlBusy('open-client-access',true,'Retrieving local access…','Local API access');const epoch=clientAccessEpoch;$('client-access').hidden=false;$('open-client-access').disabled=true;$('client-access-status').textContent=t("Retrieving local access…");
  try{const access=await api('client-access');if(epoch!==clientAccessEpoch||!authenticated)return;
    if(typeof access.api_key!=='string'||typeof access.base_url!=='string'||typeof access.model!=='string')throw Error("API access unavailable.");
    clientAccess=access;$('client-base-url').value=access.base_url;$('client-model').value=access.model;
    $('reveal-client-key').disabled=false;$('copy-client-key').disabled=false;$('client-access-status').textContent=t("The key is hidden and excluded from exports. This panel closes after two minutes or when you switch tabs.");
    clientAccessTimer=setTimeout(hideClientAccess,120000);
  }catch(e){if(epoch===clientAccessEpoch)$('client-access-status').textContent=e.status===404?t("API access unavailable in this server session."):t('API access unavailable: {0}',t(e.message));}
  finally{if(epoch===clientAccessEpoch){setControlBusy('open-client-access',false);$('open-client-access').disabled=!authenticated;}}
};
$('close-client-access').onclick=hideClientAccess;
$('reveal-client-key').onclick=()=>{
  if(!clientAccess)return;clientKeyVisible=!clientKeyVisible;$('reveal-client-key').setAttribute('aria-pressed',String(clientKeyVisible));clearTimeout(clientRevealTimer);
  $('client-key-display').textContent=clientKeyVisible?clientAccess.api_key:t("Key hidden");$('reveal-client-key').textContent=clientKeyVisible?t("Hide key"):t("Reveal key");
  if(clientKeyVisible)clientRevealTimer=setTimeout(()=>{clientKeyVisible=false;$('reveal-client-key').setAttribute('aria-pressed','false');$('client-key-display').textContent=t("Key hidden");$('reveal-client-key').textContent=t("Reveal key");},30000);
};
$('copy-client-key').onclick=async()=>{
  if(!clientAccess||$('copy-client-key').disabled)return;
  const epoch=clientAccessEpoch;setControlBusy('copy-client-key',true,'Copying…','Copy key');
  try{await navigator.clipboard.writeText(clientAccess.api_key);if(epoch===clientAccessEpoch)$('client-access-status').textContent=t("Key copied to clipboard. Paste it into the local client you want to connect.");}
  catch(_){if(epoch===clientAccessEpoch)$('client-access-status').textContent=t("Copy unavailable. Use Reveal key to copy it manually.");}
  finally{if(epoch===clientAccessEpoch){setControlBusy('copy-client-key',false);$('copy-client-key').disabled=!clientAccess;}}
};
document.addEventListener('visibilitychange',()=>{if(document.hidden)hideClientAccess();});
const sections=[...document.querySelectorAll('main>section[id]')];
const navigationLinks=[...document.querySelectorAll('.rail nav a')];
let navigationFramePending=false;
function navigationSectionAt(rows,anchor){
  const visible=rows.filter(row=>row.height>0);
  let selected=visible[0]?.id;
  for(const row of visible){if(row.top>anchor)break;selected=row.id;}
  return selected;
}
function updateNavigation(){
  navigationFramePending=false;
  // Read every major section together: observer entries only describe changes,
  // and cannot identify the current section after a large jump or layout change.
  const offset=parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop)||0;
  const anchor=Math.min(Math.max(0,window.innerHeight-1),offset+24);
  const rows=sections.map(section=>{const rect=section.getBoundingClientRect();return {id:section.id,top:rect.top,height:rect.height};});
  const selected=navigationSectionAt(rows,anchor);
  for(const link of navigationLinks){
    const active=link.getAttribute('href')==='#'+selected;
    link.classList.toggle('active',active);
    if(active)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');
  }
}
function scheduleNavigationUpdate(){
  if(navigationFramePending)return;
  navigationFramePending=true;requestAnimationFrame(updateNavigation);
}
window.addEventListener('scroll',scheduleNavigationUpdate,{passive:true});
window.addEventListener('resize',scheduleNavigationUpdate);
window.addEventListener('hashchange',scheduleNavigationUpdate);
for(const link of navigationLinks)link.addEventListener('click',scheduleNavigationUpdate);
if('ResizeObserver' in window)new ResizeObserver(scheduleNavigationUpdate).observe($('main'));
scheduleNavigationUpdate();
$('language').addEventListener('change',event=>NodeLiftI18n.setLanguage(event.target.value));
document.addEventListener('nodelift-languagechange',()=>{
  // Language changes never restart a run or submit form edits.
  hideClientAccess();
  if(window.renderModelLibrary)renderModelLibrary();
  nodeSignature='';jobSignature='';engineSignature='';
  sessionReady(authenticated);
  if(snapshot){renderNodes();renderJobs();NodeLiftGraph.update(snapshot,engineSnapshot);if(nodeAnnouncement)announceNodeAction(nodeAnnouncement.nodeId,nodeAnnouncement.message);}
  if(engineSnapshot){renderRuns(engineSnapshot.runs||[]);}
  for(const id of ['error','engine-error'])if($(id).dataset.message)$(id).textContent=t($(id).dataset.message);
  refreshEngine();
});
sessionReady(false);refresh();setInterval(refresh,3000);
