/* Exercise the browser formatter offline, including blocked storage and literal parameters. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../host/nodelift/i18n.js'),'utf8');
function session(stored, blocked=false) {
  const values=new Map(stored ? [['nodelift-language',stored]] : []);
  const document={documentElement:{lang:''},querySelectorAll:()=>[],getElementById:()=>null,dispatchEvent:()=>{}};
  const context=vm.createContext({document,navigator:{language:'zh-CN'},Event:class {},localStorage:{
    getItem:key=>{if(blocked)throw Error('blocked');return values.get(key);},
    setItem:(key,value)=>{if(blocked)throw Error('blocked');values.set(key,value);}
  }});
  vm.runInContext(source+'\nthis.i18n=NodeLiftI18n;',context);
  return {i18n:context.i18n,document,values};
}
const fresh=session();assert.equal(fresh.i18n.language,'en');assert.equal(fresh.document.documentElement.lang,'en');
assert.equal(session('invalid').i18n.language,'en');assert.equal(session(undefined,true).i18n.language,'en');
fresh.i18n.setLanguage('zh-Hans');assert.equal(fresh.document.documentElement.lang,'zh-Hans');
assert.equal(fresh.i18n.t('Add device'),'添加设备');
assert.equal(fresh.i18n.t('CPU · {0} iterations in {1} ms',9,123),'CPU · 123 毫秒内完成 9 次迭代');
assert.equal(fresh.i18n.t('Measurement interrupted: {0}','<script>{1}$&你好</script>'),'测量已中断：<script>{1}$&你好</script>');
assert.equal(fresh.i18n.t('unknown external diagnostic'), 'unknown external diagnostic');
assert.equal(fresh.i18n.t('toString'),'toString');
assert.equal(session(fresh.values.get('nodelift-language')).i18n.language,'zh-Hans');
fresh.i18n.setLanguage('en');assert.equal(fresh.i18n.t('Add device'),'Add device');
assert.equal(fresh.i18n.t('Completata'),'Completata'); // arbitrary payloads are not translated by guessing
const blocked=session(undefined,true);blocked.i18n.setLanguage('zh-Hans');assert.equal(blocked.i18n.t('Add device'),'添加设备');
console.log('Localization runtime: default, persistence, switching, fallback, parameter isolation and blocked storage passed.');
