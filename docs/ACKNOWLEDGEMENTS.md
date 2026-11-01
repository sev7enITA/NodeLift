# Acknowledgements and research credits

NodeLift is created by Fabrizio Degni. Its development is informed by an open community of engineers, researchers and maintainers. We thank them for publishing code, methods, measurements and limitations that others can inspect and learn from. Their work deserves visible credit alongside our own contributions.

This page distinguishes software included in NodeLift from projects studied and services integrated. A citation does not imply endorsement, partnership, compatibility qualification or incorporation of source code. Licenses and original notices remain authoritative; see [third-party notices](../THIRD_PARTY_NOTICES.md).

## Particular thanks

| Project and contributors | Contribution acknowledged | Relationship to NodeLift |
| --- | --- | --- |
| [DistAI](https://github.com/alex8819/DistAi), alex8819 and contributors | A concrete Android/PC prototype, layer placement experiments, network observations and openly reported negative results | Targeted source/data study. It helped frame capacity versus speed and meaningful local baselines. The attributed research snapshot is preserved; DistAI is not bundled as NodeLift's runtime. [Lessons learned](../research/distai/LESSONS_LEARNED.md) |
| [llama.cpp and GGML](https://github.com/ggml-org/llama.cpp), the ggml-org community | Portable native inference, quantization, backends and inference primitives | Actual pinned native dependency. NodeLift does not claim authorship of upstream inference mathematics or kernels. |
| [oMLX](https://github.com/jundot/omlx), jundot and contributors | Download provenance, model residency, cache ownership and experimental distributed pipelines | Targeted study and an independently implemented local API bridge. No oMLX engine, cache or kernel was copied into NodeLift. [Assessment](../research/integrations-2026-11-01/ASSESSMENT.md) |
| [REA](https://github.com/morluto/rea), morluto and contributors | Artifact admission, bounded inspection, cleanup ownership and reproducible evidence | Source patterns informed independent tooling and documentation. No REA source is vendored or linked into NodeLift. [Assessment](../research/rea-2026-11-01/ASSESSMENT.md) |
| [LM Studio public projects](https://github.com/lmstudio-ai), LM Studio maintainers and contributors | Public SDKs, local interfaces, model metadata and MLX integration work | The adapter depends on `@lmstudio/sdk`. Other repositories were studied to the depth stated in the integration assessment, not treated as permission to copy the desktop app. |
| [Jev / TypeSafe](https://docs.typesafe.ai/introduction), the TypeSafe team | Typed decisions, explicit state and separation of routing decisions from execution | A design reference for the deterministic scheduler. No Jev model or hosted runtime is integrated. [Optimization study](../research/optimization-2026-10-31/REPORT.md) |
| [Prompt lookup decoding](https://github.com/apoorvumang/prompt-lookup-decoding), apoorvumang and contributors | Established prior art for proposing continuations from existing text | NodeLift's independently implemented lookup is not presented as a newly invented algorithm. |
| [android-hrwinfo](https://github.com/nickayl/android-hrwinfo), its original authors and contributors, including the nickayl-hosted revision | Android hardware inventory and probe design | Selective source reference, not an unchanged dependency. [Inventory assessment](../research/hardware-inventory-2026-11-01/ASSESSMENT.md) |
| [DeviceHardware](https://github.com/Shakshi3104/DeviceHardware), Shakshi3104 and contributors | Apple device catalogs and runtime hardware identity | Studied as a future catalog adapter. Catalog specifications remain separate from measured performance; code reuse is not claimed. |

## Components and platform foundations

We also thank [Project Nayuki](https://www.nayuki.io/page/qr-code-generator-library) for the local QR generator, [ZXing](https://github.com/zxing/zxing) for decoding, and the [AndroidX CameraX contributors](https://developer.android.com/jetpack/androidx/releases/camera) for camera lifecycle support. NodeLift retains their applicable notices.

The native ABI uses the [nlohmann/json](https://github.com/nlohmann/json) header and Igor Pavlov's SHA-256 implementation distributed with llama.cpp. Apple AVFoundation, SwiftUI and Metal, and Android's public platform APIs provide mobile foundations. These components have their own authors, maintainers and terms.

[Hugging Face](https://huggingface.co/) supplies the model-discovery/download interfaces, [Qwen](https://huggingface.co/Qwen) publishes the control models used in the recorded experiments, and [OpenRouter](https://openrouter.ai/) supplies the optional external text interface. Model weights and services retain their own licenses and conditions. Integration is not endorsement or an acceleration result.

## Wider research and project community

The following register links every external entry in the 31 October comparison atlas to its cited primary sources. We thank the maintainers and authors of each project and paper. Inclusion records documentary comparison at the stated revision, not a claim that every codebase was audited, copied, benchmarked or supported. The [comparison methodology](../research/comparison-2026-10-31/README.md) records the scope.

| Project or research work | Visit the project or primary publication | Inspected source |
| --- | --- | --- |
| DistAI | [Open project / publication](https://github.com/alex8819/DistAi) | [Primary source](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/README.md) |
| PhoneBorg | [Open project / publication](https://github.com/dzaczek/phoneborg) | [Primary source](https://github.com/dzaczek/phoneborg/blob/912b24009dd0f15a5512335ef18f639b29cbdc37/README.md) |
| InferRing | [Open project / publication](https://github.com/N1k1tung/infer-ring) | [Primary source](https://github.com/N1k1tung/infer-ring/blob/7c13825fa25de346208d039d4ca1e8fecbb9860b/README.md) |
| Pooled / formerly SwarmLLM | [Open project / publication](https://github.com/Nehanth/pooled) | [Primary source](https://github.com/Nehanth/pooled/blob/6b4a24f73cce7ef9a9e3ab35b9a0d4c09b51dfff/README.md) |
| Silica Cluster | [Open project / publication](https://github.com/ShintoChakkiath/Silica-Cluster-Decentralized-Mobile-AI) | [Primary source](https://github.com/ShintoChakkiath/Silica-Cluster-Decentralized-Mobile-AI/blob/7f493b04e1701c4587b945888088d9f5c9b25553/README.md) |
| prima.cpp | [Open project / publication](https://github.com/OpenCPIL/prima.cpp) | [Primary source](https://github.com/OpenCPIL/prima.cpp/blob/288df6a2cc2120387e12d6f40798f30cc525c9ea/README.md) |
| exo | [Open project / publication](https://github.com/exo-explore/exo) | [Primary source](https://github.com/exo-explore/exo/blob/871caad407a70647426dffaa455bd4d0ab1d48e6/README.md) |
| distributed-llama | [Open project / publication](https://github.com/b4rtaz/distributed-llama) | [Primary source](https://github.com/b4rtaz/distributed-llama/blob/c618cd7e9ebdae235c55d13125ae774b3d1b7b83/README.md) |
| llama.cpp / RPC | [Open project / publication](https://github.com/ggml-org/llama.cpp) | [Primary source](https://github.com/ggml-org/llama.cpp/blob/ddf48f85c933c1f438212a02eb21e7b001d2d37d/README.md) |
| Petals | [Open project / publication](https://github.com/bigscience-workshop/petals) | [Primary source](https://github.com/bigscience-workshop/petals/blob/22afba627a7eb4fcfe9418c49472c6a51334b8ac/README.md) |
| LocalAI | [Open project / publication](https://github.com/mudler/LocalAI) | [Primary source](https://github.com/mudler/LocalAI/blob/832dff3c7448a4fdb0302a9af9feca1a844553c5/README.md) |
| mycellm | [Open project / publication](https://github.com/mycellm/mycellm) | [Primary source](https://github.com/mycellm/mycellm/blob/2465f52c86e91b9237ce9fb3a27b8691e82ceab6/README.md) |
| Mesh LLM | [Open project / publication](https://github.com/Mesh-LLM/mesh-llm) | [Primary source](https://github.com/Mesh-LLM/mesh-llm/blob/6820aa4d44aea55325067dbd414c60440959366d/README.md) |
| Cake | [Open project / publication](https://github.com/evilsocket/cake) | [Primary source](https://github.com/evilsocket/cake/blob/be522af17a4a4da3e1113682ba39689c634d513f/README.md) |
| Nakshatra | [Open project / publication](https://github.com/fthrvi/nakshatra) | [Primary source](https://github.com/fthrvi/nakshatra/blob/dcf7cdd688bc466f119fc70959eba4c5e0fdbccd/README.md) |
| LLMLAB | [Open project / publication](https://github.com/xdutsuay/local-distributed-llm-lab) | [Primary source](https://github.com/xdutsuay/local-distributed-llm-lab/blob/70c1ea8f210151fb199c8291f8248fd5d16f261d/README.md) |
| Ollama Cluster fork | [Open project / publication](https://github.com/shadoq/ollama-cluster) | [Primary source](https://github.com/shadoq/ollama-cluster/blob/26675f60867c62acb323953b9e5b59205315db61/README.md) |
| GPUStack | [Open project / publication](https://github.com/gpustack/gpustack) | [Primary source](https://github.com/gpustack/gpustack/blob/6e3a42a9d3d59eb6f11407ed5cb96d5840c3f48e/README.md) |
| MLC LLM | [Open project / publication](https://github.com/mlc-ai/mlc-llm) | [Primary source](https://github.com/mlc-ai/mlc-llm/blob/44fd06d04f22c87820e205b0f2b2e5e6a1f6ca85/README.md) |
| WebLLM | [Open project / publication](https://github.com/mlc-ai/web-llm) | [Primary source](https://github.com/mlc-ai/web-llm/blob/6897fadc2bed9a5a7940265dd80220f83ca184e7/README.md) |
| MNN / MNN-LLM | [Open project / publication](https://github.com/alibaba/MNN) | [Primary source](https://github.com/alibaba/MNN/blob/17236ad20b4798a1faccc761c80f283283bec30e/README.md) |
| mllm | [Open project / publication](https://github.com/UbiquitousLearning/mllm) | [Primary source](https://github.com/UbiquitousLearning/mllm/blob/1d3c3d8e506e3d12e902af82866972623b240ce0/README.md) |
| KTransformers | [Open project / publication](https://github.com/kvcache-ai/ktransformers) | [Primary source](https://github.com/kvcache-ai/ktransformers/blob/c9873312643b615a717832946fba0346e69ab035/README.md) |
| PowerInfer | [Open project / publication](https://github.com/Tiiny-AI/PowerInfer) | [Primary source](https://github.com/Tiiny-AI/PowerInfer/blob/8bd56d69906c9d2dba4d3bf6899763401e01a9a4/README.md) |
| AirLLM | [Open project / publication](https://github.com/lyogavin/airllm) | [Primary source](https://github.com/lyogavin/airllm/blob/75a6bb3c41c6b4b5869fc7fe20828aa6367f9c46/README.md) |
| ExecuTorch | [Open project / publication](https://github.com/pytorch/executorch) | [Primary source](https://github.com/pytorch/executorch/blob/05092c126d4ed5563527f0dab57f3c5da1a7f2a7/README.md) |
| LiteRT-LM | [Open project / publication](https://github.com/google-ai-edge/LiteRT-LM) | [Primary source](https://github.com/google-ai-edge/LiteRT-LM/blob/9d613ac5bb59a142c586f50821c43f1c2d001920/README.md) |
| Google AI Edge Gallery | [Open project / publication](https://github.com/google-ai-edge/gallery) | [Primary source](https://github.com/google-ai-edge/gallery/blob/7f4d6bc7062bfc2b8db6940fd022884353c79354/README.md) |
| Cactus | [Open project / publication](https://github.com/cactus-compute/cactus) | [Primary source](https://github.com/cactus-compute/cactus/blob/2cfcdb8568eb9192323b27fd0012a834517b4419/README.md) |
| GenieX / formerly Nexa SDK repository | [Open project / publication](https://github.com/qualcomm/GenieX) | [Primary source](https://github.com/qualcomm/GenieX/blob/d66de04d57ee41db2b1df3b9b85b926e41d1c4e5/README.md) |
| InferrLM | [Open project / publication](https://github.com/loomax-labs/InferrLM) | [Primary source](https://github.com/loomax-labs/InferrLM/blob/258261f7fd2e7f54e3772a6f577441de7dec26d9/README.md) |
| PocketPal AI | [Open project / publication](https://github.com/a-ghorbani/pocketpal-ai) | [Primary source](https://github.com/a-ghorbani/pocketpal-ai/blob/f8f37d9a4676763eaaf509276b21631b9e95ba8f/README.md) |
| Pocket LLM for Android | [Open project / publication](https://github.com/dineshsoudagar/local-llms-on-android) | [Primary source](https://github.com/dineshsoudagar/local-llms-on-android/blob/8e0edbc99eb3930ad37536ec137d8882e8beaceb/README.md) |
| MobileCore / TuiMa 推嘛 | [Open project / publication](https://github.com/Harzva/mobilecore) | [Primary source](https://github.com/Harzva/mobilecore/blob/1f909373d17fc4a6413006fcd88f1c46120112cc/README.md) |
| MLX / distributed collectives | [Open project / publication](https://github.com/ml-explore/mlx) | [Primary source](https://github.com/ml-explore/mlx/blob/339279525ea3168b6fa55911529e3766a145d0b2/README.md) |
| ncnn | [Open project / publication](https://github.com/Tencent/ncnn) | [Primary source](https://github.com/Tencent/ncnn/blob/f18f3ffc94dbc76a277e94556c588ab2c2d0e1d9/README.md) |
| ONNX Runtime GenAI | [Open project / publication](https://github.com/microsoft/onnxruntime-genai) | [Primary source](https://github.com/microsoft/onnxruntime-genai/blob/77a7b3b7b46ff97b2a66259f04d783beda12a274/README.md) |
| MindSpore / Lite ecosystem | [Open project / publication](https://github.com/mindspore-ai/mindspore) | [Primary source](https://github.com/mindspore-ai/mindspore/blob/16873579685a1662f10ebd1df068bf512f211869/README.md) |
| T-MAC | [Open project / publication](https://github.com/microsoft/T-MAC) | [Primary source](https://github.com/microsoft/T-MAC/blob/7042f8f73330bd083bc1e4bc5ccb3f88a4904aee/README.md) |
| FastDeploy | [Open project / publication](https://github.com/PaddlePaddle/FastDeploy) | [Primary source](https://github.com/PaddlePaddle/FastDeploy/blob/d923caf15e1eb0da8e2efd75b0152e65cefeeddd/README.md) |
| Ollama (upstream) | [Open project / publication](https://github.com/ollama/ollama) | [Primary source](https://github.com/ollama/ollama/blob/f9323416f0c3f84d82f6c4a7bde75b717448bd44/README.md) |
| vLLM | [Open project / publication](https://github.com/vllm-project/vllm) | [Primary source](https://github.com/vllm-project/vllm/blob/564ac0de1b228568cafcbfbe8ccaccc82d6023eb/README.md) |
| SGLang | [Open project / publication](https://github.com/sgl-project/sglang) | [Primary source](https://github.com/sgl-project/sglang/blob/181380682b50f4606d1a09df3cbbbfc21de931e3/README.md) |
| TensorRT-LLM | [Open project / publication](https://github.com/NVIDIA/TensorRT-LLM) | [Primary source](https://github.com/NVIDIA/TensorRT-LLM/blob/2d1a7d170eb808bbe0e1203aa9d34dea702d52c5/README.md) |
| LM Studio / LM Link / Locally | [Open project / publication](https://lmstudio.ai/docs/lmlink) | [Primary source](https://lmstudio.ai/docs/lmlink) |
| LinguaLinked | [Open project / publication](https://github.com/zjc664656505/LinguaLinked-Inference) | [Primary source](https://aclanthology.org/2024.acl-demos.16/) |
| EdgeShard | [Open project / publication](https://arxiv.org/html/2405.14371v1) | [Primary source](https://arxiv.org/html/2405.14371v1) |
| PowerInfer-2 | [Open project / publication](https://arxiv.org/html/2406.06282v3) | [Primary source](https://arxiv.org/html/2406.06282v3) |
| WISP | [Open project / publication](https://arxiv.org/html/2601.11652v2) | [Primary source](https://arxiv.org/html/2601.11652v2) |
| FlexSpec | [Open project / publication](https://arxiv.org/html/2601.00644v1) | [Primary source](https://arxiv.org/html/2601.00644v1) |
| DiP-SD | [Open project / publication](https://arxiv.org/html/2604.20919v1) | [Primary source](https://arxiv.org/html/2604.20919v1) |
| Speculation at a Distance | [Open project / publication](https://arxiv.org/html/2606.25091v2) | [Primary source](https://arxiv.org/html/2606.25091v2) |
| PipeInfer | [Open project / publication](https://arxiv.org/abs/2407.11798v2) | [Primary source](https://arxiv.org/abs/2407.11798v2) |
| PipeSpec | [Open project / publication](https://github.com/BradMcDanel/PipeSpec) | [Primary source](https://aclanthology.org/2025.findings-acl.669/) |

The atlas includes 54 external entries plus NodeLift. Additional integration and hardware studies above were recorded on 1 November. Source links and immutable revisions are maintained with the relevant assessment; published upstream measurements remain attributed to their authors and are not represented as NodeLift replications.

## Local work and review assistance

AudioEnhancerMAX and the owner's local research supplied earlier ideas about capability-aware delegation, fallback, and timing. Audio chunks and LLM token dependencies are different workloads, so their performance conclusions are not transferred. Private project files and private data are not redistributed here.

Selected changes also received documented model-assisted reviews from GLM 5.3 Max and Gemini 4 High. Findings are adjudicated against source and tests. These reviews are assistance, not independent hardware benchmarks or certification.

## Attribution and editorial policy

Original third-party source, license text, recorded benchmark output and archived reviewer responses are preserved as evidence. NodeLift-authored explanations use English and avoid em dashes; application and showcase copy additionally supports Simplified Chinese and Italian. Punctuation in verbatim third-party material is not silently rewritten. If an attribution is incomplete, please open a [repository issue](https://github.com/sev7enITA/NodeLift/issues) with the primary source so it can be corrected.

## Additional source studies: 1 November 2026

Thank you to **PurpleDoubleD and the Locally Uncensored contributors** for their published diagnostic, platform-version, signed-update and model-memory planning work. [Project](https://github.com/PurpleDoubleD/locally-uncensored) · [focused assessment](../research/locally-uncensored-2026-11-01/ASSESSMENT.md). No implementation code was imported.

Thank you to **Apple and the MLX / MLX LM contributors** for the open distributed primitives, inference implementations and published measurements. [MLX](https://github.com/ml-explore/mlx) · [MLX LM](https://github.com/ml-explore/mlx-lm) · [distributed inference research](https://machinelearning.apple.com/research/mlx-distributed-inference). NodeLift does not claim to outperform those results or to implement their RDMA backend.
