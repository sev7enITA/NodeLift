# Engine measurements: 31 October 2026

**No physical-phone LLM speedup has been demonstrated.** The control experiments below use real weights on the M3 Max. A separate TLS integration test emulates a node locally. Neither is a Xiaomi native-inference result.

## Small-model pilot

Target: official Qwen2.5-1.5B-Instruct Q4_K_M; draft: official Qwen2.5-0.5B-Instruct Q4_K_M. Hashes/revisions are in `profiles/control-models.json`. Host: M3 Max, 64 GiB, Metal, 8 CPU threads, context 2048, greedy, flash attention. Six categorized prompts, two repetitions, maximum 64 output tokens with EOS respected. Warmup is excluded and actual lengths are retained.

The [NodeLift pilot](engine-control-pilot/manifest.json) randomized 60 runs across host-only and local draft blocks 1/4/8/16. All 48 paired draft/host comparisons had identical token IDs. Median paired end-to-end speedup relative to the same NodeLift host path:

| Draft block | Speedup | Interpretation |
|---|---:|---|
| 1 | 0.703× | Slower |
| 4 | 0.791× | Slower |
| 8 | 0.635× | Slower |
| 16 | 0.423× | Slower |

[Raw runs](engine-control-pilot/runs.jsonl), [paired comparisons](engine-control-pilot/summary.json), [hashes](engine-control-pilot/hashes.json). This first pilot was collected from a working tree before an implementation commit/build provenance was frozen. The verification algorithm was retained, but later controller/lifecycle/streaming changes mean it must not be advertised as a reproducible final-release performance certification. The shared GPU was not instrumented for all unrelated desktop activity.

## Version 0.2.1 repeat with frozen source/build identity

Repeated 60 runs after the code reviews at source commit `d5e0f5d42a4a8b7a673af1b09810251691fe6992`, clean working tree at start, recording native-library and source hashes. Same six prompts, two repetitions, context, weights, output budget and randomized arm plan. Delta detokenization is now included in block/rate timing. All 48 paired token-ID comparisons again matched.

| Draft block | Median paired end-to-end speedup |
|---|---:|
| 1 | 0.691× |
| 4 | 0.719× |
| 8 | 0.605× |
| 16 | 0.425× |

[Manifest and build/source identity](engine-0.2.1-control/manifest.json), [raw runs](engine-0.2.1-control/runs.jsonl), [paired summary](engine-0.2.1-control/summary.json). Local drafting remained slower for this small pair. Differences between the two sessions are not an isolated estimate of any individual code change. No background desktop load/thermal isolation or confidence interval was established.

## Same-revision upstream comparators

Built upstream llama-server from `ddf48f85c933c1f438212a02eb21e7b001d2d37d`, using the same control weights and exact native-formatted prompt token IDs. Thirty-six requests: target-only, draft-simple (block 4), ngram-mod; six prompts and two repetitions per arm. Arm order was randomized in blocks, with process reload and warmup per arm. Only one comparator process performed inference at a time.

| Upstream arm vs upstream target-only | Median paired HTTP wall-time speedup | Token IDs equal |
|---|---:|---|
| draft-simple | 0.743× | 12/12 |
| ngram-mod | 0.988× | 12/12 |

[Manifest](upstream-control-pilot/manifest.json), [runs](upstream-control-pilot/runs.jsonl), [summary](upstream-control-pilot/summary.json). These are appropriate local candidates for this small pair, not an exhaustive best-runtime search. N-gram is close to neutral in this small sample; no statistically established regression is claimed. The two tables have distinct timing paths and must not be used as a direct NodeLift-vs-upstream speed ranking.

## Large model: upstream kernel baseline only

The already available `Qwen3.8-27B-Q6_K.gguf` reports architecture `qwen35`; this is a hybrid model rejected by the current NodeLift verifier. Upstream llama-bench nevertheless provides a useful host reference:

| Kernel workload | Repetitions | Mean tokens/s | Sample standard deviation |
|---|---:|---:|---:|
| Prompt processing, 128 tokens | 3 | 183.491 | 0.829 |
| Generation, 64 tokens | 3 | 15.344 | 0.036 |

[Results](large-host-baseline/results.json), [model/build identity and memory/swap observations](large-host-baseline/manifest.json). This benchmark uses a synthetic token stream through a real model. It is **not chat latency, a distributed result, or proof that NodeLift supports this architecture**. Existing system swap usage is recorded; it was not assumed to be a clean isolated host.

## Correctness and integration evidence

[Versioned validation manifest and hashes](engine-validation-2026-10-31/manifest.json). GitHub CI passed Python 3.12/3.14 protocol tests, DistAI evidence checks and the adapter tests on the implementation commit.

- [29 native real-weight checks](engine-validation-2026-10-31/native-correctness-expanded.json): perfect/all-rejected/random partial acceptance, rollback, invalid IDs, context limits and close/cancel racing an active call.
- [Real-weight TLS loopback](engine-validation-2026-10-31/remote-loopback.json): valid proposals, all-wrong proposals, explicit worker failure and dropped response all produced the same 32-token target sequence. Error/drop each caused one counted fallback. This uses an emulated node and an injected short timeout.
- [Live gateway](engine-validation-2026-10-31/gateway-live.json): normal/streamed text equality, valid Unicode and cancellation on client disconnect. The first short-output cancellation attempt completed before disconnection; the final drill used an output long enough to remain active.
- [LM Studio adapter handler](engine-validation-2026-10-31/lmstudio-live.json): actual SDK Chat and generator code streamed a real NodeLift response. This does not exercise LM Studio's complete GUI/plugin runtime.
- 26 automated host/protocol/startup/HTTP-contract tests and three adapter stream tests passed. Stubbed HTTP tests are not model-performance measurements.

The [physical hotspot pilot](2026-10-31-xiaomi-hotspot/REPORT.md) remains separate: median HTTPS RTT approximately 6–9 ms, a pronounced tail in the 60 ms-paced group, and payload-dependent bandwidth. Native phone drafting, under-load RTT, long thermal sessions, battery cost and wired alternatives remain unmeasured.

## Decision

Retain host-only as the default. Do not route to a phone solely because it has spare RAM. Next discriminating work requires the updated native companion online and a qualified large target/draft pair. Report per-round committed tokens and full round time, exact output comparisons, TTFT, total completion time, rejected work and failures. No projection from 64 to 300 generated tokens substitutes for a real 300-token run.
