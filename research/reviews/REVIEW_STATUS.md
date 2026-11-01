# External reviews — status and critical assessment

> Archived 0.1 review history, 31 October 2026. Both requested models later completed engine design and source reviews; adjudicated outcomes are in [ENGINE_REVIEW.md](ENGINE_REVIEW.md). Unavailability below describes earlier attempts only.

**Later update within the 0.1 phase:** Gemini 4 High completed a new NodeLift design review; GLM 5.3 Max again reported capacity limits. The first table preserves the initial session; later outcomes appear below. No external source review or hardware validation had been obtained at this checkpoint.

The owner requested GLM 5.3 Max and Gemini 4 High through the browser. The specified services were used with UI selectors verified; no model substitution was accepted. Technical questions and public sources were sent, without private AudioEnhancer code or credentials.

## Initial observed status

| Requested reviewer | Observation | Outcome |
|---|---|---|
| GLM 5.3, Max effort | First general request produced research notes without a conclusion; interrupted to focus on DistAI. A second targeted prompt received “Model is currently at capacity” / “Currently in peak hours” | **Final review unavailable**; suggestion to switch to Flash was declined |
| Gemini 4, High reasoning (4 Argon / High selector) | First request interrupted, second answer partial; then usage limit with reset shown as 17:45 and UI switched to Flash-Lite | **Partial review**, not coverage of the full DistAI dossier or approval |

Original transcripts: [partial Gemini](gemini-4-high-partial.txt), [unavailable GLM and prompt](glm-5.3-max-unavailable.txt). These are verbatim source evidence, including their original language. Gemini's text records what the reviewer said, **not verified facts**. GLM browser screenshot capture timed out; capacity status was read from the accessibility tree. No complete visual attestation is attached.

## Adjudication of Gemini suggestions

| Claim | Decision | Reason |
|---|---|---|
| Layer pipelines on slower nodes harm one sequence when the target fits the host | Accepted with explicit assumptions | Sum of critical-path durations, consistent with DistAI results |
| Compare remote drafting with local drafting | Accepted and strengthened | Include an asynchronous local baseline where supported |
| Universal NO-GO for all distribution when the model fits the Mac | **Not accepted as a general theorem** | Serial-pipeline assumptions do not cover all parallelism, speculation or hardware contention |
| Remote draft always loses unless local RAM is full | **Not accepted as demonstrated** | Assumes relative speed, equal verification cost and no overlap/contention benefit; requires measurement |
| Wi-Fi always has specific latency/bandwidth ranges and cable is always an order of magnitude better | Not used for sizing | No measurements from our phones/router; generic values are not evidence |
| exo actively supports macOS and Linux | Corrected | Consulted PLATFORMS.md listed Apple Silicon macOS Tier 1 and Linux Planned |
| distributed-llama spends 90% in busy-wait on these nodes | Rejected | No supporting benchmark of this configuration |
| iOS always offers approximately 4–6 GB per app | Rejected as a rule | Depends on model, OS, entitlement and memory pressure; no universal budget |
| BGContinuedProcessingTask is not a permanent daemon | Accepted with Apple documentation | Manage resources/lifecycle without categorically denying supported background GPU use |

GLM's general attempt correctly recognized some platform/RPC limitations but did not deliver a complete evaluation. The dossier's conclusions are not attributed to that model; DistAI findings come from our source inspection and reproducible recalculations.

## Closure needed at that checkpoint

The targeted prompt in the GLM file and three assessment documents could be resubmitted to both models: check causality/baselines, challenge E1/E2/E3, inspect exact sampling and iOS lifecycle, and identify prior work limiting novelty. Critically adjudicate responses and record corrections. Model agreement cannot replace device tests.

## NodeLift follow-up after device inventory

Verified selectors: Gemini **4 Argon / High** and GLM **5.3 / Effort Max**. The prompt described DistAI findings, owner-reported devices, hotspot topology and qualification-companion design. It included no credentials, private addresses or AudioEnhancer code.

- [Gemini original prompt and completed answer](gemini-4-high-nodelift-followup.txt).
- [GLM original prompt and renewed unavailability](glm-5.3-max-nodelift-retry.txt); no Flash substitution.

Gemini revised its earlier absolute conclusion, recognizing autonomous asynchronous drafting as a hypothesis to compare with the strongest local draft. It also corrected exo/Linux and recognized LM Studio generator plugins. This reviewed the described design, not implemented source files.

| New finding | Treatment |
|---|---|
| Closely spaced measurements hide radio wake effects | Accepted: Android/iOS `network_paced` job, 200 RTTs per requested 0/30/60 ms pause; separate groups |
| N=32 weakens p95 | Statistical limitation accepted; literal “cannot calculate it” rejected. Empirical percentile is calculable but uncertain; quick test labelled diagnostic |
| Different connections/TLS/stacks confound comparisons | Accepted: server connection IDs recorded in RTT samples; explicit Android disconnect after full response removed. Identical stack reuse not assumed |
| 256×256 matvec does not measure DRAM bandwidth or LLM speed | Accepted and disclosed in UI/docs; no tokens/s predictor based on this test |
| Host asyncio, Android OkHttp | Corrected: implementation used ThreadingHTTPServer and HttpsURLConnection; reviewer had no source and did not verify these details |
| connectedDevice necessarily requires USB/Bluetooth | Rejected: Android documentation includes network connections with permission prerequisites. Runtime OEM behavior remains to be checked |
| Universally exclude hotspot above 4 ms / 3× jitter | Not adopted: break-even depends on job, target and baseline; no device evidence supports the absolute threshold |
| Fixed 48/54 GiB Mac limits and precise radio wake times | Not treated as observations; measure allocatable memory and timing |
| Harmony cannot be qualified without SDK/device | Accepted: source candidate only; no HAP or verified compatibility claim |

At the end of this historical phase, the final GLM Max review, independent source inspection, physical iOS/Harmony installation/signing and measurements across all five phones remained open. Compilation and protocol tests did not close them. Later engine-review progress is recorded separately at the top of this page.
