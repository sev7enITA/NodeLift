# NodeLift — Detailed comparison atlas

**2026-10-31 · 55 selected entries · Dataset v1**

55 selected entries across distributed systems, mobile apps, runtimes, serving, baselines and research. Uniform criteria and primary sources; broad but non-exhaustive coverage, without a universal ranking.

[Method / Metodo](methodology.md)

Technical descriptions are canonical English. Upstream results are not NodeLift replications.

| Project | Category | Mobile compute | Memory / capacity |
|---|---|---|---|
| NodeLift | distributed | Implemented draft worker; Xiaomi evidence currently covers network/protocol only. | No target-weight sharding or shared RAM pool in 0.2.1. |
| DistAI | distributed | Yes: model layers and independent jobs. | Yes: distributed layer placement. |
| PhoneBorg | distributed | Yes: independent inference and BigBrain shards. | Yes: BigBrain model partitioning. |
| InferRing | distributed | Yes: Apple-device model execution. | Yes: memory distributed across devices. |
| Pooled / formerly SwarmLLM | distributed | Yes on capable browsers; ask-only guests do not contribute compute. | Yes: distributed layers and storage-backed expert loading. |
| Silica Cluster | distributed | Yes: pipeline shards. | Yes: documented layer allocation. |
| prima.cpp | distributed | Android and compatible Termux environments. | Yes: model placement across heterogeneous memory/storage. |
| exo | distributed | Not established for the current codebase. | Yes: supported cluster model sharding. |
| distributed-llama | distributed | Android/iOS companion qualification not established. | Yes: model weights distributed across nodes. |
| llama.cpp / RPC | runtime | Possible through native integration; mobile fleet qualification is separate. | Yes through RPC/offload on supported backends. |
| Petals | distributed | Not established. | Yes: model blocks distributed across peers. |
| LocalAI | serving | Not established. | Backend-dependent sharding, distinct from replica routing. |
| mycellm | distributed | Yes for the documented iOS peer. | Whole-model peer serving documented; cross-phone layer pooling not established. |
| Mesh LLM | distributed | Not established. | Yes: documented stage splits for supported dense models. |
| Cake | distributed | Yes, documented mobile worker integration. | Yes: layer sharding with weight delivery/caching. |
| Nakshatra | distributed | Not established. | Yes: contiguous layer ranges and sliced GGUF packages. |
| LLMLAB | distributed | Job execution documented; native LLM layer-worker qualification not established here. | Request/task distribution; single-model RAM pooling not established. |
| Ollama Cluster fork | distributed | Not established. | Yes: layer splitting; tensor mode under explicit constraints. |
| GPUStack | serving | Not established. | Backend-dependent multi-GPU/multi-node placement. |
| MLC LLM | runtime | Yes: on-device inference. | Local model execution; a distributed phone RAM pool is not documented. |
| WebLLM | runtime | Conditional browser-local compute. | No distributed model-memory pool documented. |
| MNN / MNN-LLM | runtime | Yes: on-device CPU/GPU/backend-dependent acceleration. | Local optimization; no phone-fleet weight sharding documented. |
| mllm | runtime | Yes: CPU/GPU/NPU according to device/model support. | On-device optimization; no multi-phone RAM pooling documented. |
| KTransformers | runtime | Not established. | Extends local accelerator capacity using CPU memory; not phone RAM aggregation. |
| PowerInfer | runtime | Not established. | CPU/GPU memory cooperation on one machine. |
| AirLLM | runtime | Not established. | Runs models larger than VRAM through local streaming; does not pool phones. |
| ExecuTorch | runtime | Yes: on-device inference. | Graph partitioning across local accelerators, not automatically across phones. |
| LiteRT-LM | runtime | Yes: on-device inference. | No distributed phone memory pool documented. |
| Google AI Edge Gallery | mobile | Yes: local model execution. | No model sharding across phones documented. |
| Cactus | runtime | Yes: local inference. | No phone-fleet weight pooling established. |
| GenieX / formerly Nexa SDK repository | runtime | Yes: supported CPU/Adreno GPU/Hexagon NPU. | No distributed phone memory pool documented. |
| InferrLM | mobile | Yes: complete local model execution. | Whole-model local serving; no cross-device sharding documented. |
| PocketPal AI | mobile | Yes: on-device inference. | No distributed model sharding documented. |
| Pocket LLM for Android | mobile | Yes: whole-model execution. | No cross-device layer pooling documented. |
| MobileCore / TuiMa 推嘛 | mobile | Android local inference; iOS readiness must be qualified separately. | No distributed model-memory pool documented. |
| MLX / distributed collectives | runtime | Requires an application integration. | Possible through model-parallel applications, not an automatic shared RAM pool. |
| ncnn | runtime | Yes: local inference library. | No multi-phone model-memory pooling documented. |
| ONNX Runtime GenAI | runtime | Android local inference with supported providers/models. | Local providers; no phone-cluster sharding documented. |
| MindSpore / Lite ecosystem | runtime | Local neural inference runtime; complete LLM fleet-worker qualification is separate. | Distributed framework features do not establish phone RAM pooling. |
| T-MAC | runtime | Android/local CPU integration; related NPU work is separate. | Quantization/kernel efficiency, not multi-phone pooling. |
| FastDeploy | serving | Not established. | Multi-accelerator/disaggregated serving, backend-dependent. |
| Ollama (upstream) | baseline | Not established. | Local multi-accelerator offload; a stock mobile RAM-pooling feature is not established. |
| vLLM | serving | Not established. | Yes: model parallelism on supported cluster backends. |
| SGLang | serving | Not established. | Yes on supported model-parallel deployments. |
| TensorRT-LLM | serving | Not established. | Yes: multi-GPU/node parallelism. |
| LM Studio / LM Link / Locally | baseline | LM Link example uses phone as client; local app features are a different execution path. | Remote whole-model access; cross-phone weight pooling not documented. |
| LinguaLinked | research | Yes: model partitions. | Yes: model partitioning across trusted devices. |
| EdgeShard | research | Edge compute demonstrated; native phone application not established. | Yes: distributed model shards. |
| PowerInfer-2 | research | Yes: local heterogeneous CPU/NPU inference. | Exceeds phone RAM using storage/sparsity; no multi-phone RAM pool. |
| WISP | research | Edge drafting studied; native Android/iOS product not established. | Draft distribution, not target-weight pooling. |
| FlexSpec | research | Edge-device evaluation; distinguish simulated hardware cases. | No distributed target-weight RAM pool. |
| DiP-SD | research | Modeled client drafting; physical phone cluster not demonstrated by these experiments. | Distributed drafts; target remains at verifier. |
| Speculation at a Distance | research | Not an application. | No implementation of a RAM pool. |
| PipeInfer | research | Native Android/iOS worker qualification not established. | Pipeline partitions and speculation; deployment-specific memory placement. |
| PipeSpec | research | Native phone deployment not established. | Multiple drafting/verifying models; target-weight pooling is not implied. |

## NodeLift

ID: `nodelift`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | western |
| Documented origin | Fabrizio Degni, Italy; this project. |
| Readiness | 0.2.1 experimental prerelease. |
| License | MIT; native dependencies retain their licenses. |
| Architecture | Phone drafts candidate tokens; the host verifies greedily with a pinned llama.cpp core and bounded fallback. |
| Host | macOS M3 Max measured; portable host paths require qualification. |
| Android | Native ARM64 CPU worker built; physical native drafting not yet qualified. |
| iOS | Metal/CPU companion built unsigned; physical installation pending. |
| Mobile compute | Implemented draft worker; Xiaomi evidence currently covers network/protocol only. |
| Memory / capacity | No target-weight sharding or shared RAM pool in 0.2.1. |
| Single-chat latency | 60 frozen local runs: paired median speedup 0.425–0.719×; all 48 output pairs matched. No physical-phone speedup. |
| Transport | Pinned TLS; prefix/epoch leases; bounded deadlines. |
| Integration | Restricted OpenAI-style gateway; LM Studio SDK handler tested, full plugin runtime pending. |
| Security / trust | Separate admin/client keys; TLS pinning; local trust boundary. No independent security certification. |
| Evidence | Real-weight controls, public raw runs, 29 native checks; TLS node emulated locally. |
| Limits | Greedy only; hybrid architectures rejected; thermal/battery/native phone trials pending. |
| Lesson for NodeLift | Keep host-only default until end-to-end benefit is measured against a strong local baseline. |
| Source revision | c7a41e25aaa6a9bea52ab27a12a652c7a5e71054 |
| Checked | 2026-10-31 |

