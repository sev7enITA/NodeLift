/** Parse a bounded SSE text stream, including fragmented UTF-8 and explicit failure. */
export async function consumeStream(response:Response,onText:(text:string)=>void,signal:AbortSignal) {
  if(!response.ok)throw new Error(`NodeLift returned HTTP ${response.status}: ${(await response.text()).slice(0,300)}`);
  if(!response.body)throw new Error("NodeLift returned no stream");
  const reader=response.body.getReader(),decoder=new TextDecoder();let pending="",done=false;
  try {
    while(!done) {
      signal.throwIfAborted();const value=await reader.read();
      if(value.done)break;
      pending+=decoder.decode(value.value,{stream:true});
      if(pending.length>262144)throw new Error("Oversized NodeLift event");
      let newline:number;
      while((newline=pending.indexOf("\n"))>=0) {
        const line=pending.slice(0,newline).replace(/\r$/,"");pending=pending.slice(newline+1);
        if(!line.startsWith("data: "))continue;
        const data=line.slice(6);
        if(data==="[DONE]"){done=true;break;}
        const event=JSON.parse(data);
        if(event.error)throw new Error(String(event.error.message ?? event.error));
        const content=event.choices?.[0]?.delta?.content;
        if(typeof content==="string")onText(content);
      }
    }
    if(!done)throw new Error("NodeLift stream ended before completion");
  } finally {await reader.cancel().catch(()=>{});reader.releaseLock();}
}
