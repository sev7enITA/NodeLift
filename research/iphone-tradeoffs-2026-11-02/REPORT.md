# Physical iPhone draft-delegation results

2026-11-02. **The iPhone supplied usable draft tokens, but fixed phone delegation was slower than the Mac alone for the tested small target.** The original build also lost its session after repeated errors. An iOS correction and its subsequent evidence must be kept separate from that failure.

## Scope

The [plan](PLAN.md) was recorded before measurement. The Mac uses Qwen2.5 1.5B Instruct Q4_K_M as target and Qwen2.5 0.5B Instruct Q4_K_M as draft, context 2048, 8 requested host threads and 999 requested GPU layers. Draft width is 4 and the configured remote timeout is 10 seconds. The unchanged adaptive engine can shorten its probe deadline. The collector and target/native artifacts are fingerprinted in each raw record.

The physical iPhone 15 Pro Max reports iPhone16,2, iOS 27.2 and companion 0.2.12, with matching draft hash and fresh readiness during the three completed cells. These original cells used private development build 14. The user reported `Draft ready · Metal`, consistent with the source's default requested backend. This is not effective GPU-offload attestation. The heartbeat does not report the selected backend. iOS source defaults to 4 worker threads and context 2048; those settings were not independently read back from the phone.

Mac and iPhone were on the user-reported Xiaomi hotspot, with stable observed peer and host addresses during the completed cells. The iPhone reports Wi-Fi/hotspot. It also remained attached to the Mac for development access; this is not an unplugged battery/energy test. Radio band, actual PHY rate and transport isolation were not measured.

## Original build 14 results

Positive added time and TTFT change indicate worse latency. Ratios are medians of paired candidate/host durations, not ratios of separate medians. Completed-service timing includes fallback overhead. Each cell is a correlated period, not independent confidence evidence.

| Condition | Completed candidate / planned | Equivalent pairs | Median added total time | Median TTFT change | Median candidate/host ratio | Fallbacks | Accepted / proposed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| remote-adaptive-32 | 6/6 | 6/6 | -46.473 ms | 1.625 ms | 0.866x | 6 | 0/0 |
| remote-fixed-32 | 6/6 | 6/6 | 1,040.652 ms | 109.299 ms | 4.657x | 0 | 128/246 |
| remote-adaptive-128 | 6/6 | 6/6 | 66.421 ms | 4.903 ms | 1.088x | 6 | 0/0 |
| remote-fixed-128 | 0/3 | 0/3 | unavailable ms | unavailable ms | unavailablex | 1 | 0/0 |

There were **18 completed pairs**, with all 36 primary outputs matching by token hash, token count and finish reason. The fourth cell retained one invalid candidate attempt and five missing primary attempts. Its response completed through fallback, but connection drift invalidated the planned comparison. Eight warmup attempts are separate and excluded from primary counts. No failed attempt was silently replaced.

### Fixed 32-token budget

All six pairs completed without fallback. The median total candidate duration was **1,290.589 ms**, versus **233.934 ms** for the host-arm median. The median paired slowdown was **4.657x**, paired added duration **1,040.652 ms**, and paired TTFT deterioration **109.299 ms**.

The host accepted **128 of 246 received proposals**, about **52.0%**. The other 118 were not accepted. Acceptance demonstrates usable speculative proposals, not acceleration. Median accumulated remote wait was **1,029.326 ms**; it combines polling, transport and draft work. The worker's native execution time is not returned by this protocol, so these components cannot be separated.

### Adaptive cells

All 12 adaptive requests fell back after `remote_probe_timeout`, with zero accepted phone tokens. Median remote waiting was about 60 ms per request. At a 32-token budget, the signed median total difference was -46.473 ms; at 128 tokens it was +66.421 ms. **The negative observation is not phone acceleration:** no phone proposal contributed, and host latency varied across these short ordered measurements. Both are descriptive service timings under fallback, not clean delegated speedups. TTFT changes were +1.625 ms and +4.903 ms.

### Fixed 128-token budget and session failure

This cell was scheduled because the predeclared fixed-32 median paired ratio was below 5x and all six requests finished without fallback. It completed its two warmup requests, then the first primary candidate took **10,471.919 ms**, including **10,004.930 ms** of remote wait, and used host fallback. The post-run check detected an offline companion. The attempt is `invalid / post_run_scope_drift`; no paired speed result is computed.

