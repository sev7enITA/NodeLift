# Experimental knowledge base

No architecture replacement is selected here. This is a bounded hypothesis register, not a claim that every possible approach has been explored. Local speculative verification, resident task offload and model sharding solve different objectives.

| Case | Hypothesis / unusual variant | Bounded falsifier | Contract / status |
|---|---|---|---|
| 1. Placement | A continuously running remote draft with at most one queued block hides production behind verification | Compare matched standalone target, best local speculation, and real remote pipeline. Charge rejected suffixes, cancellation, resynchronization and late replies | This cycle simulates the ideal accepted-prefix path; physical pipeline still untested |
| 1. Placement | Node work can improve multi-request throughput even when one response becomes slower | Two independent clients, same quality and aggregate hardware budget; compare queue wait, p95 latency and completed requests per second | Proposed. Cannot substitute throughput for single-request latency |
| 1. Placement | Reuse exact prompt-prefix draft state across requests, with an immutable branch ledger | Alternate shared and unrelated prefixes; measure hit rate, retained RAM, KV rebuild and stale-prefix negative controls | Proposed. Prefix digest, model hash, tokenizer/settings, epoch and authorization must all match; no cross-model KV sharing |
| 2. Cost | Charging startup and rewind changes admission and reduces unnecessary drafting | Same outputs, prompts, precision and cap; compare old policy to charged policy, including whole-request time | Implemented in isolated research generator; measured below in the results report |
| 2. Cost | A short-horizon debt budget is more useful than acceptance ratio alone | Replay immutable cost traces with varied host calibration, then prospectively test frozen rule; log false admissions | Proposed. Trace replay cannot establish the counterfactual live timing |
| 2. Cost | Host can continue serial work while slow candidates arrive, then consume only prefix-matched suffixes | Arrival-injection harness with epoch fences; count useful candidates, stale work and host work duplicated | Proposed. Never double-count overlap or commit a draft token without target verification |
| 3. Envelope | An ideal producer reveals whether optimizing the draft/network has any room to help | Teacher-force immutable serial tokens through widths 1/2/4/8, record timings and all prediction differences | Locally measured, deliberately zero producer cost. Not deployable inference |
| 3. Envelope | A host-side n-gram or trie can be a cheaper candidate producer than a neural draft | Compare lookup + verification with neural draft on repetitive and novel held-out prompts | Proposed. Repeated spans are candidates, never trusted output; lookup CPU cost included |
| 3. Envelope | A retrieved historical continuation can amortize expensive drafting | Exact-prefix cache eligibility, eviction and privacy tests; compare hit/miss latency separately | Proposed. No output-quality relaxation and no benchmark prompt memorization |
| 4. Correctness | Batch shape changes target numerics even with identical input tokens and fresh state | Cross serial/batched history with current width 1/4; record raw and normalized argmax, populated KV and layer boundaries | Local diagnostic. A first divergent component does not prove a faulty kernel |
| 4. Correctness | Rebuilding serial KV eliminates accumulated history drift but leaves current-width effects | Fresh cache rebuild on the same committed prefix, followed by current width 1/4 | Included in the 2x2 diagnostic. Rebuild cost prevents calling it a free fix |
| 4. Correctness | Batch-invariant target reductions could preserve useful batching | Isolate and replace one primitive; compare against serial target across prompt lengths, cache lengths, dtypes and near ties | Proposed. No arbitrary logit-margin exemption; no blanket FP32 guarantee |
| 5. Quality | A scheduler can classify environment validity separately from runtime capability | Inject missing/invalid telemetry and thermal/memory/disk failures; retain all refusals | Implemented helper negative controls, not a full benchmark qualification system |
| 5. Quality | Resource pressure should be an explicit experimental factor, not hidden noise | Matched idle vs controlled load, power mode and thermal steady state, fixed workload blocks | Proposed. Current shared Mac is diagnostic, not isolated; no energy sensor claim |
| 5. Quality | A device is useful only in some context-length and concurrency regions | Sweep predeclared workload/context/concurrency cells, retain losses and report uncertainty per cell | Proposed. Avoid selecting only favorable cells or calling conditional gain systematic |

## Primary references and acknowledgements

- [Leviathan et al., Fast Inference from Transformers via Speculative Decoding](https://proceedings.mlr.press/v202/leviathan23a.html): speculative verification foundations.
- [Yan et al., Decoding Speculative Decoding](https://arxiv.org/abs/2402.01528): draft design and latency matter; general language quality is not the performance objective.
- [Speculation at a Distance](https://arxiv.org/abs/2606.25091): edge/cloud communication and multi-tenant tradeoffs under the paper's assumptions. Its environment is not this phone/hotspot setup.
- [ASPIRE](https://arxiv.org/abs/2609.17943): asynchronous mixed drafting/verification scheduling. Its reported results are not NodeLift measurements.
- [Thinking Machines, Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/): batch-invariant computation and reductions. This motivates investigation, not a diagnosis of a specific MLX kernel.
- [SDCP Internet-Draft](https://www.ietf.org/ietf-ftp/internet-drafts/draft-li-mlc-inference-acceleration-00.html): distributed speculative session/state contracts. A November 2026 work in progress, not an adopted standard or implemented NodeLift protocol.
- [Apple MLX-LM](https://github.com/ml-explore/mlx-lm), particularly installed version 0.32.2: reused generator under the retained MIT license. [Issue 1470](https://github.com/ml-explore/mlx-lm/issues/1470) is related evidence, not proof of our root cause.

These projects deserve credit for the ideas and implementation foundations. External reviewers' unverified references are excluded; see `review-adjudication.md`.

## Prioritized next experiment cards after the browser reviews

These priorities choose experiments, not an architecture replacement.

**A. Causal primitive intervention.** On the frozen diagnostic prefix, replace only the first-layer attention output projection with explicit per-token width-one calls. Preserve the serial reference, weights and prefix. Run interventions separately during history construction and the current forward; include an unchanged wrapper control. Check full logits, final argmax, populated KV and the next divergent component. A restored token supports only that intervention on that prefix. If the wrapper alters the width-one reference, record a changed contract and do not call it an equivalent optimization. If it passes, expand to a predeclared new-prefix set and measure the complete performance cost. Source/kernel inspection, rather than a zero-padding result alone, is needed to establish the dispatch mechanism.

**B. Real cost surface with a noise control.** Execute genuine identical-code A/A trials, plus an actual fixed-width grid, in matched workload/context cells. Derive acceptance, startup, verification, rewind and completion costs from executed arms. Do not synthesize unobserved-width costs from one trajectory, and do not treat the old/charged aggregate ratios as raw A/A samples. Only then freeze an admission rule and test it prospectively. Record single-request latency and throughput separately.

**C. Bounded remote continuation, conditional on a fresh worker.** Verify current artifact/tokenizer identity and link measurements first. Allow at most one future candidate block beyond the one being verified; tag branch ancestry and expiry. Test delayed, duplicated, rejected and expired blocks with exact target commits. Log which physical resource progresses during each interval. A producer that waits for every commit is a stop-and-wait control, not the desired overlap experiment. The all-accepted trace simulation remains an optimistic control, not the admission evidence.
