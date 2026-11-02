# Physical phone performance and trade-offs

[Visual benchmark gallery](../visual-benchmarks-2026-11-02/README.md): paired timing, first-token delay, adaptive fallback and contribution charts.

2026-11-02. **The current Xiaomi draft-delegation path did not improve response speed in the tested model/connection scope.** Adaptive control contained the penalty by abandoning remote proposals, not by accelerating generation.

This phase consolidates [Impact v1](../../docs/IMPACT_BENCHMARK.md) at baseline commit `740705183028b57038b5b414a968dabb8de77f48`, extends its collector and executes the [frozen exploratory plan](PLAN.md). The native engine and mobile binaries were not changed. Results describe the current NodeLift route on one phone, not the maximum AI capability of the phone's hardware.

## Actual scope and coverage

- Host: M3 Max Mac, 64 GiB, Qwen2.5 1.5B Instruct Q4_K_M target, Qwen2.5 0.5B Instruct Q4_K_M draft, context 2048, 8 requested threads and 999 requested GPU layers. Actual effective offload is not attested.
- Phone: physical Xiaomi 25128PNA1C, reported Android 17/API 37 and companion 0.2.8; matching draft SHA-256 and engine readiness checked. The Android source loads the draft with `gpu_layers=0`; loaded-binary/SoC execution attestation is absent.
- Topology: user-reported Xiaomi hotspot to Mac, with stable observed host/peer addresses during each cell. The companion labels its transport as `other / not detected`; radio band, link rate and access-point behavior were not measured.
- **18 physical phone-versus-host pairs**, across three cells, plus **3 local-draft-versus-host control pairs**. All 42 primary attempts completed; all 21 paired output token hashes, token counts and completion reasons matched. Warmups are retained separately and excluded from these counts.
- Three fixed public prompts; 32/128 are output budgets, not a guarantee that every response reaches the budget. The longer cell includes natural early stops. All comparisons use their paired actual output.

## Observed results

Positive added time or TTFT change means worse latency. Ratios are medians of paired candidate/host total durations, not ratios of separate aggregate medians. Values include fallback overhead for completed equivalent-output pairs.

<!-- TABLE:START -->
| Condition | Completed candidate / planned | Equivalent pairs | Median added total time | Median TTFT change | Median candidate/host ratio | Fallbacks | Accepted / proposed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| local-fixed-32 | 3/3 | 3/3 | 113.447 ms | 31.050 ms | 1.504x | 0 | 64/123 |
| remote-adaptive-32 | 6/6 | 6/6 | 43.738 ms | 3.105 ms | 1.196x | 6 | 0/0 |
| remote-fixed-32 | 6/6 | 6/6 | 34,763.884 ms | 8,321.121 ms | 134.949x | 0 | 128/250 |
| remote-adaptive-128 | 6/6 | 6/6 | 87.604 ms | -4.789 ms | 1.121x | 6 | 0/0 |
| remote-fixed-128 | Not scheduled by rule | | | | | | |
<!-- TABLE:END -->

[Machine-readable summary](RESULTS.json) and [per-pair table](TABLE.md) are reproducible with `python3 research/phone-tradeoffs-2026-11-02/summarize.py`. Raw sessions and analysis reports are alongside this document. Each cell is one correlated collection period; the cells are not pooled as independent sessions. No confidence intervals or population-wide performance claim are supported.

### Fixed phone delegation

All six requests completed remotely with equivalent output and no fallback. The median candidate duration was **35,068.131 ms**, versus a paired-host duration median of **251.619 ms**. The median paired added duration was **34,763.884 ms**, with a **134.949x** paired slowdown. Median paired TTFT deterioration was **8,321.121 ms**.

The phone supplied **128 accepted proposals from 250 proposals received**: 51.2% acceptance, with 122 proposals not accepted. Acceptance is useful-work accounting, not speedup. The host still verified the output. The median accumulated remote wait was **34,740.971 ms**; this combines transport, polling and worker computation. The existing protocol does not return the worker's native timing, so those components cannot be separated from these records.

### Adaptive phone delegation

Every adaptive request completed with equivalent output, but every remote probe timed out and the engine continued on the host. No phone token was accepted in either adaptive cell. At 32 tokens, the median added duration was **43.738 ms** and the median paired slowdown **1.196x**. At a 128-token budget, the corresponding values were **87.604 ms** and **1.121x**.

Median remote wait was approximately **61 ms** in both adaptive cells. First text was emitted by the host before the exploratory remote probe. The small signed TTFT differences (+3.105 ms and -4.789 ms) are descriptive observations, not a demonstrated TTFT benefit. The adaptive behavior bounds damage under these conditions; it does not demonstrate acceleration or energy savings.

The zero proposed-token count in adaptive records means no proposals were accepted by the host protocol before the deadline. It does **not** mean the phone performed zero work: expired work may still execute or return late. Quantifying that discarded worker computation requires additional protocol instrumentation.

### Local speculation control