The [allowlisted physical journal](session-diagnostics.json) records repeated session retries and a final failure. Its numeric error code 0 does not identify the exact HTTP error. Code inspection found a concrete failure mechanism: expected rejection of expired or superseded draft results was treated as a network error, and repeated rejections could exhaust the connection retry budget. This is consistent with the observed failure, but the journal alone does not prove every retry had that cause.

Private development build 15 distinguishes the two existing obsolete-lease rejection messages on the authenticated result endpoint. It records `draftDiscarded`, never retries or accepts that obsolete output, and continues polling. Unauthorized requests, invalid tokens, other endpoints and unknown errors retain their error handling. No host validation is relaxed. Swift integration tests exercise repeated obsolete results and a subsequent usable session. Physical follow-up results are reported separately below and cannot erase build 14's failure.

## Separate build 15 follow-up

The two follow-up cells were planned after the failure and before new measurement. They are kept separate from build 14, with the same target, draft, connection label, width and configured deadline. No failed original attempt is replaced.

| Build 15 condition | Completed pairs / planned | Median added total time | Median TTFT change | Median paired ratio | Fallbacks | Accepted / proposed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Adaptive, 32-token budget | 3/3 | +61.822 ms | -4.912 ms | 1.247x | 3 | 0/0 |
| Fixed, 128-token budget | 3/3 | +2,555.739 ms | +109.809 ms | 4.562x | 0 | 204/328 |

All six paired outputs match. The [physical journal](build15-session-diagnostics.json) records four discarded obsolete proposals, with no session retry/failure after readiness during these cells. The host still saw the phone online and draft-ready at the final check. This supports the fix in this short physical sequence; it does not establish sustained reliability or prove the cause of every original retry.

Fixed-128 accepted 62.2% of received proposals and completed without fallback, but remained slower than its paired host baseline. The median accumulated remote wait was 3,003.828 ms. Adaptive again abandoned the phone in every measured request. Neither mode demonstrates an acceleration in this model/connection scope.

Across original and follow-up evidence there are **24 completed pairs**, plus the retained interrupted cell with one invalid and five missing primary attempts. These periods and builds are not pooled for confidence estimates. [Build identity](build-identity.json) is recorded separately because the heartbeat and original collector scope contain version but not build number.

## Comparison with Xiaomi

| Original fixed-32 observation | iPhone, build 14 | Xiaomi, companion 0.2.8 |
| --- | ---: | ---: |
| Median paired candidate/host ratio | 4.657x | 134.949x |
| Median added total time | 1,040.652 ms | 34,763.884 ms |
| Median TTFT change | +109.299 ms | +8,321.121 ms |
| Accepted / received proposals | 128/246 | 128/250 |

The measured iPhone route had a much smaller penalty. This is **not a pure hardware ranking**: the iPhone requested Metal whereas Android's source requested CPU, companion builds differed, host load differed, and the Xiaomi was the hotspot provider in its test while the iPhone was a hotspot client. Both measured fixed routes were slower than their paired Mac baseline. See the [Xiaomi report](../phone-tradeoffs-2026-11-02/REPORT.md).

## Limits and reproducibility

Reported thermal state was nominal and battery snapshots were 100% during completed cells. These are contextual readings, not measured watts, joules or sustained thermal endurance. Host one-minute load varied approximately 10.6 to 14.1; this was not an exclusive laboratory workload. Memory pooling, larger-target capacity and a model-independent benefit remain unproven. Confidence intervals and an automatic routing recommendation are withheld.

Run `python3 research/iphone-tradeoffs-2026-11-02/summarize.py` to reproduce [RESULTS.json](RESULTS.json) and [TABLE.md](TABLE.md). Each raw session has a corresponding `.report.json`; the interrupted cell is retained with missing attempts. The [decision record](study-decisions.json) keeps the scheduling rule, failure and post-fix plan. Build/install details are in [iOS setup](../../docs/IOS_DRAFT_SETUP.md).

For this measured small-model scope, **use the Mac alone when response speed is the priority**. A useful next experiment is a larger resident target with matched host controls, after session stability is confirmed. Better draft acceptance alone cannot overcome a host baseline that is already much faster than the remote proposal route.
