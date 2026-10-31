import { createConfigSchematics } from "@lmstudio/sdk";

export const globalConfigSchematics=createConfigSchematics()
  .field("apiKey","string",{displayName:"NodeLift client API key",isProtected:true,
    subtitle:"Copy the client key from NodeLift. This is separate from dashboard administration."},"")
  .field("port","numeric",{displayName:"Local gateway port",int:true,min:1,max:65535},9868).build();

export const configSchematics=createConfigSchematics()
  .field("mode","select",{displayName:"Execution mode",options:[
    {value:"host",displayName:"Host only"},{value:"local_draft",displayName:"Local draft experiment"},
    {value:"remote_draft",displayName:"Mobile draft experiment"}]},"host")
  .field("nodeId","string",{displayName:"Mobile node ID",subtitle:"Required for mobile drafting; select an online native node in NodeLift."},"")
  .field("draftK","numeric",{displayName:"Draft block",int:true,min:1,max:16},4)
  .field("maxTokens","numeric",{displayName:"Maximum output tokens",int:true,min:1,max:512},128).build();
