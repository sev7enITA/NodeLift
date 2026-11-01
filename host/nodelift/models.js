'use strict';
let hubInfo=null,hubRows=[],libraryMessage='',uploading=false;
const transferNames={transferring:'Transferring',verifying:'Verifying',completed:'Completed',cancelled:'Stopped',failed:'Failed',expired:'Expired'};
function modelMessage(message){libraryMessage=message;$('transfer-status').textContent=t(message);}
function renderProviderInfo(){
  const backend=$('run-backend').value,model=(engineSnapshot?.providers?.models?.[backend]||[]).find(m=>m.id===$('provider-model').value);
  let label=model?t('Model: {0} · context: {1}',model.id,model.context_length??'—'):t('Refresh provider models first');
  if(backend==='openrouter'&&model){const p=model.pricing||{};const price=x=>typeof x==='string'&&x.trim()!==''&&Number.isFinite(Number(x))?number(Number(x)*1e6,4):'—';label+=' · '+t('USD / million tokens · input {0} · output {1}. Published rates may change; other charges may apply.',price(p.prompt),price(p.completion));}
  $('provider-model-info').textContent=label;
}
function renderHub(){
  $('hf-results').replaceChildren();
  for(const row of hubRows)$('hf-results').append(action(row.id,async()=>{$('hf-repo').value=row.id;await inspectHub();},{quiet:true}));
  const chosen=$('hf-file')?.value;
  const box=$('hf-details');box.replaceChildren();if(!hubInfo)return;
  const card=el('a',t('Model card and license'));card.href=hubInfo.model_card;card.target='_blank';card.rel='noopener noreferrer';box.append(card,el('p',t('License: {0} · revision: {1}',String(hubInfo.license),hubInfo.revision),'field-note'));
  if(hubInfo.gated){box.append(el('p',t('Gated repository: download manually after accepting its terms.')));return;}
  if(!hubInfo.files.length){box.append(el('p',t('No supported single GGUF files with SHA-256 were found.')));return;}
  const select=el('select');select.id='hf-file';select.setAttribute('aria-label',t('Choose a GGUF file'));
  const blank=el('option',t('Choose a GGUF file'));blank.value='';select.append(blank);
  for(const file of hubInfo.files){const option=el('option',file.name+' · '+gib(file.bytes));option.value=file.name;select.append(option);}
  if(hubInfo.files.some(file=>file.name===chosen))select.value=chosen;
  const download=action(t('Download selected GGUF'),async()=>{await api('models/download',{repo:hubInfo.repo,revision:hubInfo.revision,file:select.value});await refreshEngine();});
  download.disabled=!select.value;select.onchange=()=>{download.disabled=!select.value;};box.append(select,download);
}
function renderModelLibrary(){
  if(!engineSnapshot)return;
  const transfer=engineSnapshot.library?.transfer;
  const active=transfer&&['transferring','verifying'].includes(transfer.status);
  $('transfer-progress').hidden=!active;$('cancel-transfer').hidden=!active;
  $('upload-model').disabled=uploading||!!active;
  if(transfer){
    $('transfer-status').textContent=t('Transfer: {0} · {1} / {2}',t(transferNames[transfer.status]||transfer.status),gib(transfer.received),gib(transfer.bytes))+(transfer.error?' · '+t(transfer.error):'');
    if(transfer.status==='completed')$('transfer-status').textContent+=' · '+t('Model imported. Select it as target or draft, then apply configuration.');
    $('transfer-progress').value=transfer.bytes?transfer.received/transfer.bytes:0;
  }else $('transfer-status').textContent=t(libraryMessage||'No model transfer active.');
  const providers=engineSnapshot.providers||{},backend=$('run-backend').value;
  if(!$('local-provider-url').dataset.initialized&&providers.local_url){$('local-provider-url').value=providers.local_url;$('local-provider-url').dataset.initialized='true';}
  optionsForModels($('provider-model'),providers.models?.[backend]||[],t('Refresh provider models first'));
  const access=$('access-backend').value;
  $('provider-access-status').textContent=t(providers[access==='openrouter'?'openrouter_key_set':'local_key_set']?'Key configured for this host session':'No key configured');
  $('local-url-field').hidden=access!=='local_api';
  renderProviderInfo();
}
async function modelTask(fn){clearError('model-error');try{await fn();}catch(e){showError(e,'model-error');}}
async function inspectHub(){hubInfo=await api('models/inspect?repo='+encodeURIComponent($('hf-repo').value.trim()));renderHub();}
$('import-form').onsubmit=event=>{event.preventDefault();modelTask(async()=>{await api('models/import',{path:$('import-path').value.trim()});modelMessage('Model imported. Select it as target or draft, then apply configuration.');await refreshEngine();});};
$('hf-search-form').onsubmit=event=>{event.preventDefault();modelTask(async()=>{hubRows=(await api('models/search?q='+encodeURIComponent($('hf-query').value.trim()))).models;renderHub();});};
$('hf-inspect-form').onsubmit=event=>{event.preventDefault();modelTask(inspectHub);};
$('cancel-transfer').onclick=()=>modelTask(async()=>{const id=engineSnapshot?.library?.transfer?.id;if(id)await api('models/cancel',{id});await refreshEngine();});
$('upload-form').onsubmit=event=>{event.preventDefault();modelTask(async()=>{
  if(uploading)return;const file=$('model-file').files[0];if(!file)throw Error('Select a GGUF file first.');uploading=true;$('upload-model').disabled=true;let transfer;
  try{
    transfer=await api('models/upload/start',{name:file.name,bytes:file.size});await refreshEngine();
    for(let offset=0;offset<file.size;offset+=1048576){
      const response=await fetch('/admin/models/upload/chunk?id='+encodeURIComponent(transfer.id)+'&offset='+offset,{method:'POST',headers:{Authorization:'Bearer '+key,'Content-Type':'application/octet-stream'},body:file.slice(offset,offset+1048576),signal:AbortSignal.timeout(60000)});
      if(!response.ok){const data=await response.json();throw Error(data.error||'Model upload failed.');}
    }
    await api('models/upload/finish',{id:transfer.id});
  }catch(e){if(transfer)await api('models/cancel',{id:transfer.id}).catch(()=>{});throw e;}
  finally{uploading=false;await refreshEngine();}
});};
$('provider-access-form').onsubmit=event=>{event.preventDefault();const secret=$('provider-key').value;$('provider-key').value='';modelTask(async()=>{const backend=$('access-backend').value;await api('providers/configure',{backend,api_key:secret,base_url:backend==='local_api'?$('local-provider-url').value.trim():undefined});await refreshEngine();});};
$('clear-provider-key').onclick=()=>modelTask(async()=>{await api('providers/configure',{backend:$('access-backend').value,api_key:''});$('provider-key').value='';await refreshEngine();});
$('refresh-provider-models').onclick=()=>modelTask(async()=>{await api('providers/models',{backend:$('access-backend').value});await refreshEngine();});
$('access-backend').onchange=()=>{$('provider-key').value='';renderModelLibrary();};
$('run-backend').addEventListener('change',()=>{renderModelLibrary();updateEngineControls();});
$('provider-model').addEventListener('change',renderProviderInfo);
document.addEventListener('nodelift-languagechange',()=>{renderHub();renderModelLibrary();if($('model-error').dataset.message)$('model-error').textContent=t($('model-error').dataset.message);});
document.addEventListener('visibilitychange',()=>{if(document.hidden)$('provider-key').value='';});
