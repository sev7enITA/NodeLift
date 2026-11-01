# Device assessment, sessions and useful contribution

NodeLift separates inventory, basic diagnostics and model-specific usefulness. A connected device does not automatically add usable model RAM or improve generation speed.

## Connection history

The authenticated desktop displays the peer IP observed on the server socket, first and latest enrollment, latest authenticated contact, current/latest session start, previous session's last contact and observed session count. Client JSON and forwarding headers cannot overwrite these values. An IP is a route observation, never a physical device identity.

A session boundary is inferred when a new authenticated request follows more than 20 seconds without contact. The previous session ends at its last observed contact, not a fabricated exact disconnect time. Re-enrollment also starts a session. Legacy rows retain unknown enrollment dates. The host displays its active bound LAN address and process start, separately from phone sessions.

Android and iOS show the age of the last successful authenticated response. After 20 seconds the active indicator becomes uncertain even if the worker is still running. Draft readiness remains separate. This improves reporting; it does not establish the cause or resolution of the physical Xiaomi network timeout.

## Initial assessment

The production host schedules a basic assessment only for a newly created enrollment. Automatic assessments are serialized across devices and do not overlap other diagnostic jobs. Two supported jobs run sequentially: a bounded network diagnostic and a short CPU calibration. Re-pairing an existing identity does not automatically repeat work. Existing devices have an explicit Assess device action. Repeat is blocked while jobs are pending or the host engine is busy.

Automatic job dispatch pauses below 20% reported battery, at severe/serious or higher reported thermal state, or while the host engine is busy. Existing job timeouts remain active: running jobs expire after 120 seconds, queued jobs after 300 seconds. There is no endless retry, automatic model download or automatic LLM generation. Companions retain their own thermal and cancellation controls.

| Classification | Meaning |
|---|---|
| Needs assessment | No current basic assessment, or observed connection address changed |
| Diagnostics only | Available diagnostics passed but no ready draft engine, or only some diagnostic types are supported |
| Draft candidate | Network and CPU samples returned and the companion reports a ready engine; LLM acceleration is still unqualified |
| Needs attention | Failed, timed-out, expired or incomplete supported measurements |

The assessment records the connection address at scheduling. An address change invalidates classification; historical measurements remain visible with their timestamp and a repeat-assessment explanation. A synthetic CPU score is not converted into predicted LLM tokens/s. Partial and failed results are retained.

## Contribution and KPIs

The former generic Contribution not measured label conflated several states. The graph now distinguishes no selected run, unavailable native output accounting, an external API route, a phone that was not selected, and measured zero accepted proposals. The Mac remains the target-model executor and verifier in every native mode. A zero host-origin token share does not mean zero host computation.

| KPI | Definition and use | Evidence boundary |
|---|---|---|
| HTTPS RTT p50/p95 | Application request roundtrip distribution on the observed connection | Not ICMP ping; report sample count and test date |
| Transfer MiB/s, each direction | Median throughput at the largest tested payload size | Connection measurement, not a phone compute score |
| Synthetic CPU iterations/s | FP32 256 x 256 matvec iterations divided by measured seconds | Platform/kernel-specific calibration; not LLM prediction |
| Generation TTFT | Backend-reported time to first generated token | Current native clock excludes model load, tokenization and setup; do not call it end-to-end TTFT |
| Prefill and decode tokens/s | Actual backend phases for the selected model and context | Whole-run measurements, not per-device rates |
| Total engine request duration | Recorded request_total_ms, when available | Separate clock; do not synthesize end-to-end TTFT by summing incomplete phases |
| Proposal acceptance | Accepted draft token IDs divided by submitted proposal IDs | Include count and selected device; acceptance alone does not establish a speedup |
| Accepted mobile token share | Accepted mobile draft IDs divided by all committed output IDs, including EOS | Token origin attribution, not CPU/GPU utilization or proportion of total work |
| Remote wait and fallback | Recorded wait, fallback count and reason; retain failed and stopped runs | Wait includes remote compute and transfer, not network latency alone |
| Relative speedup | Matched Mac-only total duration divided by Mac-plus-device total duration | Requires repeated paired runs with same target, prompt, output policy, context and warm/cold-load treatment; not inferred by this inspector |
| Sustained usefulness | Throughput and latency distribution under prolonged work, thermal state, battery change, failure rate and wasted proposals | Future physical qualification; no fabricated energy/power readings |

Memory inventory is reported with its scope and freshness: physical RAM, system availability or process headroom. None is labeled pooled or allocated to the host model. Model-specific memory capacity and sustained acceleration require a separate real inference qualification. The dashboard does not implement an automatic matched LLM speedup qualification in this release.

## Companion information architecture

Home shows connection, draft readiness and one next action. Activity contains diagnostics, telemetry and direct log export. Settings contains model setup, limits, language, About, pairing and manual fallback. Forgetting a computer requires confirmation. QR and pasted invitations both preserve the computer-identity confirmation step.

Readable system text, scalable native type, minimum touch targets, text plus status symbols and selective screen-reader announcements guide implementation. Android follows the [48 dp touch-target guidance](https://developer.android.com/guide/topics/ui/accessibility/views/apps-views); iOS follows [Apple accessibility guidance](https://developer.apple.com/design/human-interface-guidelines/accessibility) and [44-point controls](https://developer.apple.com/design/tips/). Source and build checks do not replace TalkBack/VoiceOver, large-text and physical-device testing.
