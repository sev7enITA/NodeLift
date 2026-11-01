# ExpandMyHW — proposed experimental protocol

Preliminary version, 31 October 2026, written before hardware results were collected. Freeze the protocol after device inventory and before observing decisive results. The thresholds below are engineering proposals to make “clearly outperform” measurable, not predicted performance or thresholds already approved by the owner.

Later that day, the [first physical Xiaomi/hotspot diagnostics](research/measurements/2026-10-31-xiaomi-hotspot/REPORT.md) were collected. This transport/synthetic-CPU pilot with an exploratory repeat is not the end-to-end benchmark or a test of the gates below.

## Primary question and controls

**Does adding one or more phones make a single conversation with the same target materially faster than the strongest practical local configuration?**

Baselines to measure and publish:

| ID | Configuration | Purpose |
|---|---|---|
| B0 | Host target only, accelerated backend and tuned settings | Gain over optimized ordinary execution |
| B1 | Host target + strongest compatible local draft | Avoid attributing speculation alone to networking |
| B2 | B1 with local overlap/asynchrony, where supported | Control for a better pipeline also available locally |
| D1 | Host target + autonomous phone draft, synchronized blocks | Isolate network costs and delegation benefit |
| D2 | D1 with overlap and cancellation/rollback | Measure, rather than assume, asynchronous benefit |
| P1 | Same target distributed by layers, as a DistAI reference | Negative/positive control depending on host capacity |
| C0/C1 | Target exceeding host capacity: local out-of-core / resident remote shards | Separate capacity experiment |

If the backend lacks a local option, document it and narrow the claim. Do not claim “beats every local solution” after testing only B0. Use comparable tuning budgets and separate tuning from test data.

## Identity and conditions to record

- Computers/phones/tablets: model/SoC, physical and process-usable RAM, OS/build, backend, drivers, power, temperature/thermal state, battery and concurrent apps.
- Target/draft: repository, immutable revision, SHA-256, quantization, complete tokenizer, chat template, context, KV dtype, cache, sampler, seed, unchanged expert count/routing.
- Runtime: full commit, build flags, patch hashes, actual backend, offloaded layers, threads, batch/ubatch, flash attention and prompt cache. Verify no unintended CPU fallback in any phase.
- Network: AP/router, band/channel/negotiated mode, distance/obstacles, peers and concurrent traffic; USB ports/cable/hub, adapter/switch. Replace private identifiers with anonymous IDs in published logs.
- Policy: no cloud inference or downloads during trials; models already local for warm runs. Time cold loading separately.

## Phase 0: transport and capacity before a full runtime

Test the same phone over available Wi-Fi, USB networking, Android laboratory ADB and compatible Ethernet. Measure both directions and full duplex, with one and multiple simultaneous peers.

Indicative messages: 64 B, 4 KiB, 16 KiB, 64 KiB, 1 MiB, 16 MiB, plus sustained weight transfer. Replace or supplement these with actual tensor/block sizes for the selected model. Record application latency p50/p95/p99, goodput, loss/errors and queueing; distinguish RTT from one-way time. Without synchronized clocks, do not subtract timestamps from different hosts as though synchronized.

Repeat with idle radio, continuous traffic and contested networking; compare keepalive on/off and its energy cost. Do not use the best ping or fastest copy as the per-token cost. Measure loading, peak RAM and pressure after 30 minutes; do not deliberately force OOM on the owner's working computer.

## Phase 1: discriminating microexperiments

### E1 — autonomous draft, one chat

A phone hosts the entire draft and proposes blocks k=1/2/4/8/16, restricted to safe supported values. The host verifies and commits; contexts and proposal sequences carry IDs/versions. Start greedy. Per block, measure draft, transfer, wait, verification, accepted tokens, rollback, actual bytes and discarded work.

Compare D1/D2 against the strongest B0/B1/B2 on the same workload. Acceptance varies with task, context and position. Do not tune exclusively on a repetitive numerical prompt. Draft-to-target speed ratio is necessary but insufficient.

**Early feasibility stop:** if even an optimistic bound cannot beat the baseline, explicitly listing omitted costs, do not build the plugin for that combination. Beating the bound still requires an end-to-end trial. For non-greedy sampling, measure the exact protocol and verify acceptance/rejection and residual sampling; sending only token IDs does not establish equivalence.