Sources: [Release 0.2.1](https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.1); [Measurements and limitations](https://github.com/sev7enITA/NodeLift/blob/c7a41e25aaa6a9bea52ab27a12a652c7a5e71054/research/measurements/ENGINE_RESULTS.md); [Engine contract](https://github.com/sev7enITA/NodeLift/blob/c7a41e25aaa6a9bea52ab27a12a652c7a5e71054/docs/ENGINE_0_2.md)

## DistAI

ID: `distai`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source available; not independently qualified here. |
| License | MIT |
| Architecture | llama.cpp RPC layer offload plus Android workers and request scheduling. |
| Host | Desktop coordinator and llama.cpp backends. |
| Android | Native CPU worker. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Yes: model layers and independent jobs. |
| Memory / capacity | Yes: distributed layer placement. |
| Single-chat latency | Capacity and queued throughput benefits do not imply faster single-chat decoding. |
| Transport | LAN/Wi-Fi; wired/USB paths documented. |
| Integration | Host orchestration over llama.cpp. |
| Security / trust | Underlying RPC trust boundary needs isolation. |
| Evidence | NodeLift inspected 37 preserved source files and recalculated published benchmark data; no hardware replication. |
| Limits | Recomputed queued throughput comparison is about 1.57× against the batched baseline, not the larger sequential comparison. |
| Lesson for NodeLift | Always include a batched local baseline and actual output lengths. |
| Source revision | b1c17109498e87b3db99f8f23648d84483b68bb9 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/README.md); [NodeLift source/data recalculation](https://github.com/sev7enITA/NodeLift/blob/c7a41e25aaa6a9bea52ab27a12a652c7a5e71054/research/distai/LESSONS_LEARNED.md)

## PhoneBorg

ID: `phoneborg`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Public proof of concept with physical-phone and emulation evidence. |
| License | Apache-2.0 |
| Architecture | USB Android fleet: whole-request pools plus BigBrain layer splitting through llama.cpp RPC. |
| Host | Linux/macOS host with ADB. |
| Android | ARM64 phones, native llama.cpp agents. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Yes: independent inference and BigBrain shards. |
| Memory / capacity | Yes: BigBrain model partitioning. |
| Single-chat latency | Author tables show extra phones can reduce decode speed; capacity is the primary sharding benefit. |
| Transport | ADB over USB; host-managed endpoints. |
| Integration | OpenAI/Ollama-compatible API; fleet UI and monitoring. |
| Security / trust | No TLS documented; gateway API keys are optional, admin tokens supported, node protocol unauthenticated in v0. |
| Evidence | Author-reported five-phone tests; freeze/failover drills also use redroid emulation. |
| Limits | Emulated reliability drills are not physical thermal endurance tests; no iOS worker documented. |
| Lesson for NodeLift | Separate routing throughput, model capacity and thermal-aware phone placement. |
| Source revision | 912b24009dd0f15a5512335ef18f639b29cbdc37 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/dzaczek/phoneborg/blob/912b24009dd0f15a5512335ef18f639b29cbdc37/README.md); [Security surfaces at inspected revision](https://github.com/dzaczek/phoneborg/blob/912b24009dd0f15a5512335ef18f639b29cbdc37/docs/ARCHITECTURE.md#security-model)

## InferRing

ID: `infer-ring`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source and App Store application. |
| License | MIT |
| Architecture | MLX pipeline/tensor parallel inference across Apple devices. |
| Host | macOS. |
| Android | No Android implementation documented. |
| iOS | Native iPhone/iPad application. |
| Mobile compute | Yes: Apple-device model execution. |
| Memory / capacity | Yes: memory distributed across devices. |
| Single-chat latency | Author Mac+iPhone examples show improved prefill but slower generation than the Mac alone. |
| Transport | Automatic discovery; Wi-Fi and wired links, wired preferred. |
| Integration | App-oriented workflow; external API contract not established here. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Author-reported M1 Pro + iPhone 17 Pro comparisons. |
| Limits | Apple ecosystem; hardware/kernel and OS requirements apply. |
| Lesson for NodeLift | Report prefill and decode separately; mixed Apple clusters already exist. |
| Source revision | 7c13825fa25de346208d039d4ca1e8fecbb9860b |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/N1k1tung/infer-ring/blob/7c13825fa25de346208d039d4ca1e8fecbb9860b/README.md)

## Pooled / formerly SwarmLLM

ID: `pooled`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Rapidly evolving browser research implementation. |
| License | MIT |
| Architecture | WebGPU/WGSL distributed layers over WebRTC; MoE expert streaming and speculative experiments. |
| Host | Browser host; Chrome on macOS documented. |
| Android | Compute depends on WebGPU/browser capability; otherwise guest client. |
| iOS | Safari iPhone shard worker demonstrated upstream. |
| Mobile compute | Yes on capable browsers; ask-only guests do not contribute compute. |
| Memory / capacity | Yes: distributed layers and storage-backed expert loading. |
| Single-chat latency | Author device demos and synthetic link-delay trials; no shared benchmark with NodeLift. |
| Transport | WebRTC; optional local API bridge. |
| Integration | Bridge supports OpenAI/Responses/Anthropic interfaces. |
| Security / trust | Room peers can see conversation data; optional bridge token. Peer trust remains necessary. |
| Evidence | Physical Mac/iPhone demonstrations plus same-GPU loopback network simulations, explicitly distinct. |
| Limits | Browser memory limits and Safari host instability; network simulations omit some loss/jitter conditions. |
| Lesson for NodeLift | Zero-install participation is valuable; distinguish browser compatibility from real worker capacity. |
| Source revision | 6b4a24f73cce7ef9a9e3ab35b9a0d4c09b51dfff |
| Checked | 2026-10-31 |

Sources: [Pinned upstream](https://github.com/Nehanth/pooled/blob/6b4a24f73cce7ef9a9e3ab35b9a0d4c09b51dfff/README.md); [Older SwarmLLM fork, not an independent engine](https://github.com/Pendia/SwarmLLM-P2P-AI/tree/a0a09aa46b8ad6100fade3b5a0ab4463097fb99e)

## Silica Cluster

ID: `silica-cluster-decentralized-mobile-ai`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Experimental Android cluster. |
| License | README declares AGPL-3.0; pinned LICENSE file is empty. Terms need clarification. |
| Architecture | Android main/worker apps distribute model layers. |
| Host | Android coordinator. |
| Android | Native main and worker roles. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Yes: pipeline shards. |
| Memory / capacity | Yes: documented layer allocation. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Wi-Fi/LAN RPC. |
| Integration | App-managed inference. |
| Security / trust | README explicitly says RPC is unencrypted; trusted LAN only. |
| Evidence | Upstream documentation only; not reproduced by NodeLift. |
| Limits | License inconsistency and no replicated hardware benchmark in this assessment. |
| Lesson for NodeLift | Pair fleet UX with authenticated transport and unambiguous licensing. |
| Source revision | 7f493b04e1701c4587b945888088d9f5c9b25553 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/ShintoChakkiath/Silica-Cluster-Decentralized-Mobile-AI/blob/7f493b04e1701c4587b945888088d9f5c9b25553/README.md); [License at inspected revision](https://github.com/ShintoChakkiath/Silica-Cluster-Decentralized-Mobile-AI/blob/7f493b04e1701c4587b945888088d9f5c9b25553/LICENSE)

## prima.cpp

ID: `prima-cpp`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | international |
| Documented origin | Paper collaboration includes China/Hong Kong, UAE and Australia. |
| Readiness | Research implementation and paper. |
| License | MIT |
| Architecture | Pipelined ring, prefetch and heterogeneous resource scheduling. |
| Host | Linux/macOS; CPU and CUDA documented. |
| Android | Termux-based worker path. |
| iOS | No iOS worker documented. |
| Mobile compute | Android and compatible Termux environments. |
| Memory / capacity | Yes: model placement across heterogeneous memory/storage. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Network ring; bandwidth-aware placement. |
| Integration | Server/chat and cancellation interfaces. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Paper reports a heterogeneous physical home-cluster testbed. |
| Limits | HarmonyOS via Termux is not HarmonyOS NEXT support; current README lists Vulkan/Windows as future work. |
| Lesson for NodeLift | Skip unhelpful devices and account for disk prefetch, not RAM alone. |
| Source revision | 288df6a2cc2120387e12d6f40798f30cc525c9ea |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/OpenCPIL/prima.cpp/blob/288df6a2cc2120387e12d6f40798f30cc525c9ea/README.md); [Paper and affiliations](https://arxiv.org/html/2504.08791v3)

## exo

ID: `exo`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | international |
| Documented origin | Open distributed-inference community; no single-country classification. |
| Readiness | Source available; not independently qualified here. |
| License | Apache-2.0 |
| Architecture | Topology-aware distributed MLX execution; pipeline/tensor parallel paths. |
| Host | Apple Silicon is the tested Tier 1 in the support document. |
| Android | Current qualified worker support not documented. |
| iOS | Current qualified worker support not documented. |
| Mobile compute | Not established for the current codebase. |
| Memory / capacity | Yes: supported cluster model sharding. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Network links; Thunderbolt 5 RDMA on qualifying Macs. |
| Integration | Model serving and cluster application. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Upstream multi-Mac examples; no phone replication here. |
| Limits | README advertises Linux, while the pinned platform tier document lists Linux as planned; archived predecessor claims are separate. |
| Lesson for NodeLift | Use exact version/platform tiers; wired Mac RDMA results do not transfer to phone Wi-Fi. |
| Source revision | 871caad407a70647426dffaa455bd4d0ab1d48e6 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/exo-explore/exo/blob/871caad407a70647426dffaa455bd4d0ab1d48e6/README.md); [Pinned support tiers (README discrepancy)](https://github.com/exo-explore/exo/blob/871caad407a70647426dffaa455bd4d0ab1d48e6/PLATFORMS.md)

## distributed-llama

ID: `distributed-llama`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source available; not independently qualified here. |
| License | MIT |
| Architecture | CPU-focused tensor parallelism across networked machines. |
| Host | ARM/x86 desktop and SBC environments. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Android/iOS companion qualification not established. |
| Memory / capacity | Yes: model weights distributed across nodes. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | TCP/Ethernet-oriented cluster. |
| Integration | CLI and server tools. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Upstream configurations and benchmark examples. |
| Limits | Documented node counts and KV-head constraints restrict topology; formats/backends vary. |
| Lesson for NodeLift | Topology and collective-communication constraints belong in the planner. |
| Source revision | c618cd7e9ebdae235c55d13125ae774b3d1b7b83 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/b4rtaz/distributed-llama/blob/c618cd7e9ebdae235c55d13125ae774b3d1b7b83/README.md)

