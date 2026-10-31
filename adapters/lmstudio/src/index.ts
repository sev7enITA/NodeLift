import { type PluginContext, type GeneratorController, type Chat } from "@lmstudio/sdk";
import {configSchematics,globalConfigSchematics} from "./config.js";
import {consumeStream} from "./stream.js";

export async function generate(ctl:GeneratorController,chat:Chat) {
  const global=ctl.getGlobalPluginConfig(globalConfigSchematics),config=ctl.getPluginConfig(configSchematics);
  const key=global.get("apiKey").trim();
  if(!key)throw new Error("Set the NodeLift client API key in this generator's settings.");
  if(chat.hasFiles())throw new Error("NodeLift 0.2 supports text messages only.");
  const messages=chat.map(message=>{
    const role=message.getRole();
    if(role==="tool" || message.getToolCallRequests().length || message.getToolCallResults().length)
      throw new Error("Tool conversations are not qualified for NodeLift 0.2.");
    return {role,content:message.getText()};
  });
  const mode=config.get("mode"),node=config.get("nodeId").trim();
  if(mode==="remote_draft" && !node)throw new Error("Choose a native mobile node ID first.");
  const signal=AbortSignal.any([ctl.abortSignal,AbortSignal.timeout(300000)]);
  const response=await fetch(`http://127.0.0.1:${global.get("port")}/v1/chat/completions`,{
    method:"POST",redirect:"error",signal,headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`},
    body:JSON.stringify({model:"nodelift",messages,temperature:0,stream:true,max_tokens:config.get("maxTokens"),
      nodelift_mode:mode,nodelift_node_id:node || null,nodelift_draft_k:config.get("draftK"),
      nodelift_draft_policy:config.get("draftPolicy")})});
  await consumeStream(response,text=>ctl.fragmentGenerated(text),signal);
}

export async function main(context:PluginContext) {
  context.withConfigSchematics(configSchematics).withGlobalConfigSchematics(globalConfigSchematics).withGenerator(generate);
}
