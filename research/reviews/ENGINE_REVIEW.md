# Engine reviews and adjudication

31 October 2026. Actual browser selectors were Gemini **4 Argon / Alta** and GLM **5.3 / Effort Max**. No Flash/other-provider substitution was made. The services received technical design material and NodeLift source snapshots, not AudioEnhancer private code, user prompts, pairing credentials or signing keys.

## Completed design reviews

- [Gemini 4 High design response](gemini-4-high-engine-design.txt).
- [GLM 5.3 Max design response](glm-5.3-max-engine-design.txt), obtained after a regeneration produced an actual final response.
- [Shared design prompt](engine-design-prompt.txt).

Both supported stronger local comparators, token-ID compatibility, measured batch/single drift, full-prefix recovery, explicit mobile lifecycle limits and failure/waste accounting. These led to upstream n-gram/draft comparisons, native correctness tests, separate client/admin credentials, TLS loopback fault tests and clear physical-device qualification boundaries.

Their asserted universal latency cutoffs, hypothetical target/draft timings and universal co-location dominance were not adopted. The inspected distance paper explicitly assumes equal models/acceptance and fixed contention-free times. Gemini's unverified arXiv 2610.03228 reference and preset 4/42 ms values are not our sources or measurements. GLM's suggested 100,000-token/10,000-RPC sweeps are future qualification proposals, not tests completed here.

## Actual source review

[Gemini code audit](gemini-4-high-code-audit.txt) covered gateway.py, host.py, NativeEngine.kt and NodeService.kt. [Prompt](gemini-gateway-audit-prompt.txt) and [source hashes](gemini-gateway-audit-source-hashes.json) identify the reviewed snapshot. It had no runtime/hardware access and did not see the C++ core or Python controller. Several findings labelled “proven” were conditional on missing files and were adjudicated accordingly.

| Finding | Disposition |
|---|---|
| Kotlin cancel/close use-after-free | C++ opaque-ID/shared-ownership registry already prevented the alleged freed-pointer dereference. Cross-thread Kotlin references were made volatile. Expanded native test races cancel/close with a real inference call. |
| Heartbeat/PSS every draft round | Accepted: heartbeat/telemetry now time-gated to three seconds on Android and iOS. Claimed kernel-scan timings were not measured/adopted. |
| Idle poll tight spin | Not present with the actual five-second blocking mailbox. Added bounded connection-error backoff; no artificial per-block sleep. |
| Mobile context mismatch | Native core already bounded context safely, so out-of-bounds memory access was not demonstrated. Android now checks its loaded context before dispatch; incompatible jobs fail explicitly. |
| Epoch coercion/prefix JSON spaces | Current host uses string epochs and canonical compact integer arrays, so the claimed interoperability failure did not apply. Metadata extraction was moved inside Android error handling. |
| UTF-8 stream retractions | Already prevented by the controller's incremental decoding of byte output; real-weight stream/nonstream equality and fragmented UTF-8 adapter tests passed. |
| Gateway timeout/missing-run response | Accepted: use a controlled runtime error rather than silently dropping HTTP on deadline; missing run records fail explicitly. |
| Keep-alive and long poll | Separate listener semaphores bound connections; actual poll is five seconds. Socket inactivity timeout does not independently interrupt a condition wait. Retained persistent TLS instead of adding handshakes per round. Wider concurrency/DoS qualification remains open. |
| Android restart overlap | Accepted: running state remains active until worker teardown completes; native thermal cancellation and error backoff added. |
| Stale startup wording / null optional fields | Banner corrected, fresh-state startup test added; supported optional nulls use defaults. Unknown API features remain rejected. |

[GLM source audit](glm-5.3-max-code-audit.txt) subsequently completed on the [core/controller/test snapshot](glm-core-audit-prompt.txt), identified by [hashes](glm-core-audit-source-hashes.json). It is a static review, not execution. Its six findings were checked against the actual pinned dependencies:

| Finding | Disposition |
|---|---|
| Empty KV removal returns false, forcing quadratic re-prefill | The claimed major bug is **not present** in pinned `llama-kv-cache.cpp`: `seq_rm` returns true even when no cell matches (lines 439–505). Added the guard anyway to avoid a needless scan. No speedup is attributed to an unobserved full reset. |
| Destroy does not cancel an active call | Accepted lifecycle improvement: destroy now marks closing and cancels before erasing the registry entry; retained calls keep memory safe and queued calls reject a closing handle. Both close alone and explicit cancel/close have real-weight race checks. Cancel remains per-call; embedders gate future work. |
| No runtime single/batch equivalence canary | Accepted qualification gap. Added actual verification batch width to every block; the real-weight oracle test covers random rejection/rollback and EOS across block widths. A sampled production shadow verifier/automatic disable is **not implemented**. Finite-logit failures now reset cache before returning. |
| UTF-8 split creates replacement characters | The claim was incorrect: the previous controller decoded the **whole accumulated byte sequence** with `final=False`, retaining the incomplete tail. Its quadratic detokenization was real. Changed to persistent incremental decoding of only newly committed IDs, tested a character split across blocks, and included detokenization in block/rate timing. |
| Fixed 30-second remote stall | Accepted: run/API/dashboard can select 500–60000 ms, default 30000; timeout causes recorded host fallback. Cumulative remote wait is reported. The default is not a measured optimal phone deadline. |
| Catalog deletion race and repeated full walk | Accepted: skip disappeared/unreadable entries, cache five seconds, refresh on configuration. A disappearance regression test passes. |

The audit snapshot did not contain `scripts/check-native.py`; its statement that no native tests existed describes the supplied subset, not the repository. Post-review checks were rerun on changed components. Neither model reviewed the final compiled binaries or measured the phone.

## Interface review

A separate evaluator obtained an actual Gemini 4 Argon/Alta design review on desktop/tablet/mobile captures: PASS with refinements, scores 2/3 design, 2/3 originality, 1/3 craft, 2/3 usability. The implementer fixed unauthenticated filtering and unapplied-configuration ambiguity, plus responsive/readability issues. A second live functional pass confirmed the two fixes and hidden-key API-panel behavior. Fresh screenshots were unavailable, so no new Gemini visual approval or improved craft score is claimed. iOS UI was parsed and the complete app compiled; physical rendering remains open.

Model agreement is advisory. Only observed tests support the corresponding implementation claims, and none of these reviews establishes phone speedup or production readiness.