## llama.cpp / RPC

ID: `llama-cpp`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | international |
| Documented origin | International ggml/llama.cpp community. |
| Readiness | Widely used local runtime; RPC explicitly experimental. |
| License | MIT |
| Architecture | Quantized native inference with optional remote GGML devices and layer/tensor splitting. |
| Host | CPU, Metal, CUDA and other backend-dependent platforms. |
| Android | Local runtime supported; no complete fleet companion implied. |
| iOS | Local runtime integration supported; fleet lifecycle is external. |
| Mobile compute | Possible through native integration; mobile fleet qualification is separate. |
| Memory / capacity | Yes through RPC/offload on supported backends. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | TCP; current RPC also documents RDMA. |
| Integration | Native C API, CLI and OpenAI-style server. |
| Security / trust | RPC README explicitly calls it insecure/fragile and unsuitable for exposed or sensitive networks. |
| Evidence | NodeLift built a pinned upstream and measured local controls; no RPC phone comparison. |
| Limits | A low-level remote backend does not provide safe mobile pairing or OS lifecycle management. |
| Lesson for NodeLift | Reuse kernels; add authenticated leases, provenance and mobile recovery above them. |
| Source revision | ddf48f85c933c1f438212a02eb21e7b001d2d37d |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/ggml-org/llama.cpp/blob/ddf48f85c933c1f438212a02eb21e7b001d2d37d/README.md); [RPC security and transport](https://github.com/ggml-org/llama.cpp/blob/ddf48f85c933c1f438212a02eb21e7b001d2d37d/tools/rpc/README.md)

## Petals

ID: `petals`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | international |
| Documented origin | BigScience collaborative research. |
| Readiness | Research software; inspected repository last pushed in 2024. |
| License | MIT |
| Architecture | Transformer blocks hosted by a distributed swarm, with inference and fine-tuning. |
| Host | GPU servers and supported desktop clients. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Yes: model blocks distributed across peers. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Internet/private swarm networking. |
| Integration | Transformers-style Python API. |
| Security / trust | Public-swarm peers process user data; private trusted swarm recommended for sensitive workloads. |
| Evidence | Published research and upstream large-model experiments. |
| Limits | Public swarm availability is not guaranteed; no native smartphone fleet documented. |
| Lesson for NodeLift | Resilient peer discovery helps capacity, but peer trust is not solved by distribution. |
| Source revision | 22afba627a7eb4fcfe9418c49472c6a51334b8ac |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/bigscience-workshop/petals/blob/22afba627a7eb4fcfe9418c49472c6a51334b8ac/README.md)

## LocalAI

ID: `localai`

| Criterion | Assessment |
|---|---|
| Category | serving |
| Ecosystem | international |
| Documented origin | Open-source LocalAI community. |
| Readiness | Versioned multi-backend serving platform. |
| License | MIT |
| Architecture | Request routing plus backend-specific distributed inference, including MLX/layer-split paths. |
| Host | Linux/macOS and supported container backends. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Backend-dependent sharding, distinct from replica routing. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | P2P/cluster transports; NATS TLS/mTLS paths documented. |
| Integration | OpenAI-compatible multimodal serving. |
| Security / trust | API keys, OIDC/roles/quotas and deny-by-default authentication documented. |
| Evidence | Current source/release documentation, not replicated here. |
| Limits | Distributed modes differ by backend; mobile worker qualification not established. |
| Lesson for NodeLift | Expose model residency, replica routing and sharding as different capabilities. |
| Source revision | 832dff3c7448a4fdb0302a9af9feca1a844553c5 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/mudler/LocalAI/blob/832dff3c7448a4fdb0302a9af9feca1a844553c5/README.md)

## mycellm

ID: `mycellm`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source available; not independently qualified here. |
| License | Apache-2.0 |
| Architecture | P2P network routes requests to model-serving peers; native iOS peer exists. |
| Host | Metal/CUDA/ROCm/CPU with multiple local backends. |
| Android | Not documented in the reviewed sources. |
| iOS | Native MLX/Metal peer can serve local models. |
| Mobile compute | Yes for the documented iOS peer. |
| Memory / capacity | Whole-model peer serving documented; cross-phone layer pooling not established. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | QUIC, relay/NAT traversal and discovery. |
| Integration | OpenAI-style serving and mesh tooling. |
| Security / trust | Signed receipts and admin/auth controls; peer trust still requires review. |
| Evidence | Source and author device reports; not replicated here. |
| Limits | Aggregating available providers is not proof of pooling model memory. |
| Lesson for NodeLift | Separate federated service capacity from one model spanning devices. |
| Source revision | 2465f52c86e91b9237ce9fb3a27b8691e82ceab6 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/mycellm/mycellm/blob/2465f52c86e91b9237ce9fb3a27b8691e82ceab6/README.md)

## Mesh LLM

ID: `mesh-llm`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source available; not independently qualified here. |
| License | Apache-2.0 |
| Architecture | Private meshes, request routing and package-backed contiguous layer stages. |
| Host | Linux, Windows, macOS with CPU/GPU-specific releases. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Yes: documented stage splits for supported dense models. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Peer mesh and invitation-based joining. |
| Integration | OpenAI client integration; explicit model selection recommended. |
| Security / trust | Invite tokens documented; external security audit not established. |
| Evidence | Current README and release caveats. |
| Limits | Some native loading/distribution paths carry open release-specific blockers; no phone worker documented. |
| Lesson for NodeLift | Model packages and supported execution paths need explicit readiness metadata. |
| Source revision | 6820aa4d44aea55325067dbd414c60440959366d |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/Mesh-LLM/mesh-llm/blob/6820aa4d44aea55325067dbd414c60440959366d/README.md)

## Cake

ID: `cake`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source available; not independently qualified here. |
| License | Custom FAIR 1.0.0; business/commercial conditions apply. See full LICENSE. |
| Architecture | Rust multimodal server shards transformer blocks across heterogeneous devices. |
| Host | Linux/macOS/Windows; CPU, CUDA, Metal and Vulkan paths. |
| Android | Documented native platform. |
| iOS | Documented native platform. |
| Mobile compute | Yes, documented mobile worker integration. |
| Memory / capacity | Yes: layer sharding with weight delivery/caching. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | mDNS discovery; cluster key; compressed weight transfer. |
| Integration | Inference server and cluster tooling. |
| Security / trust | Cluster key documented; checksum integrity is not itself transport confidentiality. |
| Evidence | Current source/platform documentation; no common-hardware replication. |
| Limits | Nonstandard license and platform/model-specific qualification require review. |
| Lesson for NodeLift | Automatic shard delivery and cross-platform workers are existing prior art. |
| Source revision | be522af17a4a4da3e1113682ba39689c634d513f |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/evilsocket/cake/blob/be522af17a4a4da3e1113682ba39689c634d513f/README.md); [License at inspected revision](https://github.com/evilsocket/cake/blob/be522af17a4a4da3e1113682ba39689c634d513f/LICENSE)

## Nakshatra

ID: `nakshatra`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Active experimental system; GitHub lineage is a Petals fork. |
| License | MIT |
| Architecture | Current design uses patched llama.cpp layer slices and a gRPC chain. |
| Host | Heterogeneous desktop CPU, Metal, CUDA and ROCm. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Yes: contiguous layer ranges and sliced GGUF packages. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | gRPC chain; discovery, relay and federation mechanisms. |
| Integration | Gateway and worker protocol. |
| Security / trust | Signed discovery/receipts and encrypted relay paths documented. |
| Evidence | Author experience report and implementation documentation. |
| Limits | GPU output may be reproducible in distribution, not byte-identical; mobile qualification absent. |
| Lesson for NodeLift | Track code lineage without mistaking a substantially changed architecture for an unchanged fork. |
| Source revision | dcf7cdd688bc466f119fc70959eba4c5e0fdbccd |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/fthrvi/nakshatra/blob/dcf7cdd688bc466f119fc70959eba4c5e0fdbccd/README.md)

## LLMLAB

ID: `local-distributed-llm-lab`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source available; not independently qualified here. |
| License | README claims MIT; linked root LICENSE was not retrievable at the pinned revision. |
| Architecture | Ray/LangGraph task orchestration over Ollama/LM Studio and optional Android jobs. |
| Host | Mac/PC/Linux coordinator. |
| Android | Kotlin worker accepts WebSocket execute_task jobs. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Job execution documented; native LLM layer-worker qualification not established here. |
| Memory / capacity | Request/task distribution; single-model RAM pooling not established. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | WebSocket Android worker and service APIs. |
| Integration | Ollama/LM Studio backend integration. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Source/status documentation; not replicated here. |
| Limits | A connected task worker is not evidence of transformer-layer execution. |
| Lesson for NodeLift | Record the actual worker operation, not only its connected state. |
| Source revision | 70c1ea8f210151fb199c8291f8248fd5d16f261d |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/xdutsuay/local-distributed-llm-lab/blob/70c1ea8f210151fb199c8291f8248fd5d16f261d/README.md)

