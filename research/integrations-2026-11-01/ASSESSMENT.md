# Model sources, LM Studio and oMLX assessment

Assessment date: 1 November 2026. Source snapshots are pinned below. This is an integration and source review, not a comparative performance benchmark.

## What was already considered

Before this assessment, NodeLift had a pinned llama.cpp native engine, an LM Studio generator adapter using `@lmstudio/sdk`, a restricted OpenAI-compatible gateway, automatic discovery of local GGUF files in `.models` and LM Studio's model folder, and a script downloading two pinned Qwen control models. SDK-to-handler-to-live-NodeLift streaming had been tested; a full installed LM Studio generator flow had not been qualified. The organization as a whole had **not** been audited. oMLX was **not** in the previous assessment.

The [31 October comparison](../comparison-2026-10-31/ASSESSMENT.md) and [machine-readable atlas](../../site/NodeLift/data/comparison.json) cover 55 entries, including DistAI, prima.cpp, exo, PhoneBorg, InferRing, Pooled, Cake, Petals, LinguaLinked, llama.cpp, MLX, MNN, ncnn, MindSpore Lite, Paddle/FastDeploy, KTransformers, PowerInfer, GenieX, LiteRT-LM and ExecuTorch, plus research such as WISP, EdgeShard and DiP-SD. Inclusion in that atlas means documentary comparison; it does not mean all their code was audited or incorporated. The [Jev/local-project optimization report](../optimization-2026-10-31/REPORT.md) records which scheduling lessons were implemented, and their observed limitations.

## LM Studio organization: component decisions

`github.com/lmstudio-ai` is an organization, not a single repository. Public component licenses do not establish a license to copy the desktop application's private code or assets.