### E2 — capacity without reloading weights every token

Select a target/context that actually exceeds host-available memory. Compare C0/C1 without changing model identity; record paging, SSD I/O, loading, TTFT and decode. Do not use poorer quantization or fewer experts only for the cluster.

**Stop:** insufficient mobile/KV memory, frequent restarts, or remote cost exceeding the measured out-of-core path. If C0 cannot start, report new capacity and absolute C1 times without an invented speedup ratio.

### E3 — transport and policy controls

Repeat the strongest D/P configuration on the same nodes, changing only transport. Compare all nodes, planner-selected subsets and host alone. Introduce network contention, observed throttling and node departure. Count detection, replanning and context-reconstruction time.

**Stop:** benefit exists only in the first minute, disappears at steady state, or requires manual exclusions the planner cannot reproduce. Do not hide poor routing by deleting the run.

## Phase 2: end-to-end benchmark

- Short/medium/long prompts, initially about 512/2048/8192 tokens where supported; measure actual tokens after templating. Fixed 128/512-token outputs for speed, natural output separately for quality/EOS.
- Include coding, reasoning, Italian/English text and long summarization; freeze data with hashes. A performance set does not replace a broad quality suite with edge cases and inspectable outputs.
- Separate single-conversation/no-concurrency and multi-user/queue tracks. The second cannot satisfy the primary criterion.
- Declare cold/warm caches and separate prompt-cache hits/misses. Prevent accidental prompt reuse from favoring a configuration.
- Randomize configuration order and pair comparisons by prompt. Block sessions over time with comparable initial conditions. Run at least 30 minutes for sustained thermal state.
- Initial plan: at least 30 test prompts and 5 paired repetitions for the finalist, across multiple sessions. Use a pilot to estimate variance and adjust sample size **before** the final test. Thousands of correlated tokens are not thousands of independent observations.
- Report medians, p95 and 95% bootstrap intervals clustered by prompt/session, plus individual cases, timeouts, failures and justified exclusions. Inconclusive results need more evidence, not a favorable claim.

## Proposed metrics and gates

| Dimension | Definition | Proposed criterion |
|---|---|---|
| Primary speed | Generated tokens / decode time at controlled output; paired comparison with strongest local baseline | Median speedup at least 1.30×; lower 95% CI above 1.10× |
| Overall experience | Submit to last useful token, cold/warm separate | At least 20% median reduction on the preregistered primary track |
| Latency tail | p95 inter-token/response time, including waits between bursts | No regression above 5% against baseline; uncertainty reported |
| Startup | Client-observed TTFT, including networking and scheduling | No warm regression above 10% on primary track; cold reported separately |
| Sustained behavior | Same metrics in final third of a run ≥30 minutes | Speed gates continue to pass |
| Quality | Greedy and predefined numerical tolerances; exact sampling and task suite | No hidden target/expert/context changes; explain regressions and preregister criterion |
| Energy | Measurable total host + node + network energy per response/useful token | Publish even if worse; product energy threshold remains to be agreed |
| Reliability | Correct completions, timeout, replay, cancellation, disconnections | No corrupt response or unverified committed token; explicit recovery costs |

A 1.30× speedup corresponds to about a 23.1% reduction in that phase's duration, not 30%. Metrics can diverge: bursts may improve tokens/s while harming smoothness. Winning one mean while hiding the rest is not a pass.

To claim “outperforms DistAI,” reproduce a comparable configuration on the same hardware with an accelerated build and fair tuning. Separate backend-update gains from runtime gains. If DistAI does not support a device, report additional coverage, not speedup against a nonexistent baseline. Do not use 3.9 tokens/s on an older PC as the M3 Max comparator.

## Minimum retained evidence

Immutable run manifest; per-request and per-block JSONL; monotonic timestamps; token/byte counts; outputs/hashes for nonsensitive prompts only; host/mobile metrics; network conditions; errors; confidence intervals and analysis scripts. Execute generated coding outputs in an actual sandbox: `python -I` alone is insufficient.

Publish favorable and negative results together. A simulation, theoretical-bandwidth estimate or external model review is not a hardware benchmark.
