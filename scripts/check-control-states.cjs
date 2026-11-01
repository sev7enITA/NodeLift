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
(async()=>{
  // A prior highlight must never survive a large scroll jump into another section.
  flushFrames();assert.equal(navLinks[0].getAttribute('aria-current'),'location');
  function setSectionTops(tops){sectionElements.forEach((element,index)=>element.rect={top:tops[index],height:1400});}
  function dispatchWindow(name){for(const callback of windowListeners.get(name)||[])callback();flushFrames();}
  setSectionTops([-6500,-5000,-3500,-1700,-100,1400]);dispatchWindow('scroll');assert.equal(navLinks[4].getAttribute('aria-current'),'location');
  setSectionTops([-5000,-3500,-2000,-500,1000,2500]);dispatchWindow('scroll');assert.equal(navLinks[3].getAttribute('aria-current'),'location','engine visible after scroll jump, even when Measurements was active');assert.equal(navLinks[4].getAttribute('aria-current'),null);
  // Clicking the same hash can skip hashchange, but the link still schedules a read.
  setSectionTops([-7500,-6000,-4500,-3000,-1500,96]);navLinks[5].events.get('click')();flushFrames();assert.equal(navLinks[5].getAttribute('aria-current'),'location');
  // A taller compact sticky header changes the visible content edge.
  stickyOffset=194;sandbox.window.innerHeight=844;setSectionTops([-4800,-3200,-1600,194,1800,3400]);dispatchWindow('resize');assert.equal(navLinks[3].getAttribute('aria-current'),'location');
  setSectionTops([-1500,194,1800,3400,5000,6600]);dispatchWindow('hashchange');assert.equal(navLinks[1].getAttribute('aria-current'),'location');assert.equal(navLinks.filter(link=>link.getAttribute('aria-current')==='location').length,1);
  assert.equal(run("navigationSectionAt([{id:'engine',top:-300,height:1200},{id:'hidden',top:0,height:0},{id:'measurements',top:900,height:400}],120)"),'engine');
  ready();
  const opening=run('openPairing()');await run('openPairing()');assert.equal(pairingCalls,1,'duplicate QR creation blocked');
  run('sessionReady(true)');assert.equal(node('invite').disabled,true);assert.equal(labelText('invite'),'Creating QR code…');assert.equal(node('invite').getAttribute('aria-busy'),'true');
  resolvePairing();await opening;assert.equal(node('invite').disabled,false);assert.equal(node('invite').getAttribute('aria-busy'),null);assert.equal(inviteLabel.dataset.i18n,'Add device','idle label still localizes after busy rendering');assert.equal(node('invite').children[0],inviteIcon,'pairing retains the icon node');assert.equal(node('invite').children[1],inviteLabel,'pairing retains the label node');
  run("pairing.open=async()=>{throw Error('Synthetic pairing failure')}");await run('openPairing()');assert.equal(node('error').textContent,'Synthetic pairing failure');assert.equal(node('invite').disabled,false);assert.equal(inviteLabel.dataset.i18n,'Add device');
  run("setControlBusy('renew-invite',true,'Creating QR code…','New QR code');updateSessionControls()");assert.equal(node('invite').disabled,true);await run('openPairing()');assert.equal(run("busyControls.has('invite')"),false);run("setControlBusy('renew-invite',false);updateSessionControls()");
  let resolveRequest,calls=0;
  sandbox.request=()=>{calls++;return new Promise(resolve=>resolveRequest=resolve);};
  run('refreshEngine=async()=>{}');
  const pending=run("submitEngineAction('start-run','Requesting run…','Run requested. Follow its state and output below.',request)");
  await run("submitEngineAction('start-run','Requesting run…','Run requested.',request)");assert.equal(calls,1);
  run('sessionReady(true);updateEngineControls()');assert.equal(labelText('start-run'),'Requesting run…');assert.equal(node('stop-run').disabled,true);assert.equal(runLabel.dataset.i18n,'Requesting run…');assert.equal(node('start-run').children[1],runIcon,'busy state retains decorative children');assert.equal(node('engine-action-status').hidden,true,'busy banner does not repeat the button label');
  assert.equal(node('engine-action-status').textContent,'');
  const originalTranslate=sandbox.NodeLiftI18n.t;sandbox.NodeLiftI18n.t=key=>'translated:'+key;run('renderBusyControls()');assert.equal(labelText('start-run'),'translated:Requesting run…');assert.equal(runLabel.dataset.i18n,'Requesting run…');sandbox.NodeLiftI18n.t=originalTranslate;run('renderBusyControls()');
  run('engineSnapshot.busy=true');resolveRequest();await pending;
  assert.equal(labelText('start-run'),'Run in progress');assert.equal(node('start-run').disabled,true,'backend running state remains authoritative');assert.equal(node('stop-run').disabled,false);
  assert.match(node('engine-action-status').textContent,/Run requested/);assert.doesNotMatch(node('engine-action-status').textContent,/completed/i);
  ready();node('threads').value='8';run('updateEngineControls()');
  sandbox.request=()=>new Promise(resolve=>resolveRequest=resolve);
  const configuring=run("submitEngineAction('configure','Applying configuration…','Configuration saved. Check the applied configuration.',request)");assert.equal(node('configuration-status').hidden,true);assert.equal(node('engine-action-status').hidden,true,'configuration requests do not write into generation feedback');resolveRequest();await configuring;assert.match(node('configuration-status').textContent,/Configuration saved/);assert.equal(node('engine-action-status').hidden,true);
  ready();sandbox.request=async()=>{};run("refreshEngine=async()=>{throw Error('Synthetic follow-up poll failure')}");await run("submitEngineAction('start-run','Requesting run…','Run requested.',request)");assert.equal(node('engine-action-status').dataset.state,'warning');assert.equal(node('engine-action-status').textContent,'Request accepted. Status is temporarily unavailable.');assert.equal(node('engine-error').hidden,true,'accepted mutation is not labeled failed when its follow-up read fails');assert.equal(node('start-run').disabled,true,'unknown backend state prevents a duplicate run');run('refreshEngine=async()=>true');
  ready();sandbox.request=async()=>{throw Error('Synthetic failure');};
  await run("submitEngineAction('start-run','Requesting run…','Requested',request)");assert.equal(node('start-run').disabled,false,'retry restored after error');assert.equal(node('start-run').getAttribute('aria-busy'),null);assert.equal(node('engine-error').textContent,'Synthetic failure');
  sandbox.request=()=>new Promise(resolve=>resolveRequest=resolve);
  const lost=run("submitEngineAction('start-run','Requesting run…','Requested',request)");run('sessionReady(false)');resolveRequest();await lost;
  assert.equal(node('start-run').disabled,true,'request completion must not restore access after session loss');assert.equal(node('engine-action-status').hidden,true);
  ready();let resolveNode,nodeCalls=0;sandbox.nodeRequest=()=>{nodeCalls++;return new Promise(resolve=>resolveNode=resolve);};
  run("api=()=>nodeRequest();refresh=async()=>{};snapshot.nodes=[{id:'fixture',name:'Synthetic phone',online:true,capabilities:{supported_jobs:['network']}}];renderNodes()");
  const findAction=kind=>node('nodes').querySelectorAll('button').find(button=>button.dataset.action===kind);
  const oldButton=findAction('network'),pendingNode=oldButton.onclick();await oldButton.onclick();assert.equal(nodeCalls,1,'duplicate node action blocked, including stale DOM handlers');
  run('renderNodes()');assert.equal(findAction('network').disabled,true);assert.equal(findAction('network').getAttribute('aria-busy'),'true');assert.equal(findAction('revoke').disabled,true);
  run("snapshot.jobs=[{node:'fixture',kind:'network',state:'queued',created:Date.now()/1000}]");resolveNode();await pendingNode;
  assert.equal(findAction('network').disabled,true,'queued backend job prevents another test after request completion');assert.equal(findAction('revoke').disabled,false);assert.equal(findAction('network').getAttribute('aria-busy'),null);
  const announcement=node('device-action-announcement');assert.match(announcement.textContent,/Test requested/);run("snapshot.jobs[0].state='completed';renderNodes()");assert.equal(run('nodeActionFeedback.size'),0,'finished backend job clears stale acknowledgment');assert.equal(announcement.textContent,'');assert.equal(findAction('network').disabled,false);
  const lostNode=findAction('network').onclick();run('sessionReady(false)');resolveNode();await lostNode;assert.equal(node('nodes').querySelectorAll('button').length,0,'session loss removes busy node controls');assert.equal(run('pendingNodeActions.size'),0);assert.equal(announcement.textContent,'');ready();
  run("clientAccess={api_key:'synthetic'}");node('reveal-client-key').onclick();assert.equal(node('reveal-client-key').getAttribute('aria-pressed'),'true');node('reveal-client-key').onclick();assert.equal(node('reveal-client-key').getAttribute('aria-pressed'),'false');
  let resolveRecovery,recoveryCalls=0,reloads=0,savedSession=null;
  sandbox.fetch=async(url,options)=>{assert.equal(url,'/admin/session/restore');assert.equal(options.headers['X-NodeLift-Session'],'restore');recoveryCalls++;return new Promise(resolve=>resolveRecovery=resolve);};
  sandbox.location.reload=()=>reloads++;
  sandbox.sessionStorage.setItem=(name,value)=>{savedSession=[name,value];};
  run('sessionReady(false)');assert.equal(node('session-recovery').hidden,false);
  const recovery=run('restoreSession()');await run('restoreSession()');assert.equal(recoveryCalls,1);assert.equal(node('restore-session').disabled,true);
  resolveRecovery({ok:false});await recovery;assert.equal(reloads,0);assert.equal(node('restore-session').disabled,false);assert.match(node('session-recovery-status').textContent,/could not be restored/);
  const recovered=run('restoreSession()');resolveRecovery({ok:true,json:async()=>({token:'synthetic_session_token_123456789012345'})});await recovered;
  assert.equal(reloads,1);assert.equal(savedSession[0],'nodelift-admin');
  sandbox.sessionStorage.setItem=()=>{throw Error('storage blocked');};let fragmentFallback='';sandbox.location.replace=url=>fragmentFallback=url;
  const noStorage=run('restoreSession()');resolveRecovery({ok:true,json:async()=>({token:'synthetic_session_token_123456789012345'})});await noStorage;assert.match(fragmentFallback,/^\/#synthetic_/);assert.equal(reloads,2);
  run('sessionReady(true)');assert.equal(node('session-recovery').hidden,true);
  console.log('PASS: session recovery retry/duplicate guard/storage fallback, QR/engine/node duplicate guards, polling-safe busy labels, backend disabling, failure retry, session loss, localized label recovery, key visibility state, and navigation after scroll jumps, explicit links, hash changes and compact-header resize.');
})().catch(error=>{console.error(error);process.exitCode=1;});
