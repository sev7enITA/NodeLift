'use strict';
let hubInfo=null,hubRows=[],libraryMessage='',uploading=false,uploadCancelled=false,uploadController=null;
const libraryBusy=new Set();
let hubStatus='';
function activeTransfer(){return ['transferring','verifying'].includes(engineSnapshot?.library?.transfer?.status);}
function updateLibraryControls(){
  const enabled=authenticated&&!!engineSnapshot?.library,active=activeTransfer();
  const states={'hf-search':libraryBusy.has('hub'),'hf-inspect':libraryBusy.has('hub'),
    'import-path-button':libraryBusy.has('import'),'upload-model':uploading||active||libraryBusy.has('download'),
    'save-provider-access':libraryBusy.has('provider'),'clear-provider-key':libraryBusy.has('provider'),
    'refresh-provider-models':libraryBusy.has('provider'),'cancel-transfer':libraryBusy.has('cancel')};
  for(const [id,busy] of Object.entries(states)){const button=$(id);button.disabled=!enabled||busy;button.setAttribute('aria-busy',String(busy));}
  for(const button of $('hf-results').querySelectorAll('button'))button.disabled=!enabled||libraryBusy.has('hub');
  const download=$('hf-download');if(download){download.disabled=!enabled||active||uploading||libraryBusy.has('download')||!$('hf-file')?.value;download.setAttribute('aria-busy',String(libraryBusy.has('download')));}
  $('hf-status').textContent=t(hubStatus);
}
function libraryAction(label,fn){
  const button=el('button',t(label),'quiet');button.type='button';button.disabled=!authenticated;
  button.onclick=()=>{if(!button.disabled) return fn();};return button;
}
async function modelTask(fn,group='general'){
  if(libraryBusy.has(group))return false;
  libraryBusy.add(group);clearError('model-error');updateLibraryControls();
  try {if(!authenticated)throw Error(sessionMessage());await fn();return true;}
  catch(error){showError(error,'model-error');return false;}
  finally{libraryBusy.delete(group);updateLibraryControls();}
}
const transferNames={transferring:'Transferring',verifying:'Verifying',completed:'Completed',cancelled:'Stopped',failed:'Failed',expired:'Expired'};
function modelSize(bytes){return typeof bytes==='number'&&bytes>=0&&bytes<1073741824?number(bytes/1048576,1)+' MiB':gib(bytes);}
function modelMessage(message){libraryMessage=message;$('transfer-status').textContent=t(message);}
function renderProviderInfo(){
  const backend=$('run-backend').value,model=(engineSnapshot?.providers?.models?.[backend]||[]).find(m=>m.id===$('provider-model').value);
  let label=model?t('Model: {0} · context: {1}',model.id,model.context_length??'-'):t('Refresh provider models first');
  if(backend==='openrouter'&&model){const p=model.pricing||{};const price=x=>typeof x==='string'&&x.trim()!==''&&Number.isFinite(Number(x))?number(Number(x)*1e6,4):'-';label+=' · '+t('USD / million tokens · input {0} · output {1}. Published rates may change; other charges may apply.',price(p.prompt),price(p.completion));}
  $('provider-model-info').textContent=label;
}
function renderHub(){
  $('hf-results').replaceChildren();
  for(const row of hubRows)$('hf-results').append(libraryAction(row.id,()=>modelTask(async()=>{$('hf-repo').value=row.id;await inspectHub();},'hub')));
  const chosen=$('hf-file')?.value;
  const box=$('hf-details');box.replaceChildren();if(!hubInfo)return;
  const card=el('a',t('Model card and license'));card.href=hubInfo.model_card;card.target='_blank';card.rel='noopener noreferrer';box.append(card,el('p',t('License: {0} · revision: {1}',String(hubInfo.license),hubInfo.revision),'field-note'));
  if(hubInfo.gated){box.append(el('p',t('Gated repository: download manually after accepting its terms.')));return;}
  if(!hubInfo.files.length){box.append(el('p',t('No supported single GGUF files with SHA-256 were found.')));return;}
  const select=el('select');select.id='hf-file';select.setAttribute('aria-label',t('Choose a GGUF file'));
  const blank=el('option',t('Choose a GGUF file'));blank.value='';select.append(blank);
  for(const file of hubInfo.files){const option=el('option',file.name+' · '+modelSize(file.bytes));option.value=file.name;select.append(option);}
  if(hubInfo.files.some(file=>file.name===chosen))select.value=chosen;
  const info=hubInfo;
  const download=libraryAction('Download selected GGUF',()=>modelTask(async()=>{await api('models/download',{repo:info.repo,revision:info.revision,file:select.value});await refreshEngine();},'download'));download.id='hf-download';
  download.disabled=!select.value;select.onchange=updateLibraryControls;box.append(select,download);updateLibraryControls();
}
function renderModelLibrary(){
  if(!engineSnapshot)return;
  const transfer=engineSnapshot.library?.transfer;
  const active=transfer&&['transferring','verifying'].includes(transfer.status);
  $('transfer-progress').hidden=!active;$('cancel-transfer').hidden=!active;
  $('upload-model').disabled=!authenticated||uploading||!!active;
  if(transfer){
    $('transfer-status').textContent=t('Transfer: {0} · {1} / {2}',t(transferNames[transfer.status]||transfer.status),modelSize(transfer.received),modelSize(transfer.bytes))+(transfer.error?' · '+t(transfer.error):'');
    if(transfer.status==='completed')$('transfer-status').textContent+=' · '+t('Model imported. Select it as target or draft, then apply configuration.');
    $('transfer-progress').value=transfer.bytes?transfer.received/transfer.bytes:0;
  }else $('transfer-status').textContent=t(libraryMessage||'No model transfer active.');
  if(transfer?.cleanup_pending)$('transfer-status').textContent+=' · '+t('A temporary model file could not be removed; check available disk space');
  if(engineSnapshot.library?.warning)$('transfer-status').textContent+=' · '+t(engineSnapshot.library.warning);
  const providers=engineSnapshot.providers||{},backend=$('run-backend').value;
  if(!$('local-provider-url').dataset.initialized&&providers.local_url){$('local-provider-url').value=providers.local_url;$('local-provider-url').dataset.initialized='true';}
  optionsForModels($('provider-model'),providers.models?.[backend]||[],t('Refresh provider models first'));
  const access=$('access-backend').value;
  $('provider-access-status').textContent=t(providers[access==='openrouter'?'openrouter_key_set':'local_key_set']?'Key configured for this host session':'No key configured');
  $('local-url-field').hidden=access!=='local_api';
  renderProviderInfo();updateLibraryControls();
}
async function inspectHub(){
  hubInfo=null;renderHub();hubStatus='Inspecting model files…';updateLibraryControls();
  try{hubInfo=await api('models/inspect?repo='+encodeURIComponent($('hf-repo').value.trim()));hubStatus='Model files loaded.';renderHub();}
  catch(error){hubStatus='Model inspection failed. Check the repository and try again.';throw error;}
}
$('import-form').onsubmit=event=>{event.preventDefault();return modelTask(async()=>{await api('models/import',{path:$('import-path').value.trim()});modelMessage('Model imported. Select it as target or draft, then apply configuration.');await refreshEngine();},'import');};
$('hf-search-form').onsubmit=event=>{event.preventDefault();return modelTask(async()=>{
  hubInfo=null;hubRows=[];renderHub();hubStatus='Searching Hugging Face…';updateLibraryControls();
  try{const result=await api('models/search?q='+encodeURIComponent($('hf-query').value.trim()));
    if(!Array.isArray(result?.models))throw Error('Hugging Face returned invalid model metadata');
    hubRows=result.models;hubStatus=hubRows.length?'Select a repository to inspect its GGUF files.':'No matching public GGUF repositories found.';renderHub();
  }catch(error){hubStatus='Search failed. Check the connection and try again.';throw error;}
},'hub');};
$('hf-inspect-form').onsubmit=event=>{event.preventDefault();return modelTask(inspectHub,'hub');};
$('cancel-transfer').onclick=()=>modelTask(async()=>{uploadCancelled=true;uploadController?.abort();const id=engineSnapshot?.library?.transfer?.id;if(id)await api('models/cancel',{id});await refreshEngine();},'cancel');
$('upload-form').onsubmit=event=>{event.preventDefault();return modelTask(async()=>{
  if(uploading||activeTransfer())return;const file=$('model-file').files[0];if(!file)throw Error('Select a GGUF file first.');uploading=true;uploadCancelled=false;$('upload-model').disabled=true;let transfer;
  try{
    transfer=await api('models/upload/start',{name:file.name,bytes:file.size});await refreshEngine();
    for(let offset=0;offset<file.size;offset+=1048576){
      if(uploadCancelled)break;
      uploadController=new AbortController();const timeout=setTimeout(()=>uploadController.abort(),60000);
      try{
      const response=await fetch('/admin/models/upload/chunk?id='+encodeURIComponent(transfer.id)+'&offset='+offset,{method:'POST',headers:{Authorization:'Bearer '+key,'Content-Type':'application/octet-stream'},body:file.slice(offset,offset+1048576),signal:uploadController.signal});
      if(response.status===401){sessionReady(false);throw Error(sessionMessage());}
      if(!response.ok){let data;try{data=await response.json();}catch(_){}throw Error(data?.error||'Model upload failed.');}
      }finally{clearTimeout(timeout);uploadController=null;}
    }
    if(!uploadCancelled)await api('models/upload/finish',{id:transfer.id});
  }catch(e){if(transfer)await api('models/cancel',{id:transfer.id}).catch(()=>{});if(!uploadCancelled)throw e;}
  finally{uploading=false;await refreshEngine();}
},'upload');};
$('provider-access-form').onsubmit=event=>{event.preventDefault();const secret=$('provider-key').value;$('provider-key').value='';return modelTask(async()=>{const backend=$('access-backend').value;await api('providers/configure',{backend,api_key:secret,base_url:backend==='local_api'?$('local-provider-url').value.trim():undefined});await refreshEngine();},'provider');};
$('clear-provider-key').onclick=()=>modelTask(async()=>{await api('providers/configure',{backend:$('access-backend').value,api_key:''});$('provider-key').value='';await refreshEngine();},'provider');
$('refresh-provider-models').onclick=()=>modelTask(async()=>{await api('providers/models',{backend:$('access-backend').value});await refreshEngine();},'provider');
$('access-backend').onchange=()=>{$('provider-key').value='';renderModelLibrary();};
$('run-backend').addEventListener('change',()=>{renderModelLibrary();updateEngineControls();});
$('provider-model').addEventListener('change',renderProviderInfo);
document.addEventListener('nodelift-languagechange',()=>{renderHub();renderModelLibrary();if($('model-error').dataset.message)$('model-error').textContent=t($('model-error').dataset.message);});
document.addEventListener('visibilitychange',()=>{if(document.hidden)$('provider-key').value='';});

updateLibraryControls();