## Ollama Cluster fork

ID: `ollama-cluster`

| Criterion | Assessment |
|---|---|
| Category | distributed |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Unofficial Ollama fork, branch cluster. |
| License | MIT |
| Architecture | Ollama policies drive llama.cpp RPC layer/tensor splitting. |
| Host | Two matching NVIDIA DGX Spark systems tested upstream. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Yes: layer splitting; tensor mode under explicit constraints. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | 200 Gb/s direct RDMA tested; LAN requires an override. |
| Integration | Ollama API plus cluster management commands. |
| Security / trust | RPC/status lack authentication; direct link and firewall isolation documented. |
| Evidence | Author warm-run tables disclose different loads and benchmark versions. |
| Limits | Not stock Ollama and not a mobile plugin; some comparisons have concurrent traffic. |
| Lesson for NodeLift | Never describe an unofficial fork as built-in upstream support. |
| Source revision | 26675f60867c62acb323953b9e5b59205315db61 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/shadoq/ollama-cluster/blob/26675f60867c62acb323953b9e5b59205315db61/README.md)

## GPUStack

ID: `gpustack`

| Criterion | Assessment |
|---|---|
| Category | serving |
| Ecosystem | international |
| Documented origin | GPUStack project community; a single national origin is not established here. |
| Readiness | Versioned GPU serving/control platform. |
| License | Apache-2.0 |
| Architecture | Cluster scheduling, backend placement and load balancing. |
| Host | Current worker documentation: Linux; macOS is not a supported worker. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Backend-dependent multi-GPU/multi-node placement. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Datacenter/cluster networking. |
| Integration | Standard model-service APIs and management UI. |
| Security / trust | Authentication, access control and usage metering documented. |
| Evidence | Upstream performance lab and auto-tuning facilities; not reproduced here. |
| Limits | Older desktop/Apple support descriptions must not be applied to current workers. |
| Lesson for NodeLift | Benchmark concurrency against service objectives; preserve version-specific platform support. |
| Source revision | 6e3a42a9d3d59eb6f11407ed5cb96d5840c3f48e |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/gpustack/gpustack/blob/6e3a42a9d3d59eb6f11407ed5cb96d5840c3f48e/README.md)

## MLC LLM

ID: `mlc-llm`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | international |
| Documented origin | MLC/Apache TVM ecosystem. |
| Readiness | Compiler/runtime with native mobile examples. |
| License | Apache-2.0 |
| Architecture | Compiles models into hardware-specific native execution libraries. |
| Host | Desktop CPU/GPU platforms depend on target build. |
| Android | Vulkan/mobile native integration. |
| iOS | Metal native integration. |
| Mobile compute | Yes: on-device inference. |
| Memory / capacity | Local model execution; a distributed phone RAM pool is not documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local execution; service interfaces optional. |
| Integration | OpenAI-style interfaces across native/server bindings. |
| Security / trust | Application owns network/pairing policy. |
| Evidence | Upstream documentation only; not reproduced by NodeLift. |
| Limits | Compiled artifacts and target support must match model/device. |
| Lesson for NodeLift | A mobile backend can improve draft speed without supplying a fleet scheduler. |
| Source revision | 44fd06d04f22c87820e205b0f2b2e5e6a1f6ca85 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/mlc-ai/mlc-llm/blob/44fd06d04f22c87820e205b0f2b2e5e6a1f6ca85/README.md)

## WebLLM

ID: `web-llm`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | international |
| Documented origin | MLC ecosystem. |
| Readiness | Source available; not independently qualified here. |
| License | Apache-2.0 |
| Architecture | Browser-local inference using WebGPU and WebAssembly. |
| Host | Compatible browser. |
| Android | Browser/device WebGPU support required. |
| iOS | Browser/device WebGPU support required; no universal device guarantee. |
| Mobile compute | Conditional browser-local compute. |
| Memory / capacity | No distributed model-memory pool documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Inference stays in browser after model loading. |
| Integration | OpenAI-compatible JavaScript API; workers/extensions. |
| Security / trust | Application permissions and model-download provenance remain relevant. |
| Evidence | Upstream documentation only; not reproduced by NodeLift. |
| Limits | Browser memory and GPU limits; a Web Worker is not another physical device. |
| Lesson for NodeLift | Do not confuse browser worker threads with distributed hardware nodes. |
| Source revision | 6897fadc2bed9a5a7940265dd80220f83ca184e7 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/mlc-ai/web-llm/blob/6897fadc2bed9a5a7940265dd80220f83ca184e7/README.md)

## MNN / MNN-LLM

ID: `mnn`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | asia |
| Documented origin | Alibaba, China. |
| Readiness | Mobile runtime with Android and iOS applications. |
| License | Apache-2.0 |
| Architecture | Optimized local neural-network/LLM execution and multimodal pipelines. |
| Host | Mobile, desktop and embedded targets. |
| Android | MNN Chat and native runtime. |
| iOS | MNN LLM iOS app and runtime. |
| Mobile compute | Yes: on-device CPU/GPU/backend-dependent acceleration. |
| Memory / capacity | Local optimization; no phone-fleet weight sharding documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local inference; app integrations vary. |
| Integration | Native runtime and LLM app APIs. |
| Security / trust | Local inference does not automatically establish application-wide privacy. |
| Evidence | Official source and app releases; NodeLift has not benchmarked it. |
| Limits | Model conversion, operators and backend support need per-device qualification. |
| Lesson for NodeLift | Evaluate as an Android draft backend with identical tokenizer/output contracts. |
| Source revision | 17236ad20b4798a1faccc761c80f283283bec30e |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/alibaba/MNN/blob/17236ad20b4798a1faccc761c80f283283bec30e/README.md)

## mllm

ID: `mllm`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Active mobile/edge research runtime. |
| License | MIT |
| Architecture | ARM CPU/OpenCL GPU/QNN and Ascend NPU paths, quantization and graph compilation. |
| Host | Android and documented desktop/edge builds. |
| Android | Native app with an on-device Go server. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Yes: CPU/GPU/NPU according to device/model support. |
| Memory / capacity | On-device optimization; no multi-phone RAM pooling documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | App-local client/server architecture. |
| Integration | C++/Python tooling and Android service. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Upstream device support matrix and separate Jetson benchmarks. |
| Limits | Jetson prefill multipliers are not phone decode results; iOS qualification not established. |
| Lesson for NodeLift | Measure NPU compilation and synchronization costs before choosing it for drafting. |
| Source revision | 1d3c3d8e506e3d12e902af82866972623b240ce0 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/UbiquitousLearning/mllm/blob/1d3c3d8e506e3d12e902af82866972623b240ce0/README.md)

## KTransformers

ID: `ktransformers`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | asia |
| Documented origin | MADSys/Tsinghua University, China, with collaborators. |
| Readiness | Source available; not independently qualified here. |
| License | Apache-2.0 |
| Architecture | Heterogeneous CPU/GPU or CPU/NPU execution, especially MoE expert offload. |
| Host | Consumer/server systems with substantial host RAM and supported accelerators. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Extends local accelerator capacity using CPU memory; not phone RAM aggregation. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local CPU/accelerator data paths. |
| Integration | Inference/server and optimization interfaces. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Official model tutorials and author benchmarks. |
| Limits | Model-specific kernels and CPU bandwidth determine feasibility; no Android/iOS fleet. |
| Lesson for NodeLift | Compare phone offload against optimized local expert offload. |
| Source revision | c9873312643b615a717832946fba0346e69ab035 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/kvcache-ai/ktransformers/blob/c9873312643b615a717832946fba0346e69ab035/README.md)

## PowerInfer

ID: `powerinfer`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | asia |
| Documented origin | Originated at SJTU IPADS, China; repository now Tiiny-AI. |
| Readiness | Source available; not independently qualified here. |
| License | MIT |
| Architecture | Activation-locality/sparse CPU-GPU execution; related SmallThinker models. |
| Host | Consumer GPU systems; backend-specific support. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | CPU/GPU memory cooperation on one machine. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local memory/accelerator transfers. |
| Integration | Modified native runtime. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Author experiments on specific sparse/ReLU models. |
| Limits | Headline speedups depend on model sparsity and baseline; PowerInfer-2 smartphone paper is a separate row. |
| Lesson for NodeLift | Compare quality and architecture as well as speed when using specialized sparse models. |
| Source revision | 8bd56d69906c9d2dba4d3bf6899763401e01a9a4 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/Tiiny-AI/PowerInfer/blob/8bd56d69906c9d2dba4d3bf6899763401e01a9a4/README.md)

## AirLLM

