/* Contextual-help policy tests. Native focus trapping and rendering need browser checks. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),source=fs.readFileSync(path.join(root,'host/nodelift/dashboard.js'),'utf8');
const html=fs.readFileSync(path.join(root,'host/nodelift/dashboard.html'),'utf8');
const helpSource=source.slice(source.indexOf('const contextHelpTopics = '),source.indexOf('sessionReady(false);refresh();setInterval(refresh,3000);',source.indexOf('const contextHelpTopics = ')));
const ids=[...html.matchAll(/data-context-help="([^"]+)"/g)].map(m=>m[1]);
assert.equal(new Set(ids).size,28);for(const label of html.matchAll(/<label\b[\s\S]*?<\/label>/g))assert.doesNotMatch(label[0],/data-context-help=/,'help buttons must not activate the associated form input');
for(const button of html.matchAll(/<button\b[^>]*data-context-help=[^>]*>/g))assert.match(button[0],/type="button"/,'help never submits a form');
assert.match(html,/<dialog[^>]*aria-labelledby="context-help-title"[^>]*aria-describedby="context-help-body"/);
function setup({saved=null,blocked=false}={}){
 const nodes=new Map(),documentEvents=new Map(),windowEvents=new Map();let lang='en',writes=[];
 class Element{
  constructor(){this.dataset={};this.attributes={};this.hidden=false;this.checked=true;this.open=false;this.isConnected=true;this.events=new Map();this.focusCount=0;this.textContent='';}
  setAttribute(k,v){this.attributes[k]=v;}getAttribute(k){return this.attributes[k];}
  addEventListener(k,fn){this.events.set(k,fn);}focus(){this.focusCount++;}showModal(){this.open=true;}close(){this.open=false;this.events.get('close')?.({});}
  getBoundingClientRect(){return {left:20,right:480,top:30,bottom:400};}contains(target){return target===this||target===node('context-help-enabled');}querySelector(){return node('options-summary');}
 }
 function node(id){if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id);}
 const triggers=ids.map(id=>{const b=new Element();b.dataset.contextHelp=id;return b;});
 const localStorage={getItem(){if(blocked)throw Error('denied');return saved;},setItem(k,v){if(blocked)throw Error('denied');saved=v;writes.push([k,v]);}};
 const context=vm.createContext({document:{querySelectorAll:()=>triggers,addEventListener:(k,fn)=>documentEvents.set(k,fn)},window:{addEventListener:(k,fn)=>windowEvents.set(k,fn)},localStorage,$:node,t:(key,...args)=>(lang==='en'?'':lang+':')+key.replace(/\{(\d+)\}/g,(_,i)=>args[i])});
 vm.runInContext(helpSource,context);
 return {node,triggers,writes,context,documents:documentEvents,windows:windowEvents,setLanguage(value){lang=value;documentEvents.get('nodelift-languagechange')();},setStored(value){saved=value;},click(i=0){triggers[i].events.get('click')();}};
}
let x=setup();const dialog=x.node('context-help-dialog');assert(x.triggers.every(b=>!b.hidden));x.click();assert.equal(dialog.open,true);assert.equal(x.triggers[0].attributes['aria-expanded'],'true');assert.equal(x.node('close-context-help').focusCount,1);assert.match(x.node('context-help-body').textContent,/Pairing authorizes a device/);
x.setLanguage('it');assert.match(x.node('context-help-title').textContent,/^it:/);assert.match(x.triggers[0].attributes['aria-label'],/^it:/);
let prevented=false;dialog.events.get('cancel')({preventDefault(){prevented=true;}});assert(prevented);assert.equal(dialog.open,false);assert.equal(x.triggers[0].attributes['aria-expanded'],'false');assert.equal(x.triggers[0].focusCount,1);
x.click(1);dialog.events.get('click')({target:dialog,clientX:60,clientY:80});assert(dialog.open,'click on dialog padding does not dismiss');dialog.events.get('click')({target:dialog,clientX:0,clientY:0});assert.equal(dialog.open,false);assert.equal(x.triggers[1].focusCount,1);
x.click(2);x.node('context-help-enabled').checked=false;x.node('context-help-enabled').events.get('change')();assert.equal(dialog.open,false);assert(x.triggers.every(b=>b.hidden));assert.deepEqual(x.writes,[['nodelift-context-help','off']]);x.click();assert.equal(dialog.open,false,'disabled help cannot reopen');
x=setup({saved:'off'});assert(x.triggers.every(b=>b.hidden));assert.equal(x.node('context-help-enabled').checked,false);x.node('context-help-enabled').checked=true;x.node('context-help-enabled').events.get('change')();assert(x.triggers.every(b=>!b.hidden));
x=setup({blocked:true});assert(x.triggers.every(b=>!b.hidden));x.node('context-help-enabled').checked=false;x.node('context-help-enabled').events.get('change')();assert.equal(x.node('context-help-storage').hidden,false);assert(x.triggers.every(b=>b.hidden));
x=setup();x.click();x.setStored('off');x.windows.get('storage')({key:'nodelift-context-help'});assert.equal(x.node('context-help-dialog').open,false);assert(x.triggers.every(b=>b.hidden));x.setStored(null);x.windows.get('storage')({key:null});assert(x.triggers.every(b=>!b.hidden));
x.node('dashboard-options').open=true;x.documents.get('keydown')({key:'Escape'});assert.equal(x.node('dashboard-options').open,false);assert.equal(x.node('options-summary').focusCount,1);
x.node('dashboard-options').open=true;x.documents.get('click')({target:{}});assert.equal(x.node('dashboard-options').open,false);
console.log('PASS: 28 independent help actions, default/persistent disabled state, storage denial, exact topic text, language refresh, Escape/close/backdrop focus return and cross-tab preferences. No network or inference triggered.');
