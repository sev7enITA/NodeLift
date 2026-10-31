# External model review and adjudication

31 October 2026. Review is advisory static analysis, not execution or device qualification.

## Actual sessions

- **GLM-5.3, Max**, selected in the browser: received a 66,985-character attachment containing NodeLift's native core, host controller/gateway, scheduling, tests and benchmark harness. Returned a substantive static review. It explicitly did not execute code and did not receive the mobile implementation, HTTP server, Python native wrapper or frozen baseline source. Subsequent adjudication was sent in the same conversation.
- **Gemini 4 Argon, Alta**, selected in the browser: the source attachment was uploaded, but both the initial request and one narrower clarification received generic refusals. **No Gemini code validation was obtained.** Earlier design reviews are unrelated to this engine update.
- Only NodeLift's own source and experiment description were sent. AudioEnhancer/myTrader private sources, prompts from private inference, account data and keys were not included. Browser snapshots containing sidebar/account information remain private.

## Decisions

| Finding | Disposition and evidence |
|---|---|
| F1: engine replacement/cancellation race | Accepted in part. Handle publication now shares the controller lock with Stop. Stop during target load prevents creation of the draft and later prefill, covered by a blocking-load test. Further cancellation checks bracket proposal/verification/text commit. The native API still clears its own cancel flag at call entry: a Stop in that narrow window can be deferred until the entire entered native operation ends. Model loading has no abort callback in this wiring and can finish before cancellation is observed. No instantaneous cancellation guarantee is claimed; model hashing/file I/O is also not fully interruptible. |
| F2: short first remote deadline can reject a cold/slow path | Valid limitation. Retained bounded latency as the opt-in policy; fixed mode retains the configured ceiling for qualification. Added the explicit `remote_probe_timeout` reason, separate from `no_measured_gain` and worker failure. Timeout is insufficient evidence of warm-state throughput. The proposed unconditional first 30-second allowance was not adopted. A claimed universal impossibility below 20 ms was unsupported by the physical hotspot measurements. |
| F3: remove publication cost from gate | Rejected as an objective change. Publication, synchronization and discarded proposal work are real costs; `block_ms` excludes the publication step and `round_ms` includes it, as documented. The gate uses the latter. Growing snapshot cost and a stale early host estimate remain performance limitations. |
| F4: count only compared proposals | Retained `proposed` as all generated/submitted proposals, including discarded work. Acceptance here is work utilization, not compared-token classification accuracy. Changing the denominator would hide spent proposal work. |
| F5: baseline lock/build identity | Accepted for robustness. Baseline files/library are verified against their manifest before execution, and each worker row records its own lock. In this experiment both pins were actually identical and the baseline binary hash was already recorded in the nested manifest. |
| F6: empty completion aggregates | Fixed before receiving the review. TTFT/speed ratios return null for no eligible data; failure checks precede the token-mismatch gate. A regression test covers failed and different-output arms. |
| F7: mismatch visibility | Console and JSON now report exact/completed/total counts. All raw runs remain visible. The review's advice to include different outputs in a same-output speed median was rejected; those rows remain in the denominator, outside that timing ratio distribution. |
| F8: full-run snapshot copying in status | Retained and documented. Dashboard polling can add overhead; benchmark workers query status only between completed runs. No claim that the isolated worker timings equal a busy GUI's latency. A compact status contract needs coordinated UI work. |
| F9: mobile context preflight | Valid missing capability negotiation, not fixed by pretending `model_offer.max_context` is loaded context. Current iOS/Android telemetry does not advertise the actual loaded context; a future companion update must do so. Current failures still return to host. |
| F10: append-only lookup / hash cache / TTFT / gateway deadline | Lookup's append-only ownership is explicit and tested against an independent scan oracle. Model identity caching by size/mtime assumes local weights are not replaced while preserving both; same-size/same-mtime replacement is not qualified. TTFT means first committed output block after load, not cold request wall time. The gateway's 300-second ceiling is separate from per-lease timeout. Unknown configuration keys remain ignored by the existing configuration subset. |

GLM found no additional demonstrated output-state error in its static inspection of argmax caching, lookup indexing and KV resynchronization. This does not prove universal correctness. The four 96-token batch/single mismatches remain a disqualifier for a universal same-output claim.

## GLM follow-up

GLM returned a substantive English follow-up to the dispositions. It accepted the same-output exclusion and retracted its original direction of publication-cost bias: per-round overhead can be amortized across accepted tokens. It accepted the proposed-token denominator as work utilization, while noting that rejected and end-truncated proposals share that denominator. It accepted the provenance/empty-summary fixes and the decision not to invent a mobile loaded-context capability.

The follow-up requested a discriminating timeout test and sharper wording. Added an end-to-end controller test with a timed-out first remote probe: exactly one lease is attempted, the rest remains host-only with `remote_probe_timeout`, and every subsequent decision has zero draft samples and no measured draft cost. The timeout is a bound, never a completed-cost observation. The cancellation and conditional-median limitations above were made explicit. No additional engine behavior was changed after the frozen 112-call repeat.

The follow-up did not execute the revised tests or inspect the final full source. Its statements about phone behavior were hypotheses based on missing worker code; an actual worker can return an explicit error as well as time out. Validation remains the recorded local tests, with physical mobile qualification still open.
