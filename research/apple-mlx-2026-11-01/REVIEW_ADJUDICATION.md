# External architecture review and decisions

1 November 2026. Scope: technical comparison and proposed execution architecture. No reviewer executed NodeLift, the phone worker or Apple's cluster. Public sources and a sanitized technical summary were supplied; private prompts, credentials and user diagnostic logs were not sent.

## Actual review status

| Reviewer | Observed selection and outcome | Evidence limit |
| --- | --- | --- |
| GLM | GLM-5.3, Effort Max selected in the browser; later attempt returned an inline architecture review after fetching three sources | The earlier rejection remains recorded; the corrective follow-up also hit the peak-hours capacity limit. No Flash substitution or corrective approval is claimed. |
| Gemini | Browser selector Argon High, requested as Gemini 4 High Effort; isolated technical conversation returned an inline review | A mixed-purpose first attempt and the correction follow-up returned generic refusals; no corrective approval is claimed |

Browser selections are observable service settings, not independent attestation of server-side model weights. Neither answer is a correctness proof, physical benchmark, governance certification or novelty review.

## Accepted contributions

- Separate capability/admission decisions, execution/state transfer and evidence accounting.
- Keep the optimized host as default and calibrate routing profiles by model, device, context and operating conditions. Add hysteresis and bounded probes.
- Investigate acknowledged context deltas, cancellable work and explicit stale-state recovery before optimizing the transport.
- Treat required capacity shards differently from optional draft workers. Report interruptions and reconstruction costs.
- Pin backend versions and runtime flags; compare against the strongest applicable local baseline and retain grouped uncertainty, failures and wasted work.

These recommendations are incorporated in the [RFC](../../docs/RFC_DISTRIBUTED_EXECUTION.md) as proposals, not claims of shipped functionality. Many are established distributed-systems practices and prior art.

## Rejected or qualified claims

| Claim in model advice | Decision and reason |
| --- | --- |
| The local 0.719× result establishes that accepted tokens cannot amortize verification, so no remote execution can help | Rejected. Total local time includes draft work and resource contention. It does not isolate verification cost or establish a universal bound on a different execution path. |
| Pipeline sharding can never improve decode latency and matters only when the target exceeds 64 GiB | Rejected as universal. Compute placement, memory bandwidth and host resource pressure differ; sequential dependencies alone do not establish that inequality against another baseline. Capacity remains a distinct primary motivation. |
| Geometric accepted-token formula applies directly | Qualified. It assumes a conditional acceptance model and needs EOS/output-cap handling. Qualification uses measured committed tokens and prefix lengths. |
| Divide draft + network + verification by accepted draft tokens alone | Rejected. Correction/bonus tokens that actually commit belong in the denominator; all request overhead and failed work belong in wall time. |
| Add TLS and queueing to measured HTTPS RTT | Rejected when those intervals already include them. Define non-overlapping component timers, or use complete measured wall time. |
| A fixed logit epsilon certifies exactness | Rejected. Token identity is a separate contract. Near-tie diagnostics do not prove arbitrary-output equivalence. |
| Missing client-certificate mTLS is itself a gap that must be closed before distribution | Rejected. NodeLift uses pinned TLS and per-node credentials; assess the actual threat model, authentication, revocation and replay behavior. A different mechanism is not automatically stronger in this application. |
| Thirty windows establish a stable p99 | Rejected. Tail uncertainty and prompt/session dependence require a justified sample design. |
| Logging prevents silent corruption | Rejected. Logging aids diagnosis; validated state transitions and output verification enforce correctness. |
| mmap guarantees a working large-model comparator | Rejected. Paging performance and successful execution depend on runtime, memory allocation, model format and storage. Compare only supported executable configurations. |
| An ordinary small-transformer dry run can predict the suggested 763B Strata/Engram model | Rejected. Different architecture/runtime/state requirements need their own implementation and measurements. |
| Current companions can immediately benchmark 32K or 128K contexts | Rejected. The Android worker currently allows up to 4096 context tokens. Larger contexts require changes and memory qualification. |
| Arbitrary 2-second recovery, 15% discarded tokens or 1.15× local-draft threshold are universal gates | Rejected. Thresholds need declared product goals; local drafting also competes for host resources and is not a universal remote ceiling. |

Wireless fine-grained tensor collectives are a poor first candidate on the observed hotspot. This is a design judgment from current evidence, not a theorem that every wireless collective can never help. Similarly, 80 ms from a paced HTTPS diagnostic is not automatically the network cost of every inference round.

The final decision is to develop and qualify the three execution lanes without advertising superiority. The initial product target in the RFC is explicitly proposed, with a distinction between a 10% time reduction and a 1.10× speed ratio. Actual adoption depends on correctness, reliability and independently reproducible measured benefit.