| Repository | Snapshot | License read | Review depth / useful parts | NodeLift decision |
|---|---|---|---|---|
| [lmstudio-js](https://github.com/lmstudio-ai/lmstudio-js) | `4b9af903e866808013524eece1e9ceb7a7f18c68` | MIT | README/license plus existing NodeLift SDK adapter | Continue SDK dependency; do not fork the SDK just to wrap requests |
| [lmstudio-python](https://github.com/lmstudio-ai/lmstudio-python) | `16796832c1665985c73f5a9e938cbf17b40adf02` | MIT | README/license; programmatic model management and inference | Candidate for richer future LM Studio management; today's generic text bridge needs no SDK dependency |
| [lms](https://github.com/lmstudio-ai/lms) | `43d4b2680e3cf679ad19753fcc7af0cb0e4a12a2` | MIT | README/license; local CLI model/server lifecycle | Optional future discovery/provisioning adapter; no automatic installation or shell interpolation |
| [mlx-engine](https://github.com/lmstudio-ai/mlx-engine) | `ab523663477bcde9b7092710eec41da02990e991` | MIT | README/license, supported MLX stack and speculative decoding demo | Candidate Apple Silicon backend. Different tokenizer/KV/runtime contracts; not a drop-in Android/iOS shard engine |
| [model-catalog](https://github.com/lmstudio-ai/model-catalog) | `78bd5602295154a6477fa440fa45e024c62a26f5` | Apache-2.0 | README/license; schema includes architecture, format, quantization and sources, version 0.0.1 with legacy GGML examples | Adopt the idea of explicit provenance/format, not the old catalog as an authoritative current list |
| [venvstacks](https://github.com/lmstudio-ai/venvstacks) | `c2e47ed7964d5ab206c98ba2ebc4e12e3e5c0c51` | MIT | README/license; layered Python environment packaging | Useful if shipping an isolated MLX runtime; unnecessary for current standard-library host |

Organization inventory additionally identified `configs` (MIT), `localization` (Apache-2.0), `nq` (MIT), `office-document-processor-sources` (MPL-2.0), documentation and a bug tracker. They were inventoried, not implementation-reviewed. No code from these repositories was copied in this change. The existing SDK retains its dependency license; a future fork must preserve the relevant notices.

## oMLX: source-level findings

Repository: [jundot/omlx](https://github.com/jundot/omlx), commit [`17fce1d939f65a3cb92616862710c3007ea32b95`](https://github.com/jundot/omlx/tree/17fce1d939f65a3cb92616862710c3007ea32b95), 31 October 2026. Root LICENSE is Apache-2.0. Files acquired at that immutable revision: README, LICENSE, pyproject, distributed-cluster guide, HF downloader, prefix cache, engine pool and distributed engine. Inspection was targeted, not a full audit of these large modules.

| Component/source | Lesson supported by the source | NodeLift application / boundary |
|---|---|---|
| [`omlx/admin/hf_downloader.py`](https://github.com/jundot/omlx/blob/17fce1d939f65a3cb92616862710c3007ea32b95/omlx/admin/hf_downloader.py) | Durable download jobs, cancellation around Hub/Xet work, distinction between LFS content SHA-256 and Git blob IDs, model-format filtering | New native GGUF library uses immutable Hub commits, published LFS size/SHA-256, bounded writes, cancellation and atomic publication. It does not treat a Git blob ID as a content SHA-256. Initial implementation deliberately has one transfer, no resume and public repositories only |
| [`omlx/engine_pool.py`](https://github.com/jundot/omlx/blob/17fce1d939f65a3cb92616862710c3007ea32b95/omlx/engine_pool.py) | Separate resident, admission and dynamic memory ceilings; evict idle models before new allocations. Source comments describe overcommit/model-swap problems and stable residency decisions | Future NodeLift capacity admission needs weights + KV + workspace + headroom per device, not addition of advertised free RAM. Current new file import checks disk capacity, not a proven RAM admission planner |
| [`omlx/cache/prefix_cache.py`](https://github.com/jundot/omlx/blob/17fce1d939f65a3cb92616862710c3007ea32b95/omlx/cache/prefix_cache.py) | Cache identity, references and eviction must remain consistent across reuse; substantial hybrid-cache and rotating-cache complexity | Do not transplant Python/MLX cache objects into llama.cpp's native contexts. A future cache requires model/tokenizer/quantization/context/runtime identity and ownership tests |
| [`docs/experimental/distributed-cluster.md`](https://github.com/jundot/omlx/blob/17fce1d939f65a3cb92616862710c3007ea32b95/docs/experimental/distributed-cluster.md) | Experimental contiguous layer pipeline, rank-local weights and KV, measured collective/compute calibration, unequal-memory placement, runtime/source preflight and group teardown | Strong reference for future capacity sharding. The guide also documents experimental Mac/CUDA execution, not verified Android/iOS support. NodeLift's phone proposal path does not yet implement this capacity pool |
| OpenAI-compatible API | Runtime isolation permits a common text interface without merging native dependencies | Implemented opt-in loopback text adapter suitable for oMLX or LM Studio. It does not control oMLX's cluster, cache or model installation, and must not be described as mobile distributed MLX |

The guide explicitly keeps KV with the layers that own it: moving KV across the network for every layer/token would add transfer to the critical path. This is a sound design input for our future planner, not a measured NodeLift gain. The oMLX failure policy avoids silently loading a whole model on the coordinator if a worker fails; capacity mode should likewise fail clearly when fallback would exceed memory.

Root Apache-2.0 permits reuse subject to its terms, but custom kernel subdirectories have additional upstream license files. No oMLX code/kernels/assets were copied or vendored here. The bridge is independently implemented against the public HTTP contract, so oMLX can evolve independently. Installing and benchmarking its actual runtime remains separate work.

## Implemented integration contract

- **Hugging Face:** explicit public GGUF search, repository inspection, card/license link, immutable revision selection and SHA-256/size verification. Only complete, single-file GGUF models with published LFS metadata. No remote Python execution, automatic conversion, model license acceptance, private/gated credentials or split-GGUF support. Search/downloads require internet; inference from downloaded files remains local. Network failure discards the partial file; retry starts over. Existing arbitrary local GGUF files can be registered without copying or uploaded from the browser in 1 MiB chunks.
- **OpenRouter:** explicit cloud backend, public model catalog/prices, text-only SSE, session-only BYOK, separate run identity, no automatic retries/fallback. Routing requests disallow provider fallback and data-collection providers according to OpenRouter's policy fields; these are requested routing constraints, not a guarantee about a vendor's practices. No paid generation was used to qualify this change. Real provider capabilities, availability, bills, key permissions and model behavior remain account/model dependent.
- **Local API:** explicit loopback HTTP `/v1` text backend for an already-running oMLX/LM Studio-compatible server. Socket connects to literal `127.0.0.1`, rejects redirects, remote hostnames and NodeLift's normal own ports. No auto-install or server startup, no model conversion, multimodal/tool support, or phone delegation through this route.
- **Evidence:** native, local external-server and cloud records are distinguishable. External token usage is included only if returned by the provider; token IDs and decode speed are not invented. Time to first text and end-to-end wall time are measured on NodeLift's client path, not server kernel performance.
- **Credentials:** administrative localhost origin and bearer checks apply to source/provider operations; the client key cannot manage them. Keys remain in host process memory, never status/export/state JSON or download URLs. A process restart clears keys and external catalogs. A client must explicitly pass `nodelift_backend` and `nodelift_provider_model` to use external routing; the default stays native regardless of dashboard selection.

Primary interface references: [Hugging Face model metadata API](https://huggingface.co/docs/huggingface_hub/package_reference/hf_api), [Hub API](https://huggingface.co/docs/hub/api), [OpenRouter API overview](https://openrouter.ai/docs/api_reference/overview), [OpenRouter provider routing](https://github.com/OpenRouterTeam/docs/blob/main/guides/routing/provider-selection.mdx).

## Qualification

See [VALIDATION.md](VALIDATION.md) for this change's test evidence and unresolved runtime qualification. None of these integrations establishes acceleration of a large model by phones. The existing native benchmark conclusions remain unchanged.
