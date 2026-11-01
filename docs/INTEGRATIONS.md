# Local client integrations

The integration objective is to make NodeLift's shared local RAM/compute execution available through the interfaces the user already uses. The local gateway and adapters are the access paths; the control room manages resources. Cloud-provider forwarding is an optional, separate route. See the [product roadmap and candidate interface matrix](ROADMAP.md) for current limits and unimplemented capacity work.

This is an authenticated OpenAI-style **text chat subset**, not full OpenAI/Ollama API compatibility.

| Setting | Value |
|---|---|
| Base URL | `http://127.0.0.1:9868/v1` |
| Model | `nodelift` |
| Key | Dedicated client key in the dashboard API panel |
| Sampling | Temperature 0, top_p 1, n 1, zero penalties |
| Messages | Text system/user/assistant, 1–32 entries, combined prompt ≤32 KiB |
| Output | 1–512 tokens, EOS respected; JSON or SSE |

Endpoints: `GET /v1/models`, `POST /v1/chat/completions`. Extra fields: `nodelift_mode` (`host`, `local_draft`, `remote_draft`, `lookup`), `nodelift_node_id`, `nodelift_draft_k` (1–16), `nodelift_remote_timeout_ms` (500–60000, default 30000; timeout triggers host fallback). `nodelift_draft_policy` selects `fixed` (default) or experimental `adaptive`. Adaptive control starts with four host tokens, measures proposal rounds, and returns to host when the observed cost loses. Its remote probe deadline can be shorter than the configured ceiling (down to 20 ms). `lookup` proposes already-seen context continuations and needs no draft model. Every proposal is target-verified; backend batch/single argmax differences remain possible. Host is the default. Use one of `max_tokens`/`max_completion_tokens`. Supported optional null fields use defaults. Tools, stop strings, logit bias, seeds and response formats fail explicitly. Usage includes a generated EOG token when emitted by the core.

Client and administrator keys have separate authority. No public listener/CORS is enabled. A container's own loopback is not the host: do not blindly bind this gateway to `0.0.0.0` to work around topology.

## LM Studio

The adapter uses the documented [generator mechanism](https://lmstudio.ai/docs/typescript/plugins/generator), forwarding messages and committed text, rejecting file/tool conversations and propagating cancellation.

```sh
cd adapters/lmstudio
npm ci --ignore-scripts
npm test
lms dev
```

The Deno manifest restricts network to loopback and disallows filesystem access. The installed CLI rejected sandboxing with a Node runner. Configure the protected client-key field and local port; per-chat controls select mode, fixed/adaptive draft control, node ID, block and output budget. Target selection stays in NodeLift. LM Studio sampling controls do not configure this generator: the current engine is greedy only.

TypeScript, stream tests and actual SDK Chat → handler → live NodeLift inference passed. Installation and a full generation inside LM Studio's GUI require separate verification. No plugin was published to LM Studio Hub.

## Ollama and other clients

[Ollama exposes its own OpenAI-style subset](https://docs.ollama.com/api/openai-compatibility); that does not make an arbitrary engine an internal Ollama plugin. NodeLift does not intercept or split an Ollama model.

Clients with a configurable OpenAI-style text endpoint can point directly to NodeLift. Their default parameters, tools, network topology and streaming expectations still require individual qualification.

## Z.ai and Xiaomi MiMo

These are hosted web environments, distinct from local runtimes and from Xiaomi phone hardware. Both publish developer APIs: [Z.ai](https://docs.z.ai/guides/overview/quick-start) and [MiMo](https://mimo.mi.com/docs/en-US/quick-start/summary/first-api-call). NodeLift does not currently include direct adapters for either API, and no connection from their hosted GUI to a custom NodeLift endpoint has been qualified. Browser access alone is not API access. A cloud-provider adapter would use their backend, not expand local resources. For the local-resource objective, assess supported extension/tool points or an explicit browser companion route to NodeLift; neither is implemented or proven here, and neither adds RAM to a remote proprietary model. See [product shape and device attribution](DEVICE-GRAPH.md).

## Model sources and external engines (host 0.3.0 preview)

The **Models** section now supports public Hugging Face search and immutable GGUF downloads, registration of an existing absolute local model path without copying, and browser file import. Select a model as target/draft and apply configuration before native inference. Complete single-file GGUF v2/v3 is the import format; the pinned llama.cpp runtime still determines architecture support at load time. No pickle/Python execution, automatic safetensors conversion, split-file assembly or remote license acceptance occurs. An interrupted download must restart; partial files are not model candidates.

For OpenRouter, expand **External engines and cloud access**, enter your key locally, save session access and refresh the provider catalog. In **Execution backend**, explicitly select **OpenRouter**, choose the model, review its displayed rates, then Run. Keys are memory-only and cleared by a host restart. Generations may incur charges. No cloud request is made by native generation, status polling, or merely selecting a backend. Public catalog queries need no key.

For oMLX or LM Studio's local server, configure **Local API** with `http://127.0.0.1:8000/v1` or the server's actual loopback port (LM Studio commonly uses 1234), save session access and refresh models. Select **Local API** in the run form. Only text streaming is supported. The external server owns loading, cache, scheduling and its own distributed features. This bridge does not supply phone drafting or merge native caches across runtimes. The bridge requires a completion reason and `[DONE]`; a truncated stream is an error. No request is automatically retried.

Client calls to NodeLift's `/v1/chat/completions` continue to default to native execution, independently of dashboard selection. To opt into an external engine explicitly:

```json
{
  "model": "nodelift",
  "messages": [{"role": "user", "content": "Hello"}],
  "nodelift_backend": "local_api",
  "nodelift_provider_model": "a-model-id-from-the-local-server",
  "max_tokens": 64,
  "stream": true
}
```

Use `openrouter` only for an intentionally cloud-routed request. Provider setup/catalog loading requires dashboard admin authority; the client key cannot change keys/endpoints or import models. External token usage is omitted if the provider does not report it. Phone lease endpoints and mobile credentials are unchanged. Mobile 0.2.3/build 5 adds Italian alongside English and Simplified Chinese. The host 0.3.0 integrations preview is separate from mobile engine qualification.

[Repository review and reuse decisions](../research/integrations-2026-11-01/ASSESSMENT.md) · [Validation and limits](../research/integrations-2026-11-01/VALIDATION.md).
