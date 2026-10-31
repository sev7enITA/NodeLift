# Engine optimization: Jev/System One and local-project lessons

31 October 2026. Experimental source update after v0.2.1; existing mobile downloads are unchanged. This work optimizes the host engine and its delegation policy. It does not qualify pooled RAM, large hybrid models or physical-phone acceleration.

## What was studied

| Source | Useful lesson | Applied in NodeLift | Boundary |
|---|---|---|---|
| TypeSafe Jev / System One | Small, typed decisions over explicit state; separate a decision from its execution | `DraftDecision` records host/draft route, reason, observations and measured costs | A deterministic numeric heuristic, **not a Jev model integration**, learned policy or calibrated confidence |
| AudioEnhancerMAX cluster manager | Capability-aware delegation, explicit local fallback, worker/transport timing | Keep target authority; count remote failure and include proposal/verification/publication cost | Audio DSP chunks are independent; autoregressive LLM tokens are not. Equal audio chunks do not justify equal LLM layer partitions |
| AudioEnhancerMAX timing engine | Bounded recent observations and distinction between cold work and warm work | Request-local bounded timing windows; defer draft loading/prefill into the first adaptive probe | No transplantation of audio timing estimates or confidence labels into LLM speed claims |
| myTrader Jev / Decision-1 study | Semantic classification, deterministic arithmetic and action authority have different jobs | Numeric break-even remains code; no cloud call or prompt transfer is needed to decide whether a measured path loses | Existing research is not evidence of a live Jev deployment |
| myTrader resource/progression controls | Detect cloud-only resources; require explicit evidence and retain missing outcomes | Local-source provenance, failed/mismatched benchmark denominators and explicit qualification limits | No private financial data or full private project source copied or published |

The [source identity manifest](source-manifest.json) records the actual local files inspected. Some MakeMyVoice files were cloud-only placeholders and were not read; no claim of a complete audit of every local project is made.

