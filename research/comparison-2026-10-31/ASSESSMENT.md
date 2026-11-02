# NodeLift: global comparison and engineering implications

**Sources frozen on 31 October 2026 · 55 entries · experimental NodeLift 0.2.1 checkpoint**

**Update, 2 November 2026:** Only the NodeLift row in the comparison atlas has been refreshed. Physical [Xiaomi](https://github.com/sev7enITA/NodeLift/blob/3e7016a7c51d2bdedee0e9427e9e009aee09f3a2/research/phone-tradeoffs-2026-11-02/REPORT.md) and [iPhone](https://github.com/sev7enITA/NodeLift/blob/3e7016a7c51d2bdedee0e9427e9e009aee09f3a2/research/iphone-tradeoffs-2026-11-02/REPORT.md) trials supplied draft tokens but were slower than their matched Mac controls in the measured fixed-mode scope. The [generic desktop/server probe](https://github.com/sev7enITA/NodeLift/blob/3e7016a7c51d2bdedee0e9427e9e009aee09f3a2/docs/NODE_PROBE.md) has physical Mac evidence and Windows/Linux fixtures; it is not a remote worker or proof of pooled RAM. The other 54 project entries and the historical analysis below retain the 31 October source freeze.

Other projects already demonstrate phone reuse for distributed inference. NodeLift's useful contribution would be making the decision to involve them measurable and reliable, with verifiable integration and failure recovery. There is no evidence to call NodeLift the first, fastest or superior to every alternative. This is a dated research snapshot; see the [current changelog](../../CHANGELOG.md) for later releases.

The [detailed matrix](../../site/NodeLift/data/comparison.md), [JSON](../../site/NodeLift/data/comparison.json), [CSV](../../site/NodeLift/data/comparison.csv) and [method](../../site/NodeLift/data/methodology.md) share one source. Public showcase: [fabriziodegni.com/NodeLift](https://www.fabriziodegni.com/NodeLift/).

## Inventory findings

The scope includes 16 distributed systems, 17 runtimes, 6 serving platforms, 5 mobile apps, 2 references and 9 research works. These are not 55 interchangeable competitors: runtimes may become dependencies, papers are scientific prior work, and apps provide mobile-experience comparisons. Universal completeness is not verifiable; this is a broad, dated, correctable inventory using common criteria.

Asian collaborations include Alibaba MNN, Tencent ncnn, Huawei/MindSpore, PaddlePaddle/FastDeploy, KTransformers, PowerInfer and studies such as EdgeShard/DiP-SD. Western/international sources include llama.cpp, MLX, Qualcomm GenieX, Google LiteRT-LM, ExecuTorch, Petals, LinguaLinked and WISP. Independent maintainers without documented provenance are labelled “unverified”; names do not establish origin.

## Closest references

| Family | What the source demonstrates | Implication for NodeLift |
|---|---|---|
| [PhoneBorg](https://github.com/dzaczek/phoneborg) | Android through ADB/USB, routing and BigBrain sharding; physical and emulated tests separated | USB and thermal handling require comparison; more phones do not guarantee more tokens/s |
| [InferRing](https://github.com/N1k1tung/infer-ring) | Apple app combining Mac/iPhone; prefill and decode can move in opposite directions | iOS compute and mixed Apple clusters are concrete prior work, not NodeLift novelty |
| [Pooled](https://github.com/Nehanth/pooled) | Browser WebGPU/WebRTC, mobile shards and expert streaming; previously SwarmLLM | Browser reduces installation friction but adds memory, compatibility and lifecycle limits |
| [DistAI](https://github.com/alex8819/DistAi) / [prima.cpp](https://github.com/OpenCPIL/prima.cpp) | Heterogeneous-node offload/planning; capacity and speed need separate evidence | Planner must exclude nodes where appropriate and account for disk, compute and communication |
| [Cake](https://github.com/evilsocket/cake) | Workers across systems, shards and documented automatic weight distribution | Provisioning and mixed platforms have precedents; check reuse terms |
| [LinguaLinked](https://aclanthology.org/2024.acl-demos.16/) | Partitioning/load balancing demonstrated on physical Android devices | Compare against a real mobile system, not only a remote server |

## Four different problems

1. **Capacity:** fitting weights and KV cache that exceed one device. Layer sharding, expert distribution and storage offload differ. NodeLift 0.2.1 does not shard the target.
2. **Single-chat latency:** reducing time to first token, inter-token delay and completion time. NodeLift remote drafting targets this, but a benefit is unproven.
3. **Throughput:** completing more requests with a fleet. Routing, replicas and batching can help even when individual requests slow down.
4. **Access:** using a phone to access a model hosted elsewhere. [LM Link](https://lmstudio.ai/docs/lmlink) addresses this; it does not lend phone RAM to the desktop model.

No overall score replaces these outcomes. An application can excel in one and be irrelevant to another.

## Engine implications

[WISP](https://arxiv.org/html/2601.11652v2), [FlexSpec](https://arxiv.org/html/2601.00644v1), [PipeInfer](https://arxiv.org/abs/2407.11798v2) and [PipeSpec](https://aclanthology.org/2025.findings-acl.669/) prevent novelty claims based merely on adaptive drafts, pipelines, cancellation or rollback. Study and qualify those techniques. [DiP-SD](https://arxiv.org/html/2604.20919v1) helps formulate a multi-user objective, but its simulation is not a Xiaomi test.

[Speculation at a Distance](https://arxiv.org/html/2606.25091v2) requires comparison with local speculation when possible. Its conditions are not a universal RTT threshold or proof of impossibility on heterogeneous LANs.

Proposed path:

- A utility selector compares host-only, strongest local acceleration and remote drafting using **complete time per actually committed token**. Count waits, rejected drafts, verification, synchronization and recovery.
- Evaluate decisions in observation mode before activation, using conservative margins and hysteresis. A connected device does not automatically belong on the critical path.
- A separate capacity path makes the tradeoff explicit: a larger model may become executable with greater latency. Do not call that acceleration.
- Compare Android CPU/GPU/NPU candidates with compatible models; compilation, loading and quality are part of the cost.
- Mobile lifecycle covers suspension, revocation, network changes, backgrounding, temperature and battery. Existing authenticated transport does not replace those tests.

These are **future development/experimental directions**, not features all available in the dated release.

For Huawei, the official [MindSpore Lite page](https://www.mindspore.cn/lite/en) documents Android/iOS and a Lite Kit integrated into HarmonyOS NEXT. This is a native lead to investigate, not proof of compatibility with a specific LLM, the owner's phone or NodeLift. Do not confuse it with other projects' Termux paths.

## Reproducible benchmarks to complete

First require an actually online native companion and a large target supported by the verifier. Then:

| Experiment | Shared conditions | Measurements and criterion |
|---|---|---|
| Host-only / strongest local / phone | Same weights, tokenizer, quantization, prompt, context and output budget; randomized order and declared warmup | Actual tokens, TTFT, inter-token p50/p95, completion, correctness, RAM/KV and swap |
| Wi-Fi hotspot / AP / USB networking / Ethernet | Verified IP path on each OS; realistic payloads; active inference | RTT distribution, jitter, bidirectional throughput, p95/reconnections; not nominal speed alone |
| Sustained session | Declared screen/power states, repetitions and controlled cooling | Performance drift, thermal state, energy/battery, failures |
| More nodes / more requests | Same workload; local baseline with equivalent batching/queues | Goodput within latency objective, fairness and discarded work |
| Fault injection | Node loss, expired lease, late reply, wrong prefix, cancellation | Correctness, recovery time and absence of duplicate output |

Preregister a practical candidate threshold, for example at least 10% median improvement with a favorable confidence interval and no unacceptable p95 regression. This is a **proposed criterion**, not a result or promise. Evaluate a modification within the same experiment, not across sessions with different workloads.

## NodeLift evidence at this checkpoint

[Public results](../measurements/ENGINE_RESULTS.md) include 156 comparison runs overall, but only 60 belong to the frozen NodeLift 0.2.1 repeat. That group uses Qwen2.5 1.5B/0.5B on M3 Max: all 48 output pairs match, while median speedup is below one in every arm. The 36 upstream trials use different timing paths and do not establish a direct NodeLift/llama.cpp ranking.

The Xiaomi pilot measures networking/protocol. The emulated TLS node tests integration/recovery. iOS is unsigned. The 27B kernel benchmark does not establish NodeLift support for that hybrid architecture. Keeping these evidence classes separate makes the project assessable and prevents claiming an improvement not yet achieved.

## Defensible positioning

A local fleet should explain **when a device helps, how much it helps and how it falls back when unhelpful**, with public benchmarks and version-specific support. Potential value lies in verifiable integration and decision quality, not nominal RAM totals. Hardware reuse is the mission; energy savings, longer useful life and GitHub popularity remain outcomes to measure, not established claims.
