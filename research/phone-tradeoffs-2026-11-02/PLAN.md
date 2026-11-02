# Physical phone trade-off study: frozen exploratory plan

2026-11-02. Continue from the [Impact pilot](../impact-2026-11-02/REPORT.md). Purpose: establish observed gains or losses and their costs for the available physical phone and specific native model/connection. No universal device ranking or claim of statistical qualification.

## Conditions fixed before new measurements

- Host: existing M3 Max, native Qwen2.5 1.5B Instruct Q4_K_M target, Qwen2.5 0.5B Instruct Q4_K_M draft, context 2048, threads 8, requested GPU layers 999. Keep native engine unchanged. Effective GPU attestation remains absent.
- Phone: only a freshly online enrolled device with the matching draft ready. Record actual model, companion version, reported thermal state, battery and memory snapshots. Never replace a physical device with an emulator.
- Connection: Xiaomi hotspot to Mac while that topology remains actual. A changed address or observed session boundary stops the collection. Other transport types and phones are separate future strata, not inferred comparisons.
- Three fixed public prompts already in the collector; randomized balanced-as-possible AB/BA pairs; one unscored warmup pair per cell. Candidate node fixed before allocation. New collector records decision blocks and state snapshots.
- Primary workload: 32 output tokens; longer workload: 128 output tokens. Fixed draft block 4, configured remote deadline 10 seconds. Adaptive policy may tighten its deadline according to the unchanged engine.
- Separate native local-draft control identifies whether speculation is itself useful on this small target. This is not mobile acceleration and residency carryover remains a confound.

## Planned cells

1. Local draft versus host, 32-token budget, fixed policy, 3 pairs. Can run while the phone is unavailable.
2. Remote adaptive versus host, 32-token budget, 6 pairs. Capture rejected probes and fallback penalty as well as successful requests.
3. Remote fixed versus host, 32-token budget, 6 pairs. Retain all planned primary attempts and outputs.
4. Remote adaptive versus host, 128-token budget, 6 pairs. Tests whether the initial probe cost is amortized, without claiming independent thermal sessions.
5. Remote fixed at 128 tokens is conditional: execute 3 pairs only if the 32-token fixed cell has a delivered-service median slowdown no greater than 5x and at least half its requests finish without fallback. Otherwise record it as not scheduled by the predeclared resource rule, not as a measured result.

Resource/safety bounds: stop further phone load if it disconnects, reports severe/critical/emergency thermal conditions or battery below 20%, or the host configuration/artifact metadata changes. Each request retains the existing 300-second gateway bound. No automatic retries replace primary attempts. Failed warmup leaves a frozen missing plan. Missing phone availability is not a performance failure and does not justify a synthetic replacement.

Each cell is one correlated collection period. Running several cells consecutively does not create independent replications. Report descriptive paired values/ranges, output equivalence, delivered-service overhead, fallback count, accepted/proposed tokens, remote wait and effective adaptive decisions. Compare cells descriptively only; policy order, thermal drift and cache carryover preclude a causal cross-cell estimate.

## Trade-offs to adjudicate

- **Response speed:** client total duration and first-text arrival, same output and budget.
- **Reliability:** all planned attempts, output differences, explicit failures, fallback and missing slots.
- **Useful contribution:** accepted/proposed token counts and observed route. Acceptance is not speedup, FLOPS utilization or shared RAM.
- **Cost containment:** adaptive return to host can reduce losses without creating a gain. Report both statements independently.
- **Memory:** actual reported process memory and available memory snapshots only. No target sharding is implemented, so no claimed increase in maximum model capacity.
- **Energy:** unavailable without a proper meter. Battery percentage and reported thermal categories are context only, never joules or proof of thermal endurance.
- **Generality:** no result applies to untested phones, iOS, larger models, other hotspots or USB/Ethernet. Existing 27B/35B files are unqualified architectures and tokenizers and cannot be silently substituted for a compatible target/draft pair.

## Instrumentation correction

Before collecting this phase, capture wall-clock end at the same boundary as monotonic stream completion. The earlier collector sampled wall end after its final admin lookup, which could wrongly report a clock discontinuity when lookup was slow. A regression test simulates that delay. This correction changes bookkeeping, not the native engine or earlier recorded pilot durations.