ID: `airllm`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source available; not independently qualified here. |
| License | Apache-2.0 |
| Architecture | Layer/expert streaming from host/storage to reduce accelerator memory. |
| Host | Python desktop/server, CUDA and documented macOS/CPU paths. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Runs models larger than VRAM through local streaming; does not pool phones. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local RAM/storage I/O. |
| Integration | Python AutoModel-style API. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Author VRAM measurements and examples. |
| Limits | Low peak VRAM is not low total RAM/disk cost or interactive speed. |
| Lesson for NodeLift | Publish wall time, disk traffic and host memory alongside VRAM reductions. |
| Source revision | 75a6bb3c41c6b4b5869fc7fe20828aa6367f9c46 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/lyogavin/airllm/blob/75a6bb3c41c6b4b5869fc7fe20828aa6367f9c46/README.md)

## ExecuTorch

ID: `executorch`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | international |
| Documented origin | PyTorch/Meta-led ecosystem with Arm, Qualcomm, Apple, MediaTek and other contributors. |
| Readiness | Versioned edge runtime with mobile packages. |
| License | BSD-style license; component notices apply. |
| Architecture | Exported graphs delegate supported regions to CPU/GPU/NPU/DSP. |
| Host | Phones, desktops and embedded targets. |
| Android | AAR; CPU/Vulkan and model-dependent mobile accelerator delegates. |
| iOS | CPU/Core ML; MLX on physical devices marked experimental. |
| Mobile compute | Yes: on-device inference. |
| Memory / capacity | Graph partitioning across local accelerators, not automatically across phones. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local runtime; application transport separate. |
| Integration | Native/mobile bindings; experimental local OpenAI-style server. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Official examples and backend documentation. |
| Limits | Export/delegate/operator coverage varies by model and device. |
| Lesson for NodeLift | Treat local hardware delegation and network partitioning as distinct layers. |
| Source revision | 05092c126d4ed5563527f0dab57f3c5da1a7f2a7 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/pytorch/executorch/blob/05092c126d4ed5563527f0dab57f3c5da1a7f2a7/README.md); [License at inspected revision](https://github.com/pytorch/executorch/blob/05092c126d4ed5563527f0dab57f3c5da1a7f2a7/LICENSE)

## LiteRT-LM

ID: `litert-lm`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | western |
| Documented origin | Google, United States; international contributors. |
| Readiness | Versioned LLM orchestration/runtime SDK. |
| License | Apache-2.0 |
| Architecture | LiteRT-based local LLM execution, quantization and model-dependent MTP. |
| Host | Desktop/mobile targets with backend-specific support. |
| Android | Kotlin SDK marked stable in the inspected README. |
| iOS | Swift SDK for iOS/macOS marked early preview, not stable. |
| Mobile compute | Yes: on-device inference. |
| Memory / capacity | No distributed phone memory pool documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local execution. |
| Integration | C/native/mobile and web interfaces. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Official SDK documentation and examples. |
| Limits | LiteRT model conversion and hardware delegates determine availability. |
| Lesson for NodeLift | Benchmark supported native formats against GGUF before adopting a backend. |
| Source revision | 9d613ac5bb59a142c586f50821c43f1c2d001920 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/google-ai-edge/LiteRT-LM/blob/9d613ac5bb59a142c586f50821c43f1c2d001920/README.md)

## Google AI Edge Gallery

ID: `gallery`

| Criterion | Assessment |
|---|---|
| Category | mobile |
| Ecosystem | western |
| Documented origin | Google, United States. |
| Readiness | Experimental beta app; Android/iOS distribution documented. |
| License | Apache-2.0 |
| Architecture | Local multimodal app built on edge inference runtimes. |
| Host | Phone app; macOS download also documented. |
| Android | Android 12+ documented. |
| iOS | iOS 17+ documented. |
| Mobile compute | Yes: local model execution. |
| Memory / capacity | No model sharding across phones documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | On-device inference after downloads. |
| Integration | App-oriented model management and benchmark UI. |
| Security / trust | Offline inference advertised; this is not an independent privacy audit. |
| Evidence | Official app/source documentation. |
| Limits | A local benchmark sandbox does not provide a reusable cluster worker. |
| Lesson for NodeLift | Make device-level model management and measurements understandable. |
| Source revision | 7f4d6bc7062bfc2b8db6940fd022884353c79354 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/google-ai-edge/gallery/blob/7f4d6bc7062bfc2b8db6940fd022884353c79354/README.md)

## Cactus

ID: `cactus`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source available; not independently qualified here. |
| License | Custom Cactus license; eligibility/commercial conditions apply. Inspect LICENSE. |
| Architecture | Mobile/wearable inference engine with local and hybrid edge/cloud paths. |
| Host | Apple/Android and supported native targets. |
| Android | Native engine and connected-device benchmarks. |
| iOS | Native engine and connected-device benchmarks. |
| Mobile compute | Yes: local inference. |
| Memory / capacity | No phone-fleet weight pooling established. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local and optional cloud integration. |
| Integration | Native engine/application interfaces. |
| Security / trust | Cloud telemetry is opt-in in documented tools; app policies remain relevant. |
| Evidence | Author benchmark suite; not reproduced by NodeLift. |
| Limits | Custom license and engine-specific model formats; hybrid cloud is not local-only clustering. |
| Lesson for NodeLift | Include sustained mobile benchmarks and explicit telemetry controls. |
| Source revision | 2cfcdb8568eb9192323b27fd0012a834517b4419 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/cactus-compute/cactus/blob/2cfcdb8568eb9192323b27fd0012a834517b4419/README.md); [License at inspected revision](https://github.com/cactus-compute/cactus/blob/2cfcdb8568eb9192323b27fd0012a834517b4419/LICENSE)

## GenieX / formerly Nexa SDK repository

ID: `geniex`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | western |
| Documented origin | Qualcomm, United States. |
| Readiness | Current canonical repository; old NexaAI/nexa-sdk URL redirects here. |
| License | BSD-3-Clause |
| Architecture | Snapdragon local inference through llama.cpp or Qualcomm AI Engine Direct. |
| Host | Qualcomm Snapdragon Windows/Android/Linux only, per current README. |
| Android | Kotlin/Java SDK, supported Snapdragon devices. |
| iOS | Not a documented target. |
| Mobile compute | Yes: supported CPU/Adreno GPU/Hexagon NPU. |
| Memory / capacity | No distributed phone memory pool documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local execution; optional local server. |
| Integration | C SDK, CLI, Python, Kotlin/Java and OpenAI-compatible server. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Official SDK examples and hardware matrix. |
| Limits | Do not carry historical Nexa cross-platform claims onto the renamed current project. |
| Lesson for NodeLift | Detect exact chipset/runtime/model path; generic NPU availability is insufficient. |
| Source revision | d66de04d57ee41db2b1df3b9b85b926e41d1c4e5 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/qualcomm/GenieX/blob/d66de04d57ee41db2b1df3b9b85b926e41d1c4e5/README.md)

## InferrLM

ID: `inferrlm`

| Criterion | Assessment |
|---|---|
| Category | mobile |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source available; not independently qualified here. |
| License | AGPL-3.0 |
| Architecture | Local GGUF/MLX mobile app with optional cloud providers and local serving. |
| Host | Android/iOS app. |
| Android | llama.cpp local inference. |
| iOS | llama.cpp, MLX and supported Apple model paths. |
| Mobile compute | Yes: complete local model execution. |
| Memory / capacity | Whole-model local serving; no cross-device sharding documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local server or optional remote APIs. |
| Integration | App and local-server interfaces. |
| Security / trust | Local and cloud modes have different data boundaries. |
| Evidence | Current app/source documentation. |
| Limits | A phone serving an entire model does not add its RAM to a desktop model. |
| Lesson for NodeLift | Expose whether each request stays local, is served by a peer or goes to a cloud. |
| Source revision | 258261f7fd2e7f54e3772a6f577441de7dec26d9 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/loomax-labs/InferrLM/blob/258261f7fd2e7f54e3772a6f577441de7dec26d9/README.md)

## PocketPal AI

ID: `pocketpal-ai`

| Criterion | Assessment |
|---|---|
| Category | mobile |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source available; not independently qualified here. |
| License | MIT |
| Architecture | Local assistant using native LLM, speech and tool bridges. |
| Host | Android/iOS/iPadOS. |
| Android | CPU, supported Adreno/OpenCL and Hexagon paths. |
| iOS | CPU/Metal paths. |
| Mobile compute | Yes: on-device inference. |
| Memory / capacity | No distributed model sharding documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local app; model downloads. |
| Integration | Application/native bridges. |
| Security / trust | No-account local workflow documented; not independently audited. |
| Evidence | Store/source releases and hardware acceleration documentation. |
| Limits | Supported backends vary; no cluster planner or remote draft contract established. |
| Lesson for NodeLift | A well-integrated standalone phone is a valuable baseline for reclaimed hardware. |
| Source revision | f8f37d9a4676763eaaf509276b21631b9e95ba8f |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/a-ghorbani/pocketpal-ai/blob/f8f37d9a4676763eaaf509276b21631b9e95ba8f/README.md)

## Pocket LLM for Android

ID: `local-llms-on-android`