Moving draft generation onto the same Mac also lost on this small target: **113.447 ms** median added duration and **1.504x** median paired slowdown over three pairs. All outputs matched and no fallback occurred. This indicates that the current target/draft/batch combination carries overhead even before adding a phone connection. It is not a causal isolation of network cost: warm state, policy order and residency are not experimentally controlled.

The conditional fixed-128 cell was **not scheduled**, because fixed-32 exceeded the preregistered 5x slowdown threshold. See [the decision record](study-decisions.json). No unperformed 128-token fixed result is inferred.

## Trade-off matrix

| Dimension | Demonstrated observation in this scope | What it does not establish | Operational consequence |
| --- | --- | --- | --- |
| Single-response latency | Fixed phone drafting was substantially slower in all six pairs | A universal ranking of phones or all model sizes | Use host-only for this model and connection when latency matters |
| First-text latency | Fixed drafting delayed first text; adaptive emitted host text before probing | A statistically established small TTFT improvement from adaptive control | Avoid fixed remote drafting for interactive use in this scope |
| Service completion | All 18 phone-cell requests completed and matched their paired host output | Long-term reliability or semantic accuracy | Keep completion separate from successful delegation |
| Useful phone work | Fixed mode accepted 128/250 proposals; adaptive accepted none | Acceleration, effective FLOPS utilization or reduced whole-system work | Do not present contribution share as a speed benefit |
| Loss containment | Adaptive remote probes stopped at roughly 61 ms in these cells | A calibrated guarantee under other workloads or networks | Adaptive is preferable to fixed if experimentation with this route is required |
| Main-model capacity | No target-weight or KV-cache sharding was exercised or implemented | More addressable RAM for the main model | These tests cannot justify running a larger target by adding phone RAM |
| Phone memory footprint | Reported process snapshots approximately 656-684 MiB during phone cells | Peak memory, host RAM saved or independently measured process RSS | Reserve memory for the companion; do not count it as free extra host capacity |
| Energy | No calibrated meter was available | Joules saved, battery-life improvement or net energy efficiency | Energy remains unavailable |
| Thermal behavior | All returned snapshots said nominal | Sustained thermal endurance or absence of throttling between snapshots | No sustained-load qualification |
| Aggregate throughput | Not tested | More parallel independent requests per second | Requires a separate workload and execution mode |
| Other devices/transports | Not tested | iPhone, Oppo, Huawei, USB or Ethernet performance | Separate physical strata are required |

Battery snapshots were 85% in the first adaptive cell, 83-84% during fixed delegation and 83% in the longer adaptive cell. The phone also provided the hotspot and remained in use; percentage changes are coarse context and cannot be attributed to inference or converted into energy. Snapshot values can repeat because telemetry is cached. Host one-minute load averages varied roughly from 6.4 to 9.5 during phone cells, so this was not an exclusive-load laboratory experiment.

## Separate connection diagnostic

After the LLM cells, one standalone quick network diagnostic was requested. It reached the host's **timed_out** state after approximately 121 seconds and returned no samples. See [raw post-hoc status](posthoc-network.json). It is not a synchronized measurement of the LLM route and yields no valid RTT or bandwidth estimate. No retries or synthetic substitutions were used to make it appear successful. Network-diagnostic robustness remains unresolved.

## What to change or test next

1. Capture worker execution duration, queue/lease age, expired/late work and effective runtime configuration in both companions. Current `remote_wait_ms` is too broad to assign the loss to Wi-Fi, compute or scheduling.
2. Measure a compatible larger target with identical paired output before claiming the phone becomes useful. The current target is small and fast on this Mac. Existing larger files are not already qualified target/draft substitutions.
3. Test transport changes on the same phone and model under a controlled crossover protocol. Resolve the timed-out network diagnostic first; do not extrapolate the historical hotspot bandwidth.
4. Compare request-level admission decisions with per-request probing: avoiding repeatedly unprofitable probes may remove overhead. This is a proposal, not an implemented or measured gain.
5. Evaluate independent-task throughput and capacity sharding separately. They solve different problems and are not evidence of single-response acceleration.

The current practical decision is **host-only for speed in this measured scope**. Keep adaptive protection for exploratory delegation. Hardware reuse remains a design objective; these results do not establish a performance benefit from the current phone path.

## Collector and UI consolidation

The collector now fingerprints the policy and draft width, retains decision blocks and captures before/after context. It fixes the wall-clock endpoint used for discontinuity detection so an admin lookup after streaming cannot create a false clock anomaly. The dashboard displays completed-service time/TTFT including fallback separately from clean no-fallback metrics, making adaptive overhead visible even when no phone proposal was usable.

Automated checks validate instrumentation and rendering; they do not certify physical performance. No mobile rebuild or new native inference implementation is included in this phase.

Validation: 138 host tests, seven desktop JavaScript suites, generated localization checks and documentation validation across 95 pages/398 local targets passed. All four saved cell reports were recomputed from raw sessions and matched; the 21 primary output pairs were reconciled against saved session records. Live Measurements displayed the all-fallback adaptive report with unavailable clean timing and retained completed-service overhead.
