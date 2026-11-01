/* Read-only device relationship view. Token attribution is not compute utilization. */
(function (root) {
  'use strict';
  const finite = value => typeof value === 'number' && Number.isFinite(value) && value >= 0;
  const count = value => Number.isSafeInteger(value) && value >= 0;
  function contribution(run) {
    const empty = {measured:false, applicable:true, generated:null, mobile:null, host:null, proposed:null, uncommitted:null, share:null, nodeId:run?.node_id || null};
    if (!run) return empty;
    if (run.backend && run.backend !== 'native') return {...empty, applicable:false};
    if (!Array.isArray(run.blocks) || !run.blocks.length) return empty;
    let generated=0, mobile=0, proposed=0;
    for (const block of run.blocks) {
      if (!block || !count(block.generated) || !count(block.accepted) || !count(block.proposed) || block.accepted > block.generated || block.accepted > block.proposed || !['host','remote_draft','local_draft','lookup'].includes(block.effective_mode)) return empty;
      generated += block.generated;
      if (block.effective_mode === 'remote_draft') {
        if (run.mode !== 'remote_draft' || !run.node_id) return empty;
        mobile += block.accepted; proposed += block.proposed;
      }
    }
    if (!generated || (run.metrics?.generated_tokens !== undefined && run.metrics.generated_tokens !== generated)) return empty;
    return {...empty,measured:true,generated,mobile,host:generated-mobile,proposed,uncommitted:proposed-mobile,share:mobile/generated};
  }
  // Orthogonal routes stay in the column gutters, never through preceding device cards.
  function edgePoints(host, peer, trunkY=host.top+host.height+30) {
    const center=host.left+host.width/2, gutter=peer.left-10, target=peer.top+peer.height/2;
    return [[center,host.top+host.height],[center,trunkY],[gutter,trunkY],[gutter,target],[peer.left,target]];
  }
  function connectionAfterUpdate(connected, statusFetched=false) {
    return statusFetched === true || connected === true;
  }
  function connectionState(node, connected=true) {
    return !connected?'unknown':node.revoked?'revoked':node.online?'online':'offline';
  }
  function memoryScope(caps) {
    const os=String(caps.os || '').toLowerCase();
    return /ios|ipados/.test(os) ? 'Process allocation headroom' : /android/.test(os) ? 'System available memory' : 'Available memory · scope unknown';
  }
  function measurements(jobs, id) {
    const completed=(jobs || []).filter(j=>j.node===id && j.state==='completed' && Array.isArray(j.result?.samples)).sort((a,b)=>(b.finished || b.created || 0)-(a.finished || a.created || 0));
    const network=completed.find(j=>['network','network_paced'].includes(j.kind));
    const cpu=completed.find(j=>j.kind==='cpu');
    const rtt=new Map(), transfer=new Map();
    for (const s of network?.result.samples || []) {
      if (!finite(s.ms)) continue;
      if (s.kind==='rtt') {
        const pace=finite(s.pace_ms)?s.pace_ms:0;
        if (!rtt.has(pace))rtt.set(pace,[]); rtt.get(pace).push(s.ms);
      } else if (['download','upload'].includes(s.kind) && finite(s.bytes) && s.bytes>0 && s.ms>0) {
        const key=s.kind+':'+s.bytes;
        if (!transfer.has(key))transfer.set(key,{kind:s.kind,bytes:s.bytes,totalBytes:0,totalMs:0,samples:0});
        const g=transfer.get(key);g.totalBytes+=s.bytes;g.totalMs+=s.ms;g.samples++;
      }
    }
    const cpuRows=(cpu?.result.samples || []).filter(s=>s.kind==='cpu' && finite(s.iterations) && finite(s.ms) && s.ms>0);
    const cpuMs=cpuRows.reduce((a,s)=>a+s.ms,0);
    return {networkAt:network?.finished || network?.created || null,cpuAt:cpu?.finished || cpu?.created || null,
      rtt:[...rtt].sort((a,b)=>a[0]-b[0]).map(([pace,values])=>({pace,median:values.sort((a,b)=>a-b)[Math.ceil(values.length*.5)-1],samples:values.length})),
      transfer:[...transfer.values()].map(g=>({...g,mbps:g.totalBytes/g.totalMs/1000})),
      cpuIterationsPerSecond:cpuMs?cpuRows.reduce((a,s)=>a+s.iterations,0)/cpuMs*1000:null};
  }
  // A visual weight is token attribution, never estimated RAM pooling or CPU usage.
  function edgeAppearance(node,run,c,connected=true) {
    const status=connectionState(node,connected);
    const participant=run?.mode==='remote_draft' && (!run.backend||run.backend==='native') && run.node_id===node.id;
    const share=participant&&c.measured?c.share:null;
    const band=share===null?'unmeasured':share<.25?'low':share<.6?'medium':'high';
    const last=run?.blocks?.at(-1);
    const flowing=status==='online'&&participant&&run.status==='running'&&last?.effective_mode==='remote_draft';
    return {status,participant,share,band,width:share===null?1.5:2+5*share,flowing};
  }
  const logic={contribution,memoryScope,measurements,connectionState,connectionAfterUpdate,edgePoints,edgeAppearance};
  if (typeof module !== 'undefined' && module.exports) module.exports=logic;
  root.NodeLiftGraph=logic;
  if (typeof document === 'undefined')return;
  const $=id=>document.getElementById(id);
  let state=null, engine=null, selected='host', runChoice='latest', filter='all', connected=true;
  let optionsSignature='', detailSignature='', announcedSelection=null;
  const buttons=new Map();
  const tr=(key,...args)=>NodeLiftI18n.t(key,...args);
  const fmt=(value,digits=1)=>finite(value)?value.toLocaleString(NodeLiftI18n.locale,{maximumFractionDigits:digits,minimumFractionDigits:digits}):tr('Not measured');
  const bytes=value=>finite(value)?fmt(value/1073741824)+' GiB':tr('Not detected');
  const date=value=>finite(value)&&value>0?new Date(value*1000).toLocaleString(NodeLiftI18n.locale):tr('Unknown');
  function make(tag,cls,text) {const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
  function set(id,text){if($(id).textContent!==text)$(id).textContent=text;}
  function field(list,label,value) {const row=make('div','graph-field');row.append(make('dt',null,tr(label)),make('dd',null,value));list.append(row);}
  function notice(text,cls='') {return make('p','graph-note '+cls,tr(text));}
  function currentRun(){const runs=engine?.runs || [];return runChoice==='latest'?runs[0] || null:runs.find(r=>r.id===runChoice) || null;}
  function deviceState(node) {return {unknown:'Contact unknown',revoked:'REVOKED',online:'ONLINE',offline:'OFFLINE'}[connectionState(node,connected)];}
  function isCurrent(run) {return run && ['queued','running','loading'].includes(run.status);}
  function selectedRole(node,run) {
    if (node.id==='host')return run?.backend && run.backend!=='native'?'API coordinator':'Target model · verifier';
    if(run?.backend && run.backend!=='native')return 'No phone delegation';
    if(run?.mode==='remote_draft' && run.node_id===node.id)return isCurrent(run)?'Selected draft proposer':'Draft proposer in this run';
    return node.capabilities?.engine_ready?(connected&&node.online&&!node.revoked?'Available draft companion':'Draft-capable companion'):'Diagnostics companion';
  }
  function telemetryAge(node) {
    if (node.id==='host')return tr('Host hardware inventory');
    const at=node.capabilities_updated_at;
    if (!finite(at))return tr('Telemetry time unknown');
    const now=Math.max(finite(state?.observed_at)?state.observed_at:0,Date.now()/1000);
    if (!connected || !node.online || node.revoked || now-at>20)return tr('Historical telemetry');
    return tr('Recent telemetry');
  }
  function buildButton(node, run, c) {
    let button=buttons.get(node.id);
    if(!button){
      button=make('button','graph-device');button.type='button';button.dataset.device=node.id;
      for(const cls of ['graph-device-kicker','graph-device-name','graph-device-spec','graph-device-role','graph-device-weight'])button.append(make('span',cls));
      button.onclick=()=>{selected=node.id;detailSignature='';render();};
      buttons.set(node.id,button);
    }
    const host=node.id==='host', caps=host?node:node.capabilities || {};
    const participating=run?.mode==='remote_draft' && run.node_id===node.id && (!run.backend || run.backend==='native');
    button.className='graph-device'+(host?' graph-host':'')+(connectionState(node,connected)==='unknown'?' is-unknown':node.online&&!node.revoked?' is-online':' is-offline')+(participating?' is-participant':'');
    button.setAttribute('aria-pressed',String(selected===node.id));
    button.setAttribute('aria-controls','graph-inspector');
    const values=[host?tr('HOST / COORDINATOR')+(connected?'':' · '+tr('Contact unknown')):tr(deviceState(node)),host?tr('This computer'):node.name,
      [caps.model || tr('Hardware unknown'),bytes(caps.physical_memory_bytes)].join(' · '),tr(selectedRole(node,run)),
      c.measured?(!host&&!participating?tr('Not the draft proposer in this run'):tr(host?'Host-origin tokens: {0}%':'Accepted mobile draft: {0}%',fmt(100*(host?c.host/c.generated:c.share)))):tr(c.applicable?'Contribution not measured':'Not applicable to this route')];
    values.forEach((value,i)=>{if(button.children[i].textContent!==value)button.children[i].textContent=value;});
    return button;
  }
  function drawEdges() {
    const svg=$('graph-edges'), canvas=$('graph-map');if(!svg||!state)return;
    const origin=canvas.getBoundingClientRect(),host=buttons.get('host');if(!host || !host.isConnected)return;
    svg.setAttribute('viewBox',`0 0 ${origin.width} ${origin.height}`);
    const localRect=rect=>({left:rect.left-origin.left,top:rect.top-origin.top,width:rect.width,height:rect.height});
    const h=localRect(host.getBoundingClientRect()),run=currentRun(),c=contribution(run);
    const remoteId=run?.mode==='remote_draft'&&(!run.backend||run.backend==='native')?run.node_id:null;
    const peers=[...buttons].filter(([id,button])=>id!=='host'&&button.isConnected)
      .map(([id,button])=>({id,button,rect:localRect(button.getBoundingClientRect())}));
    const trunkY=Math.min(h.top+h.height+30,...peers.map(peer=>peer.rect.top-10));
    const visible=new Set(peers.map(p=>p.id));
    for(const path of [...svg.children])if(!visible.has(path.dataset.device))path.remove();
    peers.sort((a,b)=>Number(a.id===remoteId)-Number(b.id===remoteId));
    for(const {id,rect} of peers) {
      const node=state.nodes.find(n=>n.id===id),look=edgeAppearance(node,run,c,connected);
      let path=[...svg.children].find(p=>p.dataset.device===id);
      if(!path){path=document.createElementNS('http://www.w3.org/2000/svg','path');path.dataset.device=id;svg.append(path);}
      path.setAttribute('d',edgePoints(h,rect,trunkY).map(([x,y],i)=>(i?'L ':'M ')+x+' '+y).join(' '));
      path.setAttribute('class','graph-edge '+look.status+' weight-'+look.band+(look.participant?' participant':'')+(look.flowing?' flowing':''));
      path.setAttribute('stroke-width',String(look.width));
      // Keep DOM nodes stable during polling so dash animation does not restart.
      if(look.participant && path!==svg.lastElementChild)svg.append(path);
    }
  }

  function renderInspector(node,run,c) {
    const signature=JSON.stringify([node,run,c,state?.jobs,connected,NodeLiftI18n.language,telemetryAge(node)]);
    if(signature===detailSignature)return;detailSignature=signature;
    const area=$('graph-inspector'),focusedSection=area.contains(document.activeElement)?document.activeElement.closest('details')?.dataset.section:null,open=new Set([...area.querySelectorAll('details[open]')].map(n=>n.dataset.section));
    const host=node.id==='host',caps=host?node:node.capabilities || {};
    area.replaceChildren();
    const heading=make('h3',null,host?tr('This computer'):node.name);heading.id='graph-device-title';
    area.append(make('p','micro',tr('DEVICE INSPECTOR')),heading,make('p','graph-inspector-role',tr(selectedRole(node,run))));
    const freshness=make('p','graph-freshness',telemetryAge(node));freshness.classList.toggle('stale',telemetryAge(node)!==tr('Recent telemetry')&&!host);area.append(freshness);
    const hardware=make('dl','graph-fields');
    field(hardware,'Model',caps.model || tr('Not detected'));field(hardware,'Processor',caps.processor || tr('Not reported'));
    field(hardware,'System',caps.os || tr('Not detected'));field(hardware,'CPU cores',finite(caps.cpu_cores)?fmt(caps.cpu_cores,0):tr('Not reported'));
    field(hardware,'Physical RAM',bytes(caps.physical_memory_bytes));
    field(hardware,host?'System available memory':memoryScope(caps),bytes(caps.available_memory_bytes));
    if(!host && /android/i.test(caps.os || ''))field(hardware,'Process memory · PSS',bytes(caps.process_memory_bytes));
    if(!host){field(hardware,'Thermal status',tr(caps.thermal || 'Not reported'));field(hardware,'Battery',finite(caps.battery_percent)?fmt(caps.battery_percent,0)+'%':tr('Not reported'));field(hardware,'Connection',tr(caps.transport || 'Not reported'));field(hardware,'Companion',caps.app_version || tr('Not reported'));}
    area.append(hardware);
    const impact=make('section','graph-impact');impact.append(make('h4',null,tr('Contribution in selected run')));
    const impactFields=make('dl','graph-fields');
    if(c.measured){
      const participating=!host && run?.mode==='remote_draft' && c.nodeId===node.id;
      if(!host&&!participating)field(impactFields,'Token attribution',tr('Not the draft proposer in this run'));
      else {
        field(impactFields,host?'Host-origin token IDs':'Accepted draft token IDs',fmt(host?c.host:participating?c.mobile:0,0)+' / '+fmt(c.generated,0));
        field(impactFields,host?'Host-origin token share':'Accepted mobile draft share',fmt(100*(host?c.host/c.generated:participating?c.share:0))+'%');
        if(participating){field(impactFields,'Submitted draft tokens',fmt(c.proposed,0));field(impactFields,'Draft tokens not committed',fmt(c.uncommitted,0));}
      }
    }else field(impactFields,'Token attribution',tr(c.applicable?'Not measured':'Not applicable to this route'));
    if(host && c.applicable)field(impactFields,'Verification scope',tr('All committed output tokens'));
    if(run?.mode==='remote_draft' && c.nodeId===node.id && c.applicable)field(impactFields,'Combined remote wait',finite(run.metrics?.remote_wait_ms)?fmt(run.metrics.remote_wait_ms/1000,2)+' s':tr('Not measured'));
    field(impactFields,'Measured acceleration',tr('No matched baseline in this view'));
    impact.append(impactFields,notice('Token attribution includes EOS IDs. The host verifies every accepted mobile proposal. This is not a compute share or a speedup.'));area.append(impact);
    const details=make('details','graph-more');details.dataset.section='measurements';details.open=open.has('measurements');details.append(make('summary',null,tr('Measurements and freshness')));
    const measured=make('dl','graph-fields');
    field(measured,host?'Inventory sampled':'Last contact',date(host?node.sampled_at:node.last_seen));
    if(!host)field(measured,'Telemetry sampled',date(node.capabilities_updated_at));
    if(host){field(measured,'Run decode throughput',c.applicable&&finite(run?.metrics?.tokens_per_second)?fmt(run.metrics.tokens_per_second,2)+' '+tr('token IDs/s'):tr('Not measured'));details.append(measured,notice('Run decode throughput includes delegation and waiting. Model loading and prefill are excluded.'));}
    else{
      const m=measurements(state.jobs,node.id);field(measured,'Network test recorded',date(m.networkAt));
      for(const r of m.rtt)field(measured,tr('HTTPS RTT median · {0} ms pacing',fmt(r.pace,0)),fmt(r.median,2)+' ms');
      for(const r of m.transfer)field(measured,tr(r.kind==='download'?'Host → device · {0} MiB':'Device → host · {0} MiB',fmt(r.bytes/1048576,2)),fmt(r.mbps,2)+' MB/s');
      field(measured,'Synthetic CPU test recorded',date(m.cpuAt));field(measured,'Synthetic CPU rate',finite(m.cpuIterationsPerSecond)?fmt(m.cpuIterationsPerSecond,0)+' '+tr('iterations/s'):tr('Not measured'));
      details.append(measured,notice('Last completed diagnostics, not live bandwidth or LLM speed. Transfers are grouped by direction and payload; RTT is grouped by pacing.'));
    }
    area.append(details);
    const limits=make('details','graph-more');limits.dataset.section='limits';limits.open=open.has('limits');limits.append(make('summary',null,tr('Usage and limitations')));
    if(host){limits.append(notice('Coordinates one native run and verifies phone proposals. Current phone delegation uses one draft companion per run; device memory is not pooled.'));}
    else{
      const list=make('dl','graph-fields');field(list,'Reported readiness',tr(caps.engine_ready?'Native draft reported ready':'Native draft not ready'));
      field(list,'Supported diagnostics',(caps.supported_jobs || []).map(kind=>tr({network:'Quick network test',network_paced:'Paced network test',cpu:'CPU test'}[kind] || kind)).join(' · ') || tr('Not reported'));
      field(list,'Lifecycle',tr(caps.lifecycle || 'Not reported'));field(list,'Live resource limits',tr('Not reported by this companion protocol'));limits.append(list);
      if(!node.online||node.revoked)limits.append(notice('This device cannot receive new work while offline or revoked.','stale'));
      limits.append(notice('Battery, thermal and memory policies remain enforced by the companion. Readiness is self-reported, not a measured performance guarantee.'));
    }
    limits.append(notice('GPU/NPU utilization, energy and separate phone compute time are not measured.'));area.append(limits);
    if(focusedSection)area.querySelector('details[data-section="'+focusedSection+'"] summary')?.focus({preventScroll:true});
  }
  function render() {
    if(!state)return;
    const runs=engine?.runs || [];
    if(runChoice!=='latest' && !runs.some(r=>r.id===runChoice))runChoice='latest';
    const run=currentRun(),c=contribution(run);
    const signature=JSON.stringify(runs.map(r=>[r.id,r.status]))+NodeLiftI18n.language;
    if(signature!==optionsSignature){
      optionsSignature=signature;const select=$('graph-run');select.replaceChildren();
      const latest=make('option',null,tr('Latest run · follow'));latest.value='latest';select.append(latest);
      for(const r of runs){const o=make('option',null,date(r.created)+' · '+tr(({completed:'Completed',running:'Running',loading:'Loading',failed:'Failed',cancelled:'Stopped',queued:'Queued'})[r.status] || 'Status unavailable')+' · '+String(r.id).slice(0,6));o.value=r.id;select.append(o);}
      if(runChoice!=='latest' && !runs.some(r=>r.id===runChoice))runChoice='latest';select.value=runChoice;
    }
    $('graph-run').disabled=!runs.length;$('graph-filter').disabled=!connected;
    $('graph-unknown-legend').hidden=connected;
    $('graph-filter').options[1].textContent=tr(connected?'Online only':'Online at last snapshot');
    const all=[{id:'host',name:'This computer',online:true,...state.host},...(state.nodes || [])];
    const visible=all.filter(n=>n.id==='host'||filter==='all'||n.online&&!n.revoked);
    if(!visible.some(n=>n.id===selected))selected='host';
    const ids=new Set(visible.map(n=>n.id));
    for(const [id,button] of buttons)if(!ids.has(id)){button.remove();buttons.delete(id);}
    for(const node of visible){const b=buildButton(node,run,c),parent=$(node.id==='host'?'graph-host-slot':'graph-peer-slots');if(b.parentNode!==parent)parent.append(b);}
    $('graph-empty').hidden=visible.length>1;
    set('graph-empty',tr(filter==='online'?'No online companions. Show all devices to inspect historical telemetry.':'No paired companions. Add a device to start measuring.'));
    set('graph-connection',tr(connected?'Session connected':'Connection interrupted · last snapshot'));
    $('graph-connection').classList.toggle('stale',!connected);
    set('graph-context',!connected?tr('Last snapshot · {0}',date(state.observed_at)):run?tr(isCurrent(run)?'In progress · {0}':'Recorded run · {0}',date(run.created)):tr('No run selected · hardware inventory only'));
    let model=run?.provider_model || run?.identity?.config?.target_model;
    if(model)model=String(model).split(/[\\/]/).pop();
    set('graph-route',run?(run.backend&&run.backend!=='native'?tr('External route · no phone delegation'):tr('Native target → verification'))+(model?' · '+model:''):tr('Select a device to inspect capabilities and evidence.'));
    set('graph-share-value',c.measured?fmt(c.share*100)+'%':tr(c.applicable?'Not measured':'Not applicable'));
    set('graph-token-total',c.measured?tr('{0} mobile / {1} committed token IDs',fmt(c.mobile,0),fmt(c.generated,0)):tr('No measured mobile contribution in this view.'));
    $('graph-share-fill').style.width=c.measured?(c.share*100)+'%':'0%';
    $('graph-share-track').classList.toggle('unmeasured',!c.measured);
    set('graph-decode',c.applicable&&finite(run?.metrics?.tokens_per_second)?fmt(run.metrics.tokens_per_second,2)+' '+tr('token IDs/s'):tr('Not measured'));
    const selectedNode=visible.find(n=>n.id===selected);
    renderInspector(selectedNode,run,c);
    if(announcedSelection!==selected){
      announcedSelection=selected;
      set('graph-selection-status',tr('Selected device: {0}',selected==='host'?tr('This computer'):selectedNode.name));
    }
    requestAnimationFrame(drawEdges);
  }
  root.NodeLiftGraph.update=function(snapshot,engineSnapshot,statusFetched=false) {state=snapshot;engine=engineSnapshot;connected=connectionAfterUpdate(connected,statusFetched);render();};
  root.NodeLiftGraph.disconnected=function(){connected=false;detailSignature='';render();};
  root.NodeLiftGraph.clear=function(){
    state=null;engine=null;connected=false;selected='host';runChoice='latest';optionsSignature='';detailSignature='';announcedSelection=null;buttons.clear();
    set('graph-selection-status','');
    for(const id of ['graph-host-slot','graph-peer-slots','graph-edges','graph-inspector','graph-run'])$(id).replaceChildren();
    const heading=make('h3',null,tr('Device inspector'));heading.id='graph-device-title';$('graph-inspector').append(heading);
    $('graph-run').disabled=true;$('graph-filter').disabled=true;$('graph-unknown-legend').hidden=true;$('graph-empty').hidden=false;
    set('graph-empty',tr('Topology appears after access is established.'));set('graph-connection',tr('Access required'));
    set('graph-context',tr('Access your session'));set('graph-route',tr('Use the complete link generated by NodeLift on your computer.'));
    set('graph-share-value','-');set('graph-token-total',tr('No measured mobile contribution in this view.'));set('graph-decode','-');$('graph-share-fill').style.width='0%';$('graph-share-track').classList.add('unmeasured');
  };
  $('graph-run').addEventListener('change',event=>{runChoice=event.target.value;detailSignature='';render();});
  $('graph-filter').addEventListener('change',event=>{filter=event.target.value;render();});
  window.addEventListener('resize',drawEdges);
  if(typeof ResizeObserver!=='undefined'){
    const observer=new ResizeObserver(drawEdges);
    for(const id of ['graph-map','graph-peer-slots','graph-host-slot'])observer.observe($(id));
  }
  const motionToggle=$('graph-motion');
  if(motionToggle){
    try{motionToggle.checked=localStorage.getItem('nodelift-graph-motion')!=='off';}catch(_){}
    const applyMotion=()=>{$('graph-map').classList.toggle('motion-paused',!motionToggle.checked||document.hidden);};
    motionToggle.addEventListener('change',()=>{try{localStorage.setItem('nodelift-graph-motion',motionToggle.checked?'on':'off');}catch(_){}applyMotion();});
    document.addEventListener('visibilitychange',applyMotion);applyMotion();
  }
})(typeof window !== 'undefined' ? window : globalThis);