| Criterion | Assessment |
|---|---|
| Category | mobile |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Source available; not independently qualified here. |
| License | MIT |
| Architecture | LiteRT-based Android app and LAN model server. |
| Host | Android phone. |
| Android | Local model import, chat and server. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Yes: whole-model execution. |
| Memory / capacity | No cross-device layer pooling documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Home LAN/web UI. |
| Integration | Local server and browser chat. |
| Security / trust | Password-protected Web UI documented. |
| Evidence | Upstream APK/runtime documentation. |
| Limits | Current runtime is LiteRT-LM, not an assumed generic GGUF server. |
| Lesson for NodeLift | Simple LAN serving and password UX are useful without implying RAM aggregation. |
| Source revision | 8e0edbc99eb3930ad37536ec137d8882e8beaceb |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/dineshsoudagar/local-llms-on-android/blob/8e0edbc99eb3930ad37536ec137d8882e8beaceb/README.md)

## MobileCore / TuiMa 推嘛

ID: `mobilecore`

| Criterion | Assessment |
|---|---|
| Category | mobile |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Android prerelease and buildable iOS skeleton. |
| License | not identified |
| Architecture | GGUF runtime, device-aware model catalog and benchmark records. |
| Host | Android app; iOS skeleton. |
| Android | Native llama.cpp foreground service. |
| iOS | Buildable skeleton/bridge; full qualification not established. |
| Mobile compute | Android local inference; iOS readiness must be qualified separately. |
| Memory / capacity | No distributed model-memory pool documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Foreground localhost API. |
| Integration | OpenAI-compatible localhost routes. |
| Security / trust | Model provenance/digests and curated catalog separation documented. |
| Evidence | Upstream source/build records; not reproduced here. |
| Limits | Do not label a skeleton equivalent to a physically qualified app. |
| Lesson for NodeLift | Separate verified model provenance from unqualified community search results. |
| Source revision | 1f909373d17fc4a6413006fcd88f1c46120112cc |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/Harzva/mobilecore/blob/1f909373d17fc4a6413006fcd88f1c46120112cc/README.md)

## MLX / distributed collectives

ID: `mlx`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | western |
| Documented origin | Apple ML research, United States. |
| Readiness | Source available; not independently qualified here. |
| License | MIT |
| Architecture | Array framework with distributed collectives for parallel training/inference. |
| Host | Apple Silicon; current distributed docs also describe CUDA/NCCL. |
| Android | Not documented in the reviewed sources. |
| iOS | Swift/mobile integrations exist separately; a phone fleet is not supplied by this API. |
| Mobile compute | Requires an application integration. |
| Memory / capacity | Possible through model-parallel applications, not an automatic shared RAM pool. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | MPI, TCP ring, JACCL Thunderbolt RDMA, NCCL. |
| Integration | Python/C++ and related Swift libraries. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Pinned distributed-communication documentation. |
| Limits | Backend and OS/hardware prerequisites matter; RDMA does not apply to ordinary Wi-Fi. |
| Lesson for NodeLift | Use collectives only when measured interconnect cost fits the partition. |
| Source revision | 339279525ea3168b6fa55911529e3766a145d0b2 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/ml-explore/mlx/blob/339279525ea3168b6fa55911529e3766a145d0b2/README.md); [Distributed backends](https://github.com/ml-explore/mlx/blob/339279525ea3168b6fa55911529e3766a145d0b2/docs/src/usage/distributed.rst)

## ncnn

ID: `ncnn`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | asia |
| Documented origin | Tencent, China. |
| Readiness | Source available; not independently qualified here. |
| License | BSD-3-Clause; third-party notices apply. |
| Architecture | Optimized local neural-network inference with CPU/Vulkan paths. |
| Host | Mobile, embedded and desktop. |
| Android | Native/Termux build documentation. |
| iOS | Native build documentation. |
| Mobile compute | Yes: local inference library. |
| Memory / capacity | No multi-phone model-memory pooling documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Application-owned; runtime is local. |
| Integration | C++/Python and platform integrations. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Official builds and supported-target documentation. |
| Limits | General neural-network support is not proof every LLM architecture is supported. |
| Lesson for NodeLift | Qualify transformer operator coverage and quantization before fleet integration. |
| Source revision | f18f3ffc94dbc76a277e94556c588ab2c2d0e1d9 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/Tencent/ncnn/blob/f18f3ffc94dbc76a277e94556c588ab2c2d0e1d9/README.md); [License at inspected revision](https://github.com/Tencent/ncnn/blob/f18f3ffc94dbc76a277e94556c588ab2c2d0e1d9/LICENSE.txt)

## ONNX Runtime GenAI

ID: `onnxruntime-genai`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | western |
| Documented origin | Microsoft, United States. |
| Readiness | Source available; not independently qualified here. |
| License | MIT |
| Architecture | ONNX generation loop, KV cache, sampling and accelerator execution providers. |
| Host | Linux/Windows/macOS/Android per current support table. |
| Android | Supported target in current matrix. |
| iOS | Listed on the roadmap, not current support. |
| Mobile compute | Android local inference with supported providers/models. |
| Memory / capacity | Local providers; no phone-cluster sharding documented. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local runtime. |
| Integration | Native and language bindings. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Official current support matrix. |
| Limits | ONNX export and execution-provider coverage differ; generic ONNX iOS support is not GenAI qualification. |
| Lesson for NodeLift | Use the exact product support table, not the broader parent framework's claims. |
| Source revision | 77a7b3b7b46ff97b2a66259f04d783beda12a274 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/microsoft/onnxruntime-genai/blob/77a7b3b7b46ff97b2a66259f04d783beda12a274/README.md)

## MindSpore / Lite ecosystem

ID: `mindspore`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | asia |
| Documented origin | Huawei/MindSpore ecosystem, China. |
| Readiness | Source available; not independently qualified here. |
| License | Apache-2.0 |
| Architecture | Training/inference framework with Ascend and edge/mobile ecosystem. |
| Host | Supported server/edge hardware; Lite deployment is a distinct component. |
| Android | MindSpore Lite documents Android; a specific LLM worker is not qualified here. |
| iOS | MindSpore Lite documents iOS; a specific LLM worker is not qualified here. |
| Mobile compute | Local neural inference runtime; complete LLM fleet-worker qualification is separate. |
| Memory / capacity | Distributed framework features do not establish phone RAM pooling. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Component-dependent. |
| Integration | Framework/native APIs. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Official Lite platform page also identifies a HarmonyOS NEXT Lite Kit; no Huawei phone run performed. |
| Limits | Lite Kit availability does not establish arbitrary LLM operators, model compatibility or NodeLift support. |
| Lesson for NodeLift | Investigate the native NEXT Lite Kit route, then verify actual model execution on the target device. |
| Source revision | 16873579685a1662f10ebd1df068bf512f211869 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/mindspore-ai/mindspore/blob/16873579685a1662f10ebd1df068bf512f211869/README.md); [Official Lite platforms and HarmonyOS NEXT Kit](https://www.mindspore.cn/lite/en)

## T-MAC

ID: `t-mac`

| Criterion | Assessment |
|---|---|
| Category | runtime |
| Ecosystem | western |
| Documented origin | Microsoft project; multinational research contributors. |
| Readiness | Research kernel library; inspected head last pushed in June 2025. |
| License | MIT |
| Architecture | Lookup-table low-bit matrix multiplication, mainly for CPU inference. |
| Host | ARM/Intel Linux/macOS/Windows. |
| Android | Cross-compilation instructions. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Android/local CPU integration; related NPU work is separate. |
| Memory / capacity | Quantization/kernel efficiency, not multi-phone pooling. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local compute. |
| Integration | Kernel library and llama.cpp integration. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Author aligned model/device comparisons and Android guide. |
| Limits | Kernel or prefill gains do not establish networked decoding gains. |
| Lesson for NodeLift | Improve local draft efficiency before adding network complexity. |
| Source revision | 7042f8f73330bd083bc1e4bc5ccb3f88a4904aee |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/microsoft/T-MAC/blob/7042f8f73330bd083bc1e4bc5ccb3f88a4904aee/README.md)

## FastDeploy

ID: `fastdeploy`

| Criterion | Assessment |
|---|---|
| Category | serving |
| Ecosystem | asia |
| Documented origin | PaddlePaddle/Baidu ecosystem, China. |
| Readiness | Current 2.x LLM/VLM serving project. |
| License | Apache-2.0 |
| Architecture | Prefill/decode disaggregation, KV transfer, quantization and MTP. |
| Host | Linux servers; NVIDIA and multiple Chinese accelerator backends. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Multi-accelerator/disaggregated serving, backend-dependent. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | NVLink/RDMA and cluster networking. |
| Integration | OpenAI-style service; vLLM-compatible interfaces. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Official current Chinese/English documentation. |
| Limits | Current LLM server is not equivalent to older general mobile FastDeploy descriptions. |
| Lesson for NodeLift | Separate prefill, decode and cache-transfer placement; keep mobile claims version-specific. |
| Source revision | d923caf15e1eb0da8e2efd75b0152e65cefeeddd |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/PaddlePaddle/FastDeploy/blob/d923caf15e1eb0da8e2efd75b0152e65cefeeddd/README.md)

## Ollama (upstream)

ID: `ollama`

