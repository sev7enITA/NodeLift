# Models and providers

The Models panel offers three local import paths:

| Path | How to use it | Boundary |
|---|---|---|
| Existing GGUF | Enter an absolute local path and choose **Add path** | Registers without copying |
| Browser file import | Select a complete GGUF and choose **Import selected file** | Uses bounded upload chunks |
| Hugging Face | Search a public repository, inspect files, review the model card/license, select a GGUF and download | Pinned revision and SHA-256; restricted models require manual download |

Import validates the header. Loading in the pinned runtime determines architecture support. Split GGUF sets, automatic safetensors conversion and model-supplied Python are not supported. Target/draft vocabulary IDs must have compatible meaning. The native verifier currently refuses recurrent/hybrid architectures that lack qualified state rollback.

Select **NodeLift native · local cluster** for NodeLift’s host/local/phone strategies.

For **OpenRouter**, expand External engines and cloud access, save a session key, refresh models, explicitly select OpenRouter and review the model’s rates before generation. Prompts leave the local network and charges may apply. There is no automatic cloud fallback; restart clears provider keys from host memory.

For **Local API · oMLX / LM Studio**, enter that server’s loopback URL ending in `/v1`, refresh its catalog and select a model. This route calls the external server for text generation. Its caching, loading and scheduling remain external; NodeLift does not add phone drafting to that route.

Ollama itself is not patched. Compatible clients can call NodeLift’s documented OpenAI-style text subset; API shape alone does not establish complete client compatibility.

[API, SDK adapter and provider instructions](https://github.com/sev7enITA/NodeLift/blob/main/docs/INTEGRATIONS.md) · [Repository reuse assessment](https://github.com/sev7enITA/NodeLift/blob/main/research/integrations-2026-11-01/ASSESSMENT.md)
