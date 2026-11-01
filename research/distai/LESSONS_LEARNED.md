# DistAI: evidence, limits and lessons for ExpandMyHW

Assessment dated 31 October 2026, before ExpandMyHW hardware benchmarks. This document distinguishes inspected code, author-published results, our recalculations and hypotheses requiring tests. It is neither repository certification nor an independent performance replication. ExpandMyHW was subsequently named NodeLift; [later NodeLift results](../measurements/ENGINE_RESULTS.md) are reported separately.

## Verdict

DistAI demonstrates a concrete Android/PC distributed inference prototype: discovery, loading, layer partitioning, execution and an OpenAI-style API. Its most instructive result is negative: **adding memory through a layer pipeline does not add speed to one conversation**. The project states this openly. Our priority, accelerating one chat against an optimized computer, therefore needs a different experiment and a stronger baseline.

The lesson is not “Wi-Fi is impossible” or “phones are useless.” Decisions must depend on actual delegated work, the critical path, and measured hardware/network behavior. A scheduler must be able to leave every phone idle when none helps.

## Scope and reproducibility

- Repository: [alex8819/DistAi](https://github.com/alex8819/DistAi).
- Snapshot: [b1c17109498e87b3db99f8f23648d84483b68bb9](https://github.com/alex8819/DistAi/tree/b1c17109498e87b3db99f8f23648d84483b68bb9), latest observed commit dated 16 October 2026. Retrieved history contains four commits, all that day; it does not establish a long maintenance history.
- Retrieved 37 targeted text files, including the MIT license. Not a full clone or comprehensive security audit. No upstream APK, binary or inference script was executed.
- Every retrieved file matches its Git blob in the snapshot. [provenance.json](provenance.json) records tree/commit; [source-manifest.json](source-manifest.json) contains SHA-256 hashes.
- Read three JSONL files: 17 quality rows, 89 optimization rows and 27 prefill rows. These **133 rows are not 133 controlled repetitions**: configurations differ and include errors/nested measurements. Fourteen optimization rows have a nonempty error field.
- [verify_evidence.py](verify_evidence.py) reads data and literal definitions through AST without executing upstream code. It regenerates [evidence-checks.json](evidence-checks.json); it does not benchmark an LLM.

Run from the project root:

```sh
python3 research/distai/verify_evidence.py
```

## 1. The prototype expands capacity; it does not improve single-user speed

The architecture uses a `llama-server` coordinator and `ggml-rpc-server` workers holding layer groups. Weights transfer at loading; remote layers compute and exchange activations. This is not coherent remote RAM that becomes Mac memory. The README reports a 30B at **7.0 tokens/s on PC versus 3.9 distributed**, and approximately 2 tokens/s for a 7B on PC + phone. These are the author's results, not ours.

For a pipeline without useful overlap within one token:

`T_token ≈ sum(T_stage_i) + sum(T_transfer_i + T_synchronization_i)`.

If all layers fit the host and each is faster there, moving some to slower nodes cannot improve decode under those assumptions. This does not prove every form of distributed inference, speculation or intra-layer parallelism impossible.

**Required improvement:** compare the same chat and target against an optimized host. “Larger model fits” and “more users served” are separate outcomes.

Source: [pinned README](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/README.md).

## 2. The 3× result is queue throughput and depends on the baseline

The final three rows of `results-codeeval.jsonl` report:

| Published configuration | Time for 22 tasks | Tasks passed |
|---|---:|---:|
| Sequential PC | 202.7 s | 20/22 |
| PC with 4 slots | 106.4 s | 20/22 |
| PC 4 + Xiaomi 4 + Huawei 1 slot | 67.7 s | 20/22 |

Recalculation: `202.7 / 67.7 = 2.994×`, but `106.4 / 67.7 = 1.572×`. The cluster reduces queue completion time by **36.37%** against the batched PC. Interesting, but **not 3× against the optimized baseline and not 3× for one chat**. One batch per configuration is published, without a confidence interval.

The script's `tok_s` field is an arithmetic mean of request speeds, not total emitted tokens divided by queue completion time. It must not be labelled aggregate system throughput.

**Required improvement:** tuned batching/speculation baselines; individual latency separated from aggregate capacity; total tokens/wall-clock seconds; distributions and repetitions, not one favorable number.

Sources: [data](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/results-codeeval.jsonl), [script](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/codeeval.py).

## 3. Improved prefill: useful measurements, extrapolated full turn

For 7B Q4_K_M with 14 PC layers and 14 Samsung layers, patch off/on:

- 2048-token prefill: **312.093 → 169.411 seconds** in published data.
- Long-context decode: **1.91 → 1.89 tokens/s**, so no decode improvement in that comparison.
- Observed generations contain **64 tokens**.
- The **445 → 305 second** summary projects a 300-token turn using the mean of short-/long-context decode. Our recalculation reproduces 445.438 and 304.696 seconds.
- Using long-context decode instead yields about 469.161 and 328.141 seconds: **also estimates**, not new measurements.

The published prefill improvement remains substantial. Avoid presenting a projection as a fully measured conversation or transferring the prefill gain to decode tokens/s.

Sources: [prefillbench.py, lines 44–50](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/prefillbench.py#L44), [JSONL](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/results-prefill.jsonl).

## 4. Wi-Fi, USB and power saving: measure the complete path

Notes report about 1.4–2 MB/s over 5 GHz Wi-Fi on those configurations; ADB up to 237 MB/s in one direction and approximately 35 in the other; USB tethering about 29.7/40.4 MB/s with 1.2–1.6 ms RTT. These describe specific devices/stacks, not universal Wi-Fi/USB limits. ADB forwarding, USB networking and file copying are different tests.

A useful observation: with idle radio, reported mean/maximum latency rises to 205/539 ms; periodic bidirectional traffic reduces it to about 5.6/7 ms. `Keepalive.kt` sends one byte every 100 ms and expires peers after 30 seconds. Keeping radio/CPU awake costs energy and can raise temperature; measure sustained benefit with those costs included.

**Required improvement:** compare Wi-Fi/USB/Ethernet on the same phone with actual message sizes, both directions, idle/loaded network, p50/p95/p99, thermals and joules per response. Good Wi-Fi can beat a USB 2.0 port in bandwidth; cable may win on latency/predictability. USB-C does not guarantee USB 3, Thunderbolt or OS-supported networking.

Sources: [NOTES](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/NOTES.md), [Keepalive.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/Keepalive.kt).

## 5. Node selection already exists; the cost model is fragile

`SplitPlan.kt` selects node subsets, favors faster nodes and can exclude some. This idea is not new. However:

- Android available RAM is multiplied by 0.5 on workers and 0.6 on the coordinator, with fixed 400 MiB/200 MiB compute reserves. These are empirical heuristics, not OS memory contracts.
- Missing speed data falls back to memory-proportional assignment: useful for fitting a model, insufficient for promising acceleration.
- Estimated cost uses average layer bytes / effective bandwidth and RTT, plus **10 fixed milliseconds per remote node**. Stored size alone does not describe MoE active bytes, operators/kernels, KV, context, transfers or thermal state.
- `RpcBench.kt` uses synthetic Q4_0 matvecs and selects minima: the minimum of five RTTs and best graph times. This calibrates peak performance, not sustained p95 latency.
- Its bandwidth variable represents effective compute/memory bandwidth in the benchmark, not Wi-Fi bandwidth.

**Required improvement:** profiles by model/backend/phase/context, actual block durations, memory pressure, adaptive reserve and thermal pressure. Validate prediction error out of sample; use safety margins/hysteresis to avoid repeated migrations. In speed mode, a missing profile means “calibrate or stay local,” not blind allocation.

Sources: [SplitPlan.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/SplitPlan.kt), [RpcBench.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/RpcBench.kt).

## 6. Existing optimizations and changes that alter the problem

DistAI keeps embedding/output on the coordinator, avoiding a full vocabulary of logits returned each token. It documents repacking, persistent thread pools, fast-core affinity and differentiated ARM binaries. Reuse the lessons after checking what upstream backends already provide.

The default PC build disables Metal, but **`--gpu` enables Metal on macOS**. Comparing our Metal path against its default CPU path would not establish a new architectural advantage. Conclusions about older Intel integrated GPUs do not transfer directly to Apple Silicon unified memory.

Reducing `expert_used_count` from 8 to 6 changes model computation. Equal 21/22 scores for two configurations do not prove unchanged quality. Four experts score 14/22; five score 19/22: the repository itself shows sensitivity. Keep expert routing/count unchanged in the primary comparison; approximate variants need a separate quality/performance experiment.

Sources: [NodeService.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/NodeService.kt), [build-pc.py](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/native/build-pc.py), [patches](https://github.com/alex8819/DistAi/tree/b1c17109498e87b3db99f8f23648d84483b68bb9/native/patches).

## 7. Speculation: avoid per-token remote delegation

A `NodeService.kt` comment reports Huawei RPC drafting at 2.24 tokens/s versus 4.5 without drafting: each proposed token pays the remote path. The implementation therefore chooses a local draft. `Speculative.kt` calibrates it and can disable it when unhelpful: conditional activation already exists too.

This negative experiment **is not equivalent** to a phone retaining a complete small model, generating a block autonomously and proposing it to the Mac target. That second architecture is a candidate, not a demonstrated solution or absolute novelty: PipeInfer, PipeSpec and other asynchronous/distributed speculation research already exist.

For a sequential cycle, an initial condition is:

`(T_draft_block + T_network + T_verify + T_rollback) / E[accepted_and_committed_tokens] < T_baseline_token`.

With overlap, derive the numerator from the actual critical-path timeline, including queues, discarded work and resynchronization. Do not arbitrarily replace a sum with a maximum. Compare with **the strongest local draft**, including asynchronous execution, as well as target-only. Verification time is not constant: it depends on k, context and GPU.

Start with greedy token equivalence, then exact sampling. Preserving the target distribution requires correct acceptance/rejection and the draft distribution needed for residual sampling, or a proven equivalent protocol. Token IDs alone are insufficient; that traffic may erase some benefit.

DistAI's draft selection checks tokenizer family and vocabulary size with a tolerance of 128, not complete token-ID/normalization/special-token identity. This is not an observed incompatibility, but it is insufficient preventive certification. Our manifest must verify identity and handle incompatibility explicitly.

Sources: [Speculative.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/Speculative.kt), [Gguf.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/Gguf.kt), [PipeInfer](https://arxiv.org/abs/2407.11798), [PipeSpec](https://aclanthology.org/2025.findings-acl.669/).

## 8. Diffusion is an experimental branch, not a universal shortcut

BD3LM patches are separate and not applied to the standard build. `d3_rpc.py` defaults to **Stable-DiffCoder-8B-Instruct.Q4_K_M.gguf**: without further evidence, it is incorrect to accuse it of simply applying noncausal attention to ordinary autoregressive weights.

Decisive checks remain: model revision/hash, compatible training objective, mask-token semantics and complete generation. `bd3eval.py` expects `results-dllm.jsonl`, but that file is absent from the retrieved published tree. Summary numbers in the notes lack that detailed trace there. A `llama-bench` block-prefill microbenchmark does not establish correct useful tokens/s for a complete response.

**Required improvement:** a separate benchmark for natively diffusion-trained models, comparable quality and retained outputs. No promise to parallelize an arbitrary causal LLM by changing its mask.

Sources: [experimental patches](https://github.com/alex8819/DistAi/tree/b1c17109498e87b3db99f8f23648d84483b68bb9/native/patches-sperimentali), [d3_rpc.py](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/d3_rpc.py), [bd3eval.py](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/bd3eval.py).

## 9. Quality, reliability and operational boundaries

The 22 coding tasks are useful smoke tests, not a general evaluation. Limited assertions, one generation sample and no broad corpus/statistical interval do not justify “no quality loss.” JSONL files retain outcomes, not all responses, so every error cannot be reexamined retrospectively. An initial suspicion about `group_anagrams` was checked and **withdrawn: its oracle is correct**, as recorded by our verifier.

Generated Python is executed with `python3 -I` and a timeout: import isolation is not a security sandbox. Our coding benchmark must run outputs in a genuinely isolated environment with network, filesystem and resource limits.

Unauthenticated/unencrypted RPC and management servers on network interfaces require an explicit trust boundary. Product requirements include pairing, node identity, job authorization, protected transport, allocation limits, verified models and no automatic Internet exposure. No penetration test was performed.

DistAI instructions call for restarting a job after cable disconnection. Weight caching is not KV/session resumption. Our runtime must define behavior when a phone locks, handles a call, experiences thermal pressure or disappears. Fallback may require context replay; count its duration and discarded work.

The documented llama.cpp pin is `69f201a`; protocol and patches must match. A future build should lock the full commit and patch/model hashes, rather than relying on an incidental checkout or mutable `main` URL.

## 10. Lessons and required proof

| DistAI lesson | Proposed ExpandMyHW choice | Evidence needed to claim improvement |
|---|---|---|
| Serial layers slow a chat | Separate speed and capacity modes | Same-target speedup against optimized host, or capacity-only claim |
| Per-token RPC draft is too expensive | Autonomous block draft; measured overlap | Beat optimized local drafting with equivalence and networking cost included |
| Older network/power saving dominates | Job-aware transport selection | Better sustained p95/response time; energy cost published |
| Synthetic/fixed cost model | Phase/model profiles and actual state | Out-of-sample prediction validation; unhelpful nodes excluded |
| 3× depends on comparator | Strong baselines and complete raw evidence | Confidence intervals and public metric definitions |
| Small quality test | Equivalence plus separate broad suite | No hidden target change; preregistered quality margins |
| Only Android mobile in inspected repository | Native Android/iOS workers with explicit capabilities | Physical tests on both OSes, including memory/thermals/lifecycle |
| Crash/disconnection requires restart | Explicit drain, cancellation, fallback and replay | Fault injection with recovery timing and no corrupt response |

**Decision at this checkpoint:** run discriminating microexperiments and preregistered benchmarks before building the full plugin. Unidentified phones had not been shown to accelerate the observed 64 GiB M3 Max. That was a hypothesis to falsify quickly, not a promised outcome.