| Criterion | Assessment |
|---|---|
| Category | baseline |
| Ecosystem | western |
| Documented origin | Ollama company/project, United States; international contributors. |
| Readiness | Versioned local model runner. |
| License | MIT |
| Architecture | Local models and backend-dependent accelerator execution. |
| Host | macOS/Windows/Linux. |
| Android | Mobile clients do not establish an official native compute worker. |
| iOS | Mobile clients do not establish an official native compute worker. |
| Mobile compute | Not established. |
| Memory / capacity | Local multi-accelerator offload; a stock mobile RAM-pooling feature is not established. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Local HTTP service; remote clients optional. |
| Integration | Ollama API and compatible integrations. |
| Security / trust | Network exposure must be configured deliberately; client reachability is not peer authentication. |
| Evidence | Current upstream source; NodeLift is not an internal Ollama backend. |
| Limits | Unofficial Ollama Cluster fork is a separate matrix entry. |
| Lesson for NodeLift | Keep upstream, adapter and fork compatibility claims separate. |
| Source revision | f9323416f0c3f84d82f6c4a7bde75b717448bd44 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/ollama/ollama/blob/f9323416f0c3f84d82f6c4a7bde75b717448bd44/README.md)

## vLLM

ID: `vllm`

| Criterion | Assessment |
|---|---|
| Category | serving |
| Ecosystem | international |
| Documented origin | Open-source serving community with international academic/industry contributors. |
| Readiness | Source available; not independently qualified here. |
| License | Apache-2.0 |
| Architecture | Paged KV management, batching and tensor/pipeline/data/expert/context parallelism. |
| Host | Server/workstation accelerators; CPU and hardware plugins. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Yes: model parallelism on supported cluster backends. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | High-bandwidth cluster/collective transports. |
| Integration | OpenAI, Anthropic Messages and gRPC interfaces documented. |
| Security / trust | Deployment authentication/isolation remains operator responsibility. |
| Evidence | Official features and extensive upstream benchmark ecosystem; no phone comparison here. |
| Limits | Hardware plugins are not proof of a supported Android/iOS worker. |
| Lesson for NodeLift | Compare multi-user throughput against efficient batching, not serial requests. |
| Source revision | 564ac0de1b228568cafcbfbe8ccaccc82d6023eb |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/vllm-project/vllm/blob/564ac0de1b228568cafcbfbe8ccaccc82d6023eb/README.md)

## SGLang

ID: `sglang`

| Criterion | Assessment |
|---|---|
| Category | serving |
| Ecosystem | international |
| Documented origin | International open-source research and serving community. |
| Readiness | Source available; not independently qualified here. |
| License | Apache-2.0 |
| Architecture | High-throughput serving, cache reuse, speculation and parallel execution. |
| Host | GPU/TPU/NPU/CPU platforms; current Apple Silicon path documented. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Yes on supported model-parallel deployments. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | Cluster networking and backend collectives. |
| Integration | Serving APIs and runtime interfaces. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Current hardware/runtime documentation. |
| Limits | Mac support does not establish iPhone compute support; deployment results depend on backend. |
| Lesson for NodeLift | A strong local/cache-aware baseline can erase apparent offload gains. |
| Source revision | 181380682b50f4606d1a09df3cbbbfc21de931e3 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/sgl-project/sglang/blob/181380682b50f4606d1a09df3cbbbfc21de931e3/README.md)

## TensorRT-LLM

ID: `tensorrt-llm`

| Criterion | Assessment |
|---|---|
| Category | serving |
| Ecosystem | western |
| Documented origin | NVIDIA, United States. |
| Readiness | Source available; not independently qualified here. |
| License | Apache-2.0 for project; incorporated components have additional notices. |
| Architecture | Specialized NVIDIA kernels, speculative decoding and distributed parallel serving. |
| Host | Supported NVIDIA accelerator systems. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not established. |
| Memory / capacity | Yes: multi-GPU/node parallelism. |
| Single-chat latency | No comparable NodeLift measurement. |
| Transport | NVIDIA accelerator/cluster interconnects. |
| Integration | Runtime and serving integrations. |
| Security / trust | Not independently audited; deployment-specific controls require review. |
| Evidence | Official kernels, deployment guidance and performance reports. |
| Limits | Not a general Android/iOS heterogeneous fleet runtime. |
| Lesson for NodeLift | Use specialized server results as architectural references, not phone performance predictions. |
| Source revision | 2d1a7d170eb808bbe0e1203aa9d34dea702d52c5 |
| Checked | 2026-10-31 |

