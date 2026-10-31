import test from 'node:test';
import assert from 'node:assert/strict';
import {consumeStream} from '../dist/stream.js';
const event=content=>'data: '+JSON.stringify({choices:[{delta:{content}}]})+'\r\n\r\n';
function response(text,width=1){const bytes=new TextEncoder().encode(text);return new Response(new ReadableStream({start(controller){for(let i=0;i<bytes.length;i+=width)controller.enqueue(bytes.slice(i,i+width));controller.close();}}));}
test('fragmented UTF-8, heartbeat, ordered text, explicit completion',async()=>{
  let output='';await consumeStream(response(': working\n\n'+event('Città ')+event('🌍')+'data: [DONE]\n\n'),s=>output+=s,new AbortController().signal);
  assert.equal(output,'Città 🌍');
});
test('truncated response and server error fail visibly',async()=>{
  await assert.rejects(consumeStream(response(event('partial')),()=>{},new AbortController().signal),/before completion/);
  await assert.rejects(consumeStream(response('data: {"error":{"message":"thermal pause"}}\n\n'),()=>{},new AbortController().signal),/thermal pause/);
});
test('cancellation prevents output',async()=>{
  const ctl=new AbortController();ctl.abort();let calls=0;
  await assert.rejects(consumeStream(response(event('unexpected')),()=>calls++,ctl.signal));assert.equal(calls,0);
});
