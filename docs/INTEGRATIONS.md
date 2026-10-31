# Local client integrations

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
