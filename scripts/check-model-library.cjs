/* Synthetic asynchronous UI tests; no browser, live credentials, devices or inference. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../host/nodelift/dashboard.js'),'utf8');
const nodes=new Map(),listeners=new Map(),windowListeners=new Map(),frames=[];
class Element {
  constructor(tag='div'){this.tagName=tag;this.dataset={};this.attributes={};this.children=[];this.value='';this.textContent='';this.disabled=false;this.hidden=false;this.classList={add(){},toggle(){}};this.events=new Map();this.rect={top:0,height:100};}
  get textContent(){return (this._textContent||'')+this.children.map(child=>child.textContent).join('');} set textContent(value){this._textContent=value;this.children=[];}
  setAttribute(name,value){this.attributes[name]=value;} removeAttribute(name){delete this.attributes[name];} getAttribute(name){return this.attributes[name]??null;}
  append(...children){this.children.push(...children);} replaceChildren(...children){this.children=children;} addEventListener(name,callback){this.events.set(name,callback);} getBoundingClientRect(){return this.rect;} contains(){return false;}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  querySelectorAll(selector){return this.children.flatMap(child=>[...((selector==='button'&&child.tagName==='button')||(selector==='[data-i18n]'&&child.dataset.i18n!==undefined)?[child]:[]),...child.querySelectorAll(selector)]);} focus(){} click(){} scrollIntoView(){}
}
function node(id){if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id);}
const inviteIcon=new Element('span'),inviteLabel=new Element('span'),runIcon=new Element('span'),runLabel=new Element('span');
inviteIcon.setAttribute('aria-hidden','true');inviteIcon.textContent='＋';inviteLabel.dataset.i18n='Add device';inviteLabel.textContent='Add device';node('invite').append(inviteIcon,inviteLabel);
runIcon.setAttribute('aria-hidden','true');runIcon.textContent='↗';runLabel.dataset.i18n='Run';runLabel.textContent='Run';node('start-run').append(runLabel,runIcon);
const labelText=id=>(node(id).querySelector('[data-i18n]')||node(id)).textContent;
const sectionIds=['overview','cluster','model-library','engine','measurements','about'];
const sectionElements=sectionIds.map((id,index)=>{const element=node(id);element.id=id;element.rect={top:index*1500,height:1400};return element;});
const navLinks=sectionIds.map(id=>{const link=new Element('a');link.setAttribute('href','#'+id);return link;});
const flushFrames=()=>{for(const callback of frames.splice(0))callback();};
let stickyOffset=96;
let resolvePairing,pairingCalls=0;
const sandbox={console,URL,AbortController,Map,Date,Blob,setTimeout:()=>1,clearTimeout(){},setInterval(){},location:{hash:''},history:{replaceState(){}},sessionStorage:{getItem:()=>'',setItem(){}},requestAnimationFrame:callback=>(frames.push(callback),frames.length),getComputedStyle:()=>({scrollPaddingTop:stickyOffset+'px'}),window:{innerHeight:950,addEventListener(name,callback){if(!windowListeners.has(name))windowListeners.set(name,[]);windowListeners.get(name).push(callback);}},document:{getElementById:node,createElement:tag=>new Element(tag),createTextNode:()=>new Element(),documentElement:{},querySelectorAll:selector=>selector==='main>section[id]'?sectionElements:selector==='.rail nav a'?navLinks:[],addEventListener:(name,fn)=>listeners.set(name,fn)},navigator:{clipboard:{writeText:async()=>{}}},NodeLiftI18n:{locale:'en',language:'en',t:(key,...values)=>key.replace(/\{(\d+)\}/g,(_,i)=>values[i])},NodeLiftGraph:{clear(){},update(){},memoryScope:()=>''},NodeLiftPairing:{mount:()=>({clear(){},close(){},copy(){},open(){pairingCalls++;return new Promise(resolve=>resolvePairing=resolve);}})}};
const context=vm.createContext(sandbox);
// Avoid automatic network startup. All actual handlers and state updates remain intact.
vm.runInContext(source.replace('sessionReady(false);refresh();setInterval(refresh,3000);',''),context);
const run=code=>vm.runInContext(code,context);
function ready(){
  run(`authenticated=true;engineActionFeedback=null;configurationActionFeedback=null;snapshot={nodes:[],jobs:[]};engineSnapshot={available:true,busy:false,config:{target_model:'target.gguf',draft_model:null,n_ctx:2048,threads:4,gpu_layers:999}};writeAppliedConfiguration();`);
  node('run-backend').value='native';node('run-mode').value='host';node('prompt').value='Synthetic prompt';run('updateEngineControls()');
}
// Shared synthetic DOM conventions; both production scripts execute together.
Object.defineProperty(Element.prototype,'id',{get(){return this._id;},set(value){this._id=value;nodes.set(value,this);}});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../host/nodelift/models.js'),'utf8'),context);
const submit=id=>node(id).onsubmit({preventDefault(){}});
const calls=[];
let handler=async()=>({});
sandbox.testApi=async(route,body)=>{calls.push({route,body});return handler(route,body);};
run('api=testApi;refreshEngine=async()=>{renderModelLibrary();};authenticated=true;engineSnapshot={available:true,library:{transfer:null},providers:{models:{}},models:[]};updateLibraryControls();');
(async()=>{
  assert.equal(run("action('Generic result',async()=>{}).textContent"),'Generic result','generic buttons must not dereference undefined pending actions');
  run('showError(undefined,"model-error")');assert.equal(node('model-error').textContent,'Request failed');
  let finish;handler=()=>new Promise(resolve=>finish=resolve);node('hf-query').value='real-query';
  const searching=submit('hf-search-form');await submit('hf-search-form');assert.equal(calls.length,1,'double submit suppressed');
  assert.equal(node('hf-search').disabled,true);run('renderModelLibrary()');assert.equal(node('hf-search').disabled,true,'poll cannot re-enable busy search');
  finish({models:[{id:'owner/model'}]});await searching;
  assert.equal(node('model-error').hidden,true);assert.equal(node('hf-results').children[0].textContent,'owner/model');assert.equal(node('hf-search').disabled,false);
  const info={repo:'owner/model',revision:'a'.repeat(40),license:'mit',model_card:'https://huggingface.co/owner/model',gated:false,files:[{name:'test.gguf',bytes:1024,sha256:'b'.repeat(64)}]};
  handler=async()=>info;await node('hf-results').children[0].onclick();assert.equal(node('hf-repo').value,'owner/model');assert.equal(node('hf-download').disabled,true);
  node('hf-file').value='test.gguf';node('hf-file').onchange();assert.equal(node('hf-download').disabled,false);
  handler=()=>new Promise(resolve=>finish=resolve);const startingDownload=node('hf-download').onclick();assert.equal(node('upload-model').disabled,true,'upload waits while download starts');assert.equal(node('hf-download').getAttribute('aria-busy'),'true');finish({id:'transfer'});await startingDownload;handler=async()=>({});assert.equal(calls.at(-1).route,'models/download');assert.equal(calls.at(-1).body.revision,'a'.repeat(40));
  run("engineSnapshot.library.transfer={id:'transfer',status:'transferring'};renderModelLibrary()");assert.equal(node('hf-download').disabled,true);assert.equal(node('upload-model').disabled,true);
  await node('cancel-transfer').onclick();assert.equal(calls.at(-1).route,'models/cancel');
  run('engineSnapshot.library.transfer=null');
  handler=async()=>({models:[]});await submit('hf-search-form');assert.equal(node('hf-results').children.length,0);assert.match(node('hf-status').textContent,/No matching/);
  handler=async()=>{throw Error('synthetic network failure');};await submit('hf-search-form');assert.equal(node('model-error').textContent,'synthetic network failure');assert.equal(node('hf-search').disabled,false);
  handler=async()=>info;await submit('hf-inspect-form');handler=async()=>{throw Error('invalid repo');};await submit('hf-inspect-form');assert.equal(node('hf-details').children.length,0,'old files cannot remain selectable after failed inspection');
  handler=async()=>({});node('import-path').value='/synthetic/test.gguf';await submit('import-form');assert.equal(calls.at(-1).route,'models/import');assert.match(node('transfer-status').textContent,/Model imported/);
  node('model-file').files=[];await submit('upload-form');assert.match(node('model-error').textContent,/Select a GGUF/);
  const file=new Blob([new Uint8Array(1048576+32)]);file.name='synthetic.gguf';node('model-file').files=[file];
  handler=async route=>route==='models/upload/start'?{id:'upload'}:{};let chunks=0;
  sandbox.fetch=async()=>{chunks++;return {ok:true,status:200};};await submit('upload-form');assert.equal(chunks,2);assert.equal(calls.at(-1).route,'models/upload/finish');
  // Cancel a browser upload while a chunk is in flight: no next chunk or finish.
  let chunkStarted;const started=new Promise(resolve=>chunkStarted=resolve);let aborted=false;
  sandbox.fetch=async(url,options)=>new Promise((resolve,reject)=>{chunkStarted();options.signal.addEventListener('abort',()=>{aborted=true;reject(Error('abort'));});});
  handler=async route=>{if(route==='models/upload/start'){run("engineSnapshot.library.transfer={id:'upload-cancel',status:'transferring'}");return {id:'upload-cancel'};}return {};};
  const before=calls.filter(c=>c.route==='models/upload/finish').length,pendingUpload=submit('upload-form');await started;await node('cancel-transfer').onclick();await pendingUpload;
  assert.equal(aborted,true);assert.equal(calls.filter(c=>c.route==='models/upload/finish').length,before);assert.equal(node('model-error').hidden,true,'user cancellation is not a failure');
  run('engineSnapshot.library.transfer=null');handler=async()=>({});node('access-backend').value='local_api';node('local-provider-url').value='http://127.0.0.1:8000/v1';node('provider-key').value='synthetic-key';
  await submit('provider-access-form');assert.equal(node('provider-key').value,'');assert.equal(calls.at(-1).body.api_key,'synthetic-key');
  await node('clear-provider-key').onclick();assert.equal(calls.at(-1).body.api_key,'');await node('refresh-provider-models').onclick();assert.equal(calls.at(-1).route,'providers/models');
  run('sessionReady(false)');for(const id of ['hf-search','hf-inspect','import-path-button','upload-model','save-provider-access'])assert.equal(node(id).disabled,true,id);
  console.log('PASS: model search/results, inspect/select/download, empty/error/retry, polling-safe duplicate guards, import, chunked upload/cancel, provider controls and session loss. Synthetic UI tests, not live network or inference.');
})().catch(error=>{console.error(error);process.exitCode=1;});