Sources: [Pinned primary source](https://github.com/NVIDIA/TensorRT-LLM/blob/2d1a7d170eb808bbe0e1203aa9d34dea702d52c5/README.md); [License at inspected revision](https://github.com/NVIDIA/TensorRT-LLM/blob/2d1a7d170eb808bbe0e1203aa9d34dea702d52c5/LICENSE)

## LM Studio / LM Link / Locally

ID: `lm-studio`

| Criterion | Assessment |
|---|---|
| Category | baseline |
| Ecosystem | western |
| Documented origin | LM Studio/Element Labs, United States. |
| Readiness | Desktop application and linked-device service. |
| License | Application/service terms; separate SDK repositories have their own licenses. |
| Architecture | A device accesses a model hosted on another linked device. |
| Host | Desktop LM Studio host. |
| Android | Android compute-worker support not established by LM Link documentation. |
| iOS | Locally is the linked iPhone/iPad client in the documented workflow. |
| Mobile compute | LM Link example uses phone as client; local app features are a different execution path. |
| Memory / capacity | Remote whole-model access; cross-phone weight pooling not documented. |
| Single-chat latency | Latency includes remote service/link; no common benchmark with NodeLift. |
| Transport | Tailscale-based end-to-end encrypted links. |
| Integration | REST, lms CLI and application integration. |
| Security / trust | End-to-end encryption documented; linked devices remain the trusted endpoints. |
| Evidence | Official LM Link documentation. |
| Limits | Remote model access is not donated phone RAM or distributed decoding. |
| Lesson for NodeLift | Integration UX is valuable; describe precisely which machine performs inference. |
| Source revision | Document version stated in sources |
| Checked | 2026-10-31 |

Sources: [Official LM Link](https://lmstudio.ai/docs/lmlink)

## LinguaLinked

ID: `lingualinked`

| Criterion | Assessment |
|---|---|
| Category | research |
| Ecosystem | western |
| Documented origin | UC Irvine and VMware Research, United States. |
| Readiness | Published research/prototype; not a qualified NodeLift integration. |
| License | Paper access terms do not establish a reusable software license. |
| Architecture | Model subgraphs assigned to trusted mobile devices with runtime load balancing. |
| Host | Coordinator plus Android device group. |
| Android | Physical Android prototype and app demonstrated. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Yes: model partitions. |
| Memory / capacity | Yes: model partitioning across trusted devices. |
| Single-chat latency | Author results only; no same-hardware NodeLift comparison. |
| Transport | Local network; monitored bandwidth/latency. |
| Integration | Research interface; drop-in Ollama/LM Studio plugin not established. |
| Security / trust | Research assumptions; production pairing/authentication not qualified. |
| Evidence | ACL 2024 system demo; physical Android devices, including a two-Pixel demonstration. |
| Limits | Model conversion/graph extraction and trusted-node assumptions; no iOS app established. |
| Lesson for NodeLift | Profile computation, memory and link cost together; monitor load during execution. |
| Source revision | ACL 2024, 2024.acl-demos.16 |
| Checked | 2026-10-31 |

Sources: [Author paper and PDF](https://aclanthology.org/2024.acl-demos.16/); [Author implementation](https://github.com/zjc664656505/LinguaLinked-Inference)

## EdgeShard

ID: `edgeshard`

| Criterion | Assessment |
|---|---|
| Category | research |
| Ecosystem | asia |
| Documented origin | Hong Kong Polytechnic University, Hong Kong, China. |
| Readiness | Published research/prototype; not a qualified NodeLift integration. |
| License | Paper access terms do not establish a reusable software license. |
| Architecture | Joint device selection/model partitioning using dynamic programming. |
| Host | Heterogeneous physical edge prototype. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Edge compute demonstrated; native phone application not established. |
| Memory / capacity | Yes: distributed model shards. |
| Single-chat latency | Author results only; no same-hardware NodeLift comparison. |
| Transport | Network-aware partition placement. |
| Integration | Research interface; drop-in Ollama/LM Studio plugin not established. |
| Security / trust | Research assumptions; production pairing/authentication not qualified. |
| Evidence | Llama2 experiments on a physical heterogeneous prototype, author reported. |
| Limits | Optimizing latency and throughput uses different objectives; no consumer mobile release established. |
| Lesson for NodeLift | A capacity-feasible partition may still be the wrong latency partition. |
| Source revision | arXiv:2405.14371v1 |
| Checked | 2026-10-31 |

Sources: [Primary paper v1](https://arxiv.org/html/2405.14371v1)

## PowerInfer-2

ID: `powerinfer-2`

| Criterion | Assessment |
|---|---|
| Category | research |
| Ecosystem | asia |
| Documented origin | SJTU IPADS, Shanghai, China. |
| Readiness | Published research/prototype; not a qualified NodeLift integration. |
| License | Paper access terms do not establish a reusable software license. |
| Architecture | Neuron-cluster CPU/NPU scheduling with storage offload and neuron caching. |
| Host | Smartphone-local execution. |
| Android | OnePlus 12/Ace 2 physical testbed in paper. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Yes: local heterogeneous CPU/NPU inference. |
| Memory / capacity | Exceeds phone RAM using storage/sparsity; no multi-phone RAM pool. |
| Single-chat latency | Author results only; no same-hardware NodeLift comparison. |
| Transport | Local UFS/storage and accelerator transfers. |
| Integration | Research interface; drop-in Ollama/LM Studio plugin not established. |
| Security / trust | Research assumptions; production pairing/authentication not qualified. |
| Evidence | Physical phones; 47B TurboSparse-Mixtral result is author-reported and model-specific. |
| Limits | Sparse/modified model and accuracy assumptions; not arbitrary GGUF equivalence or a downloadable general fleet app. |
| Lesson for NodeLift | Treat quality, storage traffic and NPU scheduling as part of the benchmark. |
| Source revision | arXiv:2406.06282v3 |
| Checked | 2026-10-31 |

Sources: [Primary paper v3](https://arxiv.org/html/2406.06282v3); [Related project](https://github.com/Tiiny-AI/PowerInfer)

## WISP

ID: `wisp`

| Criterion | Assessment |
|---|---|
| Category | research |
| Ecosystem | western |
| Documented origin | Virginia Tech, UCD, NTUA and Queen's Belfast; US/Ireland/Greece/UK. |
| Readiness | Published research/prototype; not a qualified NodeLift integration. |
| License | Paper access terms do not establish a reusable software license. |
| Architecture | Distributed drafting with wasted-work prediction and SLO-aware verification batching. |
| Host | Edge draft devices plus centralized verification. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Edge drafting studied; native Android/iOS product not established. |
| Memory / capacity | Draft distribution, not target-weight pooling. |
| Single-chat latency | Author results only; no same-hardware NodeLift comparison. |
| Transport | Edge/server network with scheduling model. |
| Integration | Research interface; drop-in Ollama/LM Studio plugin not established. |
| Security / trust | Research assumptions; production pairing/authentication not qualified. |
| Evidence | Paper numerical evaluation and estimator profiling; no NodeLift device replication. |
| Limits | System capacity/goodput gains are not automatically single-user latency gains. |
| Lesson for NodeLift | Measure rejected suffix work and verifier contention; adapt draft length and batching. |
| Source revision | arXiv:2601.11652v2 |
| Checked | 2026-10-31 |

Sources: [Primary paper v2](https://arxiv.org/html/2601.11652v2)

## FlexSpec

ID: `flexspec`

| Criterion | Assessment |
|---|---|
| Category | research |
| Ecosystem | international |
| Documented origin | Baidu/SJTU/Shenzhen collaborators, KTH Sweden and Canadian affiliation. |
| Readiness | Published research/prototype; not a qualified NodeLift integration. |
| License | Paper access terms do not establish a reusable software license. |
| Architecture | Shared-backbone frozen draft with evolving targets and channel-aware speculation. |
| Host | Edge/cloud experimental setup. |
| Android | Not documented in the reviewed sources. |
| iOS | iPhone 15 Pro Max case is a simulation in the study. |
| Mobile compute | Edge-device evaluation; distinguish simulated hardware cases. |
| Memory / capacity | No distributed target-weight RAM pool. |
| Single-chat latency | Author results only; no same-hardware NodeLift comparison. |
| Transport | Channel-adaptive draft/verify exchanges. |
| Integration | Research interface; drop-in Ollama/LM Studio plugin not established. |
| Security / trust | Research assumptions; production pairing/authentication not qualified. |
| Evidence | Author experiments under model alignment/training assumptions. |
| Limits | Results do not transfer automatically to unrelated GGUF draft/target pairs or physical iPhones. |
| Lesson for NodeLift | Version/tokenizer compatibility and link-aware block selection need explicit qualification. |
| Source revision | arXiv:2601.00644v1 |
| Checked | 2026-10-31 |

Sources: [Primary paper v1](https://arxiv.org/html/2601.00644v1)

## DiP-SD

ID: `dip-sd`

| Criterion | Assessment |
|---|---|
| Category | research |
| Ecosystem | asia |
| Documented origin | Tsinghua University, Beijing, China. |
| Readiness | Published research/prototype; not a qualified NodeLift integration. |
| License | Paper access terms do not establish a reusable software license. |
| Architecture | Distributed multi-user drafts, pipelined phases and batch/draft-length optimization. |
| Host | Modeled edge server/devices; GPU profiling supplies cost parameters. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Modeled client drafting; physical phone cluster not demonstrated by these experiments. |
| Memory / capacity | Distributed drafts; target remains at verifier. |
| Single-chat latency | Author results only; no same-hardware NodeLift comparison. |
| Transport | Modeled edge network and verification pipeline. |
| Integration | Research interface; drop-in Ollama/LM Studio plugin not established. |
| Security / trust | Research assumptions; production pairing/authentication not qualified. |
| Evidence | RTX 3090/A100 profiling followed by numerical simulation. |
| Limits | Throughput optimization and simulated heterogeneous users are not physical single-chat speedup. |
| Lesson for NodeLift | Include a batched local verifier baseline and label simulation explicitly. |
| Source revision | arXiv:2604.20919v1 |
| Checked | 2026-10-31 |

Sources: [Primary paper v1](https://arxiv.org/html/2604.20919v1)

## Speculation at a Distance

ID: `speculation-distance`

| Criterion | Assessment |
|---|---|
| Category | research |
| Ecosystem | western |
| Documented origin | University of Victoria, Canada. |
| Readiness | Published research/prototype; not a qualified NodeLift integration. |
| License | Paper access terms do not establish a reusable software license. |
| Architecture | Analytical comparison of co-located and edge/cloud speculative decoding. |
| Host | Analytical deployment regimes. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Not an application. |
| Memory / capacity | No implementation of a RAM pool. |
| Single-chat latency | Author results only; no same-hardware NodeLift comparison. |
| Transport | WAN communication bounds and pipeline conditions. |
| Integration | Research interface; drop-in Ollama/LM Studio plugin not established. |
| Security / trust | Research assumptions; production pairing/authentication not qualified. |
| Evidence | Conditional mathematical analysis; not a phone benchmark. |
| Limits | Synchronous result fixes models, acceptance and contention-free service costs; it is not a universal LAN impossibility theorem. |
| Lesson for NodeLift | Compare remote speculation with best local speculation, not just target-only generation. |
| Source revision | arXiv:2606.25091v2 |
| Checked | 2026-10-31 |

Sources: [Primary paper v2](https://arxiv.org/html/2606.25091v2)

## PipeInfer

ID: `pipeinfer`

| Criterion | Assessment |
|---|---|
| Category | research |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Published research/prototype; not a qualified NodeLift integration. |
| License | Paper access terms do not establish a reusable software license. |
| Architecture | Continuous asynchronous speculation with early cancellation in heterogeneous pipelines. |
| Host | Experimental distributed computer cluster. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Native Android/iOS worker qualification not established. |
| Memory / capacity | Pipeline partitions and speculation; deployment-specific memory placement. |
| Single-chat latency | Author results only; no same-hardware NodeLift comparison. |
| Transport | Cluster interconnects with bandwidth sensitivity. |
| Integration | Research interface; drop-in Ollama/LM Studio plugin not established. |
| Security / trust | Research assumptions; production pairing/authentication not qualified. |
| Evidence | Author experimental comparison; not replicated by NodeLift. |
| Limits | No ready-made mobile lifecycle/pairing app established. |
| Lesson for NodeLift | Cancel invalid work promptly and measure wasted in-flight computation. |
| Source revision | arXiv:2407.11798v2 |
| Checked | 2026-10-31 |

Sources: [Primary paper v2](https://arxiv.org/abs/2407.11798v2)

## PipeSpec

ID: `pipespec`

| Criterion | Assessment |
|---|---|
| Category | research |
| Ecosystem | unverified |
| Documented origin | Maintainer geography not established in the reviewed primary sources. |
| Readiness | Published research/prototype; not a qualified NodeLift integration. |
| License | Paper access terms do not establish a reusable software license. |
| Architecture | Hierarchical models execute asynchronously with verification and rollback. |
| Host | Experimental multi-device model pipeline. |
| Android | Not documented in the reviewed sources. |
| iOS | Not documented in the reviewed sources. |
| Mobile compute | Native phone deployment not established. |
| Memory / capacity | Multiple drafting/verifying models; target-weight pooling is not implied. |
| Single-chat latency | Author results only; no same-hardware NodeLift comparison. |
| Transport | Pipeline coordination messages. |
| Integration | Research interface; drop-in Ollama/LM Studio plugin not established. |
| Security / trust | Research assumptions; production pairing/authentication not qualified. |
| Evidence | ACL 2025 experiments on summarization, math and code. |
| Limits | Analytical throughput guarantees rely on the paper's assumptions; not a universal mobile latency guarantee. |
| Lesson for NodeLift | Rollback and stage independence already have prior art; qualify real mobile network behavior. |
| Source revision | ACL Findings 2025, 2025.findings-acl.669 |
| Checked | 2026-10-31 |

Sources: [Primary paper](https://aclanthology.org/2025.findings-acl.669/); [Author implementation](https://github.com/BradMcDanel/PipeSpec)