Primary Jev documentation: [introduction](https://docs.typesafe.ai/introduction), [models](https://docs.typesafe.ai/models), [confidence](https://docs.typesafe.ai/confidence), [routing](https://docs.typesafe.ai/patterns/confidence-routing), [documented jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13). The official model list identifies `jev-1.14.0`, released 14 October 2026, and a hosted API. No official local model weights were established in this study. Confidence derived from a distribution does not itself establish correctness on our scheduling workload. Vendor benchmark numbers were not treated as NodeLift evidence.

## Changes implemented

1. **Greedy argmax cache.** Retain the selected token instead of copying a complete logit vector and scanning it again. Finite-value validation, first-max tie handling and KV synchronization remain in the native core. This is a lower-overhead greedy path, not a new sampler.
2. **Measured adaptive control, opt-in.** Four useful host tokens establish a local cost estimate. Two initial proposal rounds are allowed, with a one-round stop for a very costly probe. Total round cost per committed token must improve on the host median by at least 10%. Continued delegation is re-evaluated; loss/failure returns to host for the rest of the request. History resets for each request. The first cold local probe pays draft loading and prefill; a very short request need not load the draft at all. Remote exploratory deadlines are clamped to measured host cost and the configured ceiling. A timeout cancels the lease, and a late reply cannot commit tokens.
3. **Context lookup.** An incremental index of committed 3–8-token sequences proposes a continuation of the longest matching suffix. Up to 16 proposals are still target-verified. A lookup miss takes the ordinary host path. No second model is needed. [Prompt lookup decoding](https://github.com/apoorvumang/prompt-lookup-decoding) is established prior art; this implementation is not claimed as a new algorithm.
4. **Integration and evidence.** Dashboard and LM Studio generator expose lookup and fixed/adaptive control. API fields are documented in [INTEGRATIONS](../../docs/INTEGRATIONS.md). Stop checks prevent a completed proposal from entering verification/publication after an observed cancellation. Per-round records include the decision, effective deadline, native timing and total round timing.

Host-only and fixed control remain defaults. Node selection and block size remain manual. The adaptive policy is deliberately small and inspectable. A cold probe can still be expensive, an early host estimate can become stale, and a heuristic window is not a statistical confidence interval. First-token latency and complete-request cost must be considered separately from warm generation throughput.

## Benchmark design

Frozen baseline: `5826468a0b2e27a4f63bfc69f94221012535193d`. Candidate implementation: `2063d237c658b8a070df86e5e34d01789de7cbf1`. Same native dependency pin and real Qwen2.5 1.5B/0.5B Q4_K_M weights. M3 Max, 64 GiB, Metal, 8 threads, context 2048, greedy, block 4, up to 96 output tokens, EOS respected.

Seven arms: baseline host, baseline fixed local draft, optimized host, optimized fixed local draft, adaptive local draft, lookup, adaptive lookup. Eight fixed prompts, two repetitions per arm, 112 calls in a seeded randomized interleaving. Two persistent processes retain their model pairs; only one performs inference at a time. Warmup/model loading is excluded from the paired elapsed-time ratio; `request_total_ms`, load/prefill/TTFT and individual block costs remain in raw records. This is not a cold-start memory benchmark. Background desktop load and thermals were not isolated.

The six general prompts are reused from the earlier pilot, so this is not an independent held-out study. Two repetition/copy prompts form a separate exploratory subgroup, not a basis for a general speedup headline. One repetition request actually terminated after nine tokens; its requested length must not be substituted for the actual generated length.

A speedup is comparator elapsed time divided by candidate elapsed time for the **same prompt, repetition and actual token-ID list**. Failed/mismatched runs remain in the denominator and the raw data, but never enter a same-output speedup distribution. The report includes the pair count for each comparator. Neither faster generation of a different answer nor adaptive policy selection establishes semantic quality. Same-output eligibility is itself an outcome of the experiment: these conditional medians are descriptive and cannot be promoted to a workload-wide causal speedup. The exact-pair denominator must travel with each ratio.

## Frozen-source results

All 112 calls completed. Optimized host, adaptive local draft, lookup and adaptive lookup each matched baseline host token IDs in 16/16 comparisons. Baseline fixed draft and optimized fixed draft each matched in 14/16; the same four drift cases remained. The harness **exited 1 for token drift**, not as a fully passing correctness qualification.

[Final manifest](../measurements/engine-optimization-2026-10-31/final/manifest.json), [raw runs](../measurements/engine-optimization-2026-10-31/final/runs.jsonl), [all pair counts and ratios](../measurements/engine-optimization-2026-10-31/final/summary.json), [file hashes](../measurements/engine-optimization-2026-10-31/final/hashes.json). The manifest verifies source bytes for the listed benchmark dependencies against the source commit; unrelated documentation changes are outside that check. The earlier [112-call pilot](../measurements/engine-optimization-2026-10-31/pilot/NOTE.md) is retained separately with a corrected same-output summary.

General prompts, 12 runs per arm. Ratios above 1 favor the candidate; all ratios below compare identical token lists:

| Arm | Exact outputs vs baseline host | Median vs baseline host | Median vs old fixed draft | Eligible pairs vs old fixed draft |
|---|---:|---:|---:|---:|
| Optimized host | 12/12 | 1.023× | 1.194× | 10/12 |
| Optimized fixed draft | 10/12 | 0.823× | 0.999× | 12/12 |
| Adaptive local draft | 12/12 | 0.961× | 1.149× | 10/12 |
| Context lookup | 12/12 | 0.975× | 1.186× | 10/12 |
| Adaptive context lookup | 12/12 | 0.956× | 1.185× | 10/12 |

Adaptive local drafting reduced the penalty relative to old fixed local drafting by a median speed ratio of **1.149× on ten eligible general-prompt pairs**, while remaining **0.961× relative to host-only on twelve pairs**. This is an improvement to a losing delegation path, not a general host acceleration. The optimized host's 1.023× is a small exploratory difference with no isolated causal estimate or confidence interval.

The repetition subgroup has only two prompts × two repetitions. Lookup/adaptive lookup medians vs baseline host are **1.594× / 1.688×**, 4/4 exact pairs each. On the concrete 53-token repeated-text copy prompt, lookup ratios were **1.838× and 2.061×**; adaptive lookup **1.925× and 1.940×**. The other request ended after nine tokens despite asking for eight lines; it is not evidence that the model obeyed that instruction. These narrow gains must not be presented as general-language or phone speedups.

For general prompts, median first committed-block latency was 31.7 ms for old host, 65.3 ms for old fixed draft and 32.3 ms for adaptive draft, with models resident. Cold model loading is excluded from those TTFT values; it remains in request-total accounting. No cold-start performance result is claimed from the fake-clock scheduling tests.

## Validation

- 40 automated host/protocol/HTTP/scheduling/benchmark tests passed, including independent lookup oracle, cold-load accounting, cancellation during load/proposal, stale lease rejection and unequal-output exclusion.
- 29 real-weight native checks passed on the unchanged optimized native build; [evidence](../measurements/engine-optimization-2026-10-31/validation/native-correctness.json).
- Five real-weight TLS loopback cases passed, including adaptive expiry and rejection of a late reply; [evidence](../measurements/engine-optimization-2026-10-31/validation/remote-loopback.json). This is an emulated node, not a smartphone result.
- LM Studio TypeScript build and three stream tests passed. [Live lookup/adaptive gateway](../measurements/engine-optimization-2026-10-31/validation/gateway-lookup-adaptive.json) produced equal normal/streamed text and cancelled on client disconnect; the [actual SDK adapter handler](../measurements/engine-optimization-2026-10-31/validation/lmstudio-lookup-adaptive.json) streamed real weights through those new controls. Dashboard lookup/adaptive generation completed. These do not qualify the full LM Studio GUI runtime.
- [GLM review, Gemini unavailability and adjudication](REVIEW.md). No external-model approval substitutes for measured validation.

During development an idle keepalive caused a loopback test to disconnect after slow startup; the test now opens a fresh heartbeat connection while the worker still reuses its TLS polling connection. A unit-test attempt failed transiently while local cloud-backed reads were stalling; its first error detail was not captured. The discriminating test and full suite passed afterwards. An attempted final benchmark was stopped before inference because repository status was waiting on unrelated cloud files; the subsequent run uses explicit source-byte identities. These attempts are not counted as successful performance runs.

## Numerical limitation found at 96 tokens

The pilot found four mismatches, all on the Italian latency prompt in fixed local drafting: two baseline and two optimized runs. The first differing choice is token 75 (one-based; index 74), beyond the previous 64-token qualification. Target-only selected token 1853 while fixed batch verification selected token 13. Baseline and optimized fixed-draft outputs agree with one another: the scalar argmax cache is not the demonstrated cause.

This is a counterexample to universal batch/single greedy equality for the existing verifier/backend configuration. Prior 64-token sample results remain historically valid; they do not extend to arbitrary lengths. The adaptive/lookup paths also use batch verification and do **not** repair this numerical limitation. Matching a finite sample is not proof of universal equality. The benchmark intentionally exits nonzero when any arm drifts, retaining all data for inspection.

## Reproduction

Build the current native core with `scripts/build-native.sh` and fetch the pinned control weights with `scripts/fetch-control-models.py`. Prepare a separate baseline source directory at the baseline commit (outside a cloud-placeholder directory), build its native library, then copy its `host/nodelift/*.py`, `native/core.cpp`, `native/core.h`, `native/llama.lock` and library into `artifacts/optimization-baseline/`. Name the library `libnodelift-baseline.dylib`; write `manifest.json` with `source_commit` and SHA-256 values under `files`, as in the published baseline manifest. This records the rebuilt binary's identity rather than pretending it must hash identically on every toolchain.

```sh
PYTHONPATH=host python3 -m unittest discover -s host/tests -v
python3 scripts/check-native.py
python3 scripts/check-remote-loopback.py
python3 scripts/benchmark-optimization.py --output artifacts/optimization-repeat
cd adapters/lmstudio && npm test
```

Use a new output directory for every run; the benchmark refuses to overwrite prior evidence. Inspect the nonzero token-equivalence result before making any performance claim. Public data uses only the listed synthetic prompts and model basenames; model weights, private prompts, paired-device keys and private runtime logs are excluded.

## Remaining limits

No physical phone participated in these engine benchmarks. The Xiaomi was offline during the final GUI check and still reported the earlier qualification companion. No Android/iOS artifact was rebuilt in this update. Large compatible targets, sustained mobile inference, energy cost, under-load Wi-Fi/wired comparisons, context-delta transport and multi-node capacity sharding remain separate work. Neither this optimization nor the Jev study establishes superiority over every runtime in the comparison atlas.
