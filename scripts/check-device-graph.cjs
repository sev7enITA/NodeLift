/* Accounting invariants for the device graph; all data below is synthetic. */
const assert=require('node:assert/strict');
const {contribution,memoryScope,measurements,connectionState,connectionAfterUpdate,edgePoints}=require('../host/nodelift/graph.js');
assert.equal(connectionState({online:true},false),'unknown');
assert.equal(connectionState({online:false},false),'unknown');
assert.equal(connectionState({online:true,revoked:true},false),'unknown');
assert.equal(connectionState({online:true}),'online');
assert.equal(connectionState({online:false}),'offline');
assert.equal(connectionState({online:true,revoked:true}),'revoked');
// Language and engine redraws must retain a lost-contact state; only a new status fetch restores it.
let contact=false;
contact=connectionAfterUpdate(contact);
assert.equal(connectionState({online:true},contact),'unknown');
contact=connectionAfterUpdate(contact,false);
assert.equal(connectionState({online:true},contact),'unknown');
contact=connectionAfterUpdate(contact,true);
assert.equal(connectionState({online:true},contact),'online');
assert.equal(connectionAfterUpdate(contact),true);
assert.equal(connectionAfterUpdate(false,'true'),false);
const block=(mode,generated,accepted=0,proposed=0)=>({effective_mode:mode,generated,accepted,proposed});
const run=(mode,blocks,extra={})=>({backend:'native',mode,node_id:'synthetic-phone',blocks,...extra});
const remote=contribution(run('remote_draft',[block('remote_draft',5,4,4),block('remote_draft',3,1,4)]));
assert.equal(remote.generated,8);assert.equal(remote.mobile,5);assert.equal(remote.host,3);assert.equal(remote.share,5/8);assert.equal(remote.uncommitted,3);
// A selected proposer with no accepted tokens is measured zero, not missing evidence.
const zero=contribution(run('remote_draft',[block('remote_draft',1,0,4)]));
assert.equal(zero.measured,true);assert.equal(zero.share,0);assert.equal(zero.proposed,4);assert.equal(zero.uncommitted,4);
// A fallback keeps committed phone work attributed, but host steps add no phone tokens.
const fallback=contribution(run('remote_draft',[block('remote_draft',4,3,3),block('host',1),block('host',1)]));
assert.equal(fallback.share,.5);assert.equal(fallback.mobile,3);assert.equal(fallback.proposed,3);
// EOS or output-budget truncation leaves an unexamined tail, not necessarily rejected tokens.
const eos=contribution(run('remote_draft',[block('remote_draft',2,2,8)]));
assert.equal(eos.generated,2);assert.equal(eos.mobile,2);assert.equal(eos.uncommitted,6);assert.equal(eos.share,1);
assert.equal(contribution(run('local_draft',[block('local_draft',8,7,7)])).mobile,0);
assert.equal(contribution(run('lookup',[block('lookup',4,3,3)])).mobile,0);
assert.equal(contribution(run('host',[block('host',3)])).share,0);
for(const value of [null,run('remote_draft',[]),run('remote_draft',[{generated:2}]),run('remote_draft',[block('remote_draft',3,4,4)]),run('remote_draft',[block('remote_draft',2,1,1)],{node_id:null}),run('remote_draft',[block('remote_draft',2,1,1)],{metrics:{generated_tokens:3}}),run('remote_draft',[block('remote_draft',Infinity,1,1)]),run('host',[block('remote_draft',2,1,1)])])assert.equal(contribution(value).measured,false);
assert.equal(contribution(run('remote_draft',[block('remote_draft',2,1,1)],{backend:'openrouter'})).applicable,false);
assert.equal(contribution(run('host',[block('host',2)],{backend:'local_api'})).applicable,false);
assert.equal(memoryScope({os:'iOS 19'}),'Process allocation headroom');
assert.equal(memoryScope({os:'Android 17'}),'System available memory');
assert.equal(memoryScope({os:'unknown'}),'Available memory · scope unknown');
const jobs=[
 {node:'phone',kind:'network_paced',state:'completed',finished:20,result:{samples:[{kind:'rtt',ms:10,pace_ms:0},{kind:'rtt',ms:4,pace_ms:0},{kind:'rtt',ms:100,pace_ms:30},{kind:'download',bytes:1000000,ms:20},{kind:'download',bytes:1000000,ms:30},{kind:'download',bytes:2000000,ms:20},{kind:'upload',bytes:1000000,ms:100},{kind:'download',bytes:1,ms:0}]}},
 {node:'phone',kind:'network',state:'completed',finished:10,result:{samples:[{kind:'rtt',ms:999}]}},
 {node:'phone',kind:'network',state:'failed',finished:30,result:{samples:[{kind:'rtt',ms:999}]}},
 {node:'other',kind:'network',state:'completed',finished:40,result:{samples:[{kind:'rtt',ms:999}]}},
 {node:'phone',kind:'cpu',state:'completed',finished:22,result:{samples:[{kind:'cpu',iterations:100,ms:1000},{kind:'cpu',iterations:50,ms:500}]}}
];
const m=measurements(jobs,'phone');assert.equal(m.networkAt,20);assert.deepEqual(m.rtt.map(r=>[r.pace,r.median]),[[0,4],[30,100]]);
assert.equal(m.transfer.length,3);assert.equal(m.transfer.find(r=>r.kind==='download'&&r.bytes===1000000).mbps,40);assert.equal(m.cpuIterationsPerSecond,100);
assert.equal(measurements([], 'phone').cpuIterationsPerSecond,null);assert.equal(measurements([], 'phone').networkAt,null);
// Six-device routing at narrow, two-column and wide layouts. Every segment must
// stay out of all card interiors, including earlier cards in the same column.
function intersectsInterior(a,b,r) {
  const right=r.left+r.width,bottom=r.top+r.height;
  if(a[0]===b[0])return a[0]>r.left&&a[0]<right&&Math.max(a[1],b[1])>r.top&&Math.min(a[1],b[1])<bottom;
  return a[1]>r.top&&a[1]<bottom&&Math.max(a[0],b[0])>r.left&&Math.min(a[0],b[0])<right;
}
for(const [width,columns,padding] of [[390,1,18],[700,2,24],[1100,3,24]]) {
  const gap=18,cardWidth=(width-padding*2-gap*(columns-1))/columns;
  const host={left:(width-310)/2,top:32,width:310,height:155};
  const cards=Array.from({length:6},(_,i)=>({left:padding+(i%columns)*(cardWidth+gap),top:270+Math.floor(i/columns)*230,width:cardWidth,height:i%2?200:160}));
  for(const card of cards){
    const points=edgePoints(host,card);
    assert.deepEqual(points.at(-1),[card.left,card.top+card.height/2]);
    assert.equal(points[2][0],card.left-10);
    for(let i=1;i<points.length;i++)for(const other of [host,...cards])assert.equal(intersectsInterior(points[i-1],points[i],other),false,`route crosses a card at ${width}px/${columns} columns`);
  }
}
console.log('Device graph: remote/local/fallback/EOS/missing-data attribution, memory scopes and dated network grouping passed.');
