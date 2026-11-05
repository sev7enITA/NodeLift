/* Meaningful browser lifecycle tests without a browser or live invitation. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.join(__dirname,'../host/nodelift');
const nodes=new Map();
function node(id){if(!nodes.has(id))nodes.set(id,{hidden:true,value:'',textContent:'',disabled:false,open:false,focus(){},setAttribute(k,v){this[k]=v},removeAttribute(k){delete this[k]},scrollIntoView(){},getContext(){return {fillRect(){},clearRect(){}};}});return nodes.get(id);}
let now=1800000000000,timer=null,handler={};
const context=vm.createContext({URL,console,Date:class extends Date{static now(){return now}},document:{getElementById:node,addEventListener:(e,f)=>handler[e]=f},window:{addEventListener(){}},setInterval:f=>(timer=f,1),clearInterval:()=>timer=null,navigator:{clipboard:{writeText:async()=>{}}}});
vm.runInContext(fs.readFileSync(path.join(root,'vendor/qrcodegen.js'),'utf8')+'\n'+fs.readFileSync(path.join(root,'pairing.js'),'utf8')+'\nthis.pairing=NodeLiftPairing;',context);
const fixture={protocol:1,url:'https://192.168.1.9:9867',certificate:'-----BEGIN CERTIFICATE-----\n'+Buffer.alloc(800,31).toString('base64')+'\n-----END CERTIFICATE-----',invite:'a'.repeat(32),sha256:'b'.repeat(64),expires_at:now/1000+300};
assert.ok(context.pairing.encode(fixture).startsWith('nodelift://pair/v1/192.168.1.9:9867/'));
const roaming={...fixture,protocol:2,tls_name:'nodelift-'+'c'.repeat(32)+'.local'};
const compact=context.pairing.encode(roaming);
assert.ok(compact.startsWith('nodelift://pair/v2/192.168.1.9:9867/'));
assert.ok(compact.includes('/'+roaming.tls_name+'/'));
assert.throws(()=>context.pairing.encode({...roaming,tls_name:'*.local'}));
assert.throws(()=>context.pairing.encode({...roaming,protocol:3}));
let pending=true,calls=[],deferred=null,errors=[],revokeFails=false;
const api=async(route,body)=>{calls.push([route,body]);if(route==='invite')return deferred?await deferred:structuredClone(fixture);if(route==='invite/status')return {pending};if(revokeFails)throw Error('offline');return {pending:false};};
const controller=context.pairing.mount({api,t:(s,...args)=>s.replace(/\{(\d+)\}/g,(_,i)=>args[i]),authenticated:()=>true,error:e=>errors.push(e.message)});
(async()=>{
 await controller.open();assert.equal(node('pairing').hidden,false);assert.equal(node('pairing-qr').hidden,false);assert.ok(node('ticket').value);assert.ok(node('pairing-identity').textContent.endsWith(Array(16).fill('bbbb').join(' ')));assert.ok(node('pairing-identity')['aria-label'].endsWith(Array(64).fill('b').join(' ')));handler['nodelift-languagechange']();assert.ok(node('pairing-identity').textContent.endsWith(Array(16).fill('bbbb').join(' ')));
 await controller.close();assert.equal(node('pairing').hidden,true);assert.equal(node('ticket').value,'');assert.equal(node('pairing-qr').hidden,true);assert.equal(calls.at(-1)[0],'invite/revoke');
 await controller.open();pending=false;await timer();assert.equal(node('ticket').value,'');assert.equal(node('pairing-qr').hidden,true);assert.match(node('expiry').textContent,/used or closed/);
 pending=true;await controller.open();now+=301000;await timer();assert.match(node('expiry').textContent,/expired/);assert.equal(node('ticket').value,'');now-=301000;
 let resolve;deferred=new Promise(r=>resolve=r);const opening=controller.open();controller.clear();resolve(fixture);await opening;assert.equal(node('pairing').hidden,true);assert.equal(node('ticket').value,'');assert.equal(calls.at(-1)[0],'invite/revoke');deferred=null;
 await controller.open();revokeFails=true;await controller.close();assert.equal(node('pairing-qr').hidden,true);assert.match(errors.at(-1),/could not be confirmed/);
 console.log('PASS: QR lifecycle, consumed/expired cleanup, close revocation, stale-response race and revocation failure.');
})().catch(e=>{console.error(e);process.exitCode=1});
