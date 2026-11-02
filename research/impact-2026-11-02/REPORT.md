# NodeLift Impact: implementation and physical pilot

Date: 2026-11-02. This is development evidence, not a qualified performance claim or a benchmark leaderboard.

## Delivered policy

See [NodeLift Impact v1](../../docs/IMPACT_BENCHMARK.md). The analyzer reports paired time saved, client TTFT change, full-denominator completion and output-equivalence reliability, measured energy availability, and session-cluster uncertainty. No automatic routing promotion is enabled.

The report and measurement schema are original NodeLift integration work using established statistical methods. Authorship: Fabrizio Degni, with implementation assistance and the model reviews documented below. No patentability, mathematical novelty or superiority over another engine is asserted.

## Physical phone pilot

Host: the user's M3 Max Mac, 64 GiB. Companion: Xiaomi 25128PNA1C, Android 17/API 37, reported app 0.2.8, draft ready. Connection: the Xiaomi provides the hotspot to the Mac. Local native target: Qwen2.5 1.5B Instruct Q4_K_M; draft: Qwen2.5 0.5B Instruct Q4_K_M. Context 2048, 8 requested threads, 999 requested GPU layers, fixed draft width 4, remote timeout 10 seconds. Requested GPU layers do not attest actual offload.

Three public prompts, 32 output tokens each, one unscored warmup pair, balanced-as-possible randomized AB/BA order. One continuous session, no cool-down or independent-session qualification. Effective loaded companion binary, host residency and background-load control were not attested.

| Pair | Mac total | Delegated total | Mac TTFT | Delegated TTFT | Candidate result |
| --- | ---: | ---: | ---: | ---: | --- |
| 0 | 300.592 ms | 34,099.601 ms | 46.885 ms | 3,809.736 ms | Completed remotely, 21 accepted draft tokens |
| 1 | 413.672 ms | 10,298.359 ms | 79.385 ms | 10,088.201 ms | Timeout and host fallback, zero accepted draft tokens |
| 2 | 384.032 ms | 48,589.177 ms | 57.887 ms | 9,758.050 ms | Completed remotely, 20 accepted draft tokens |

All three output token hashes, counts and completion reasons matched the paired Mac runs. Both arms completed 3/3 requests. The candidate completed without fallback in 2/3. The clean paired median saved time was **negative 41,002.077 ms**, and TTFT change was **positive 6,731.507 ms**, over the two eligible pairs. The fallback pair is excluded from the clean estimate but retained in reliability and the separate delivered-service comparison.

These observations show no speed benefit in this pilot. They do not establish a population regression estimate, universal phone performance or the source of every delay. `remote_wait_ms` combines device work, transport and polling; it must not be labeled pure network latency. One session is insufficient for confidence intervals. No power meter was available; energy is unavailable.

Artifacts:
- [Physical pilot session](xiaomi-pilot.json)
- [Physical pilot analysis](xiaomi-pilot.report.json)
- [Mac versus Mac collector control](mac-control.json)
- [Control analysis](mac-control.report.json)

The phone pilot was collected during development, before adding explicit start/end monotonic fields, clock-discontinuity checks, artifact-metadata drift checks and collector file hashing. It remains a labeled pilot, not evidence that those later guards passed on a phone. The final collector was exercised with a real host-versus-host control; all six planned control runs completed with equal paired outputs. Control data is never phone acceleration evidence. The analyzer can read this pilot without treating its missing provenance as attestation.

## Independent model methodology reviews

Both requested services were used through their logged-in browser interfaces with a sanitized methodology description, not private tokens, raw diagnostics, user prompt history or personal files.

- **GLM 5.3 Max:** the first response was generated with the interface's Flash model despite the initial selection. That response is not represented as a GLM 5.3 Max review. The model selector was then verified as GLM 5.3, Max effort retained, and a second request received a completed independent review. It emphasized missing-data defaults, three-way blocked/inconclusive/regression handling, run-ID duplication, artifact drift, fallback denominators, session pseudoreplication, degenerate bootstrap intervals and unattested GPU/residency.
- **Gemini 4 Argon, High reasoning:** verified selector `Argon Alta`. The first request was interrupted; the follow-up completed a substantial methodology review. It emphasized conditional-selection bias, SSE event definitions, thermal/order carryover, connection-epoch changes, full-system energy scope and independent sessions.

These were methodology reviews. Neither model independently navigated the final implementation, operated the physical phone, authenticated power measurements or certified the code. The dashboard received a separate implementation/evaluation pass and automated UI checks.

## Adjudication

| Finding | Implemented response | Remaining qualification |
| --- | --- | --- |
| Survivor-only latency can hide bad service | Clean latency and fallback-inclusive delivered-service latency are separate; all planned attempts remain in reliability | Censored/deadline utility and unconditional production benefit are not estimated |
| Missing information can silently become a pass | Explicit gates, unavailable values, persistent `qualified_recommendation=false` | Runtime effective-offload/residency attestation is absent |
| Repeated tokens or loops are not independent samples | Whole-session resampling; no interval below 10 clusters; duplicate runs/sessions rejected | Physical independence remains unverified; file names cannot prove it |
| Degenerate intervals imply false precision | Identical bootstrap bounds yield null plus a degeneracy flag | Small-cluster percentile coverage remains approximate |
| Token mismatch is not cosmetic | Mismatch is retained, counts against verified equivalence and blocks a speedup claim | Equality does not establish semantic accuracy |
| Fallback success is not device acceleration | Separate fallback counts and service metrics; no clean-time credit | Scheduler cost optimization is deferred |
| Meter windows/components can be incomparable | Same source/scope/components, complete window coverage, finite samples, no extrapolation | Instrument calibration, charging and clock alignment need physical validation |
| Unequal-duration energy needs an estimand | Explicit energy-to-completion per task | Equal-horizon idle-tail energy is a different unimplemented protocol |
| Cold restart/thermal washout suggested | Warmup and uncontrolled residency are recorded and qualification blocked | Collector does not reset another process or assert thermal recovery |
| BCa/10,000 resamples suggested by Gemini | V1 deliberately uses documented percentile bootstrap with 2,000 replicates, isolated seed and no qualification claim | BCa, simultaneous inference and holdout protocols remain future work |

No suggested formula was adopted solely because a model supplied it. In particular, a confidence interval crossing a decision threshold is inconclusive; it is not a demonstrated regression. Repeated calls and convenient subsets cannot establish independent corroboration.

## Automated and integration validation

The implementation includes arithmetic/sign/units, missing/failed/cancelled/fallback accounting, output mismatch, scope drift, duplicate plans/runs, non-finite values, degenerate intervals, energy integration/coverage, origin/admin authorization and actual HTTP/SSE parser tests. SSE tests inject empty role chunks, heartbeats, whitespace, incomplete streams, changed run IDs and errors.

Synthetic fixtures validate code paths only. Final frozen-source verification passed 136 host tests, seven JavaScript suites, generated localization/release consistency checks, and documentation checks across 92 pages and 389 local targets. The live authenticated analysis endpoint reproduced the pilot report. The full dashboard displayed the physical pilot, missing-energy state, fallback count and qualification warning; Chinese and Italian controls were checked separately from the English default. Native engine source and companion binaries are unchanged by this measurement release.
