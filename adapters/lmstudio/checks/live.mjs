// Actual SDK Chat + adapter + real local target. Does not qualify LM Studio's GUI runtime.
import {readFile,writeFile} from 'node:fs/promises';
import {homedir} from 'node:os';
import {Chat} from '@lmstudio/sdk';
import {generate} from '../dist/index.js';
const apiKey=(await readFile(homedir()+'/.local/share/nodelift/client-api-key','utf8')).trim();
const global=new Map([['apiKey',apiKey],['port',9868]]);
const config=new Map([['mode','host'],['nodeId',''],['draftK',4],['maxTokens',32]]);
let output='',fragments=0;
const controller={getGlobalPluginConfig:()=>global,getPluginConfig:()=>config,
  abortSignal:new AbortController().signal,fragmentGenerated:text=>{output+=text;fragments++;}};
await generate(controller,Chat.from([{role:'user',content:'Explain RAM in one short sentence.'}]));
if(!output.trim() || !fragments)throw new Error('No generated content');
const result={scope:'SDK Chat and generator handler through live NodeLift; LM Studio UI runtime not exercised',
  passed:true,fragments,characters:output.length,timestamp:new Date().toISOString()};
await writeFile(new URL('../../../artifacts/lmstudio-live.json',import.meta.url),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
