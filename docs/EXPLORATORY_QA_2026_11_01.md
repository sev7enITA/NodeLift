# Exploratory QA with GLM and Gemini, November 1, 2026

This is a bounded functional audit, not proof that every NodeLift feature works or that phones accelerate inference. The desktop baseline was commit `34d6676ad3c42b5d0a5c238019a41d6f3d848a3d`. Companion binaries remain 0.2.8; this change does not publish new mobile binaries.

## How the external testers participated

Actual browser sessions used **GLM 5.3 with Max effort** and **Gemini 4 Argon with High effort**. They proposed adversarial sequences and reviewed sanitized observations. GLM also inspected the public repository. Neither model could access the owner's localhost or operate the phone. The local agent executed browser actions, inspected backend results and relayed outcomes. Model suggestions are not independent execution evidence. GLM's initial capacity failure was retried without silently substituting Flash.

Gemini drove session, model-library, cancellation, native lifecycle, provider and localization probes. GLM additionally identified untranslated validation errors, absent fallback-cause rendering, missing restart restoration of run history and orphaned transfer visibility. Suggested tests that require an unavailable physical device, installed third-party client or paid cloud call were not represented as passes.

## Confirmed fixes

| Defect | Change | Evidence |
|---|---|---|
| Cancelling an HF download displayed a download failure | A cancelled transfer clears the failure message, preserving cleanup warnings | Real browser cancellation after 14.4 MiB; stopped state, no owned partial file; backend regression |
| Uploaded-model provenance disappeared through `/tmp` versus `/private/tmp` aliases | Canonicalize registry paths on read, lookup and registration | Real imported file regains its original name and Imported file label; alias/reload regression |
| Small models displayed 0.0 GiB | Reuse adaptive model-size formatting | Real 18,901,824-byte file displays 18.0 MiB; UI regression |
| Native and validation errors remained English in Italian/Chinese | Extend canonical catalogs and regenerate assets | Real context-budget and missing-chat-template errors checked in both locales; catalog/runtime checks |
| Completed remote runs did not disclose their fallback cause | Render the recorded fallback reason in the result card | Synthetic UI regression verifies disclosure and absence on an ordinary host run; no claim of physical fallback qualification |

The Android Wiki source download link and documentation hub version now point to the current companion release. Generated mobile translation sources changed, but installed mobile binaries did not.

## Executed coverage

| Area | Observed result | Boundary |
|---|---|---|
| Session | Unauthenticated controls disabled; recovery works; host restart expires access; restore recovers persisted model configuration | Tested in isolated dashboard; no weakening of authentication |
| QR | Real modal creation and close; lifecycle/duplicate guards exercised by focused automated checks | Physical scan, five-minute wall-clock expiry and re-pair migration not fully exercised in this audit |
| Hugging Face | Public search/inspection, empty result, repository validation and real download cancellation | Private/gated auth and every repository format not tested |
| Local models | Native OS file chooser, invalid GGUF rejection, real 18 MB upload and matching SHA-256, path import | Header validation does not qualify every architecture for inference |
| Native host | Real host, local-draft and lookup generation; stop, reconfigure and generate again; context-budget rejection; missing chat template | Fixed public prompts and small control models; no throughput qualification |
| Providers | Unreachable server and invalid local URL fail visibly; browser reload retains configured local URL | Installed LM Studio UI and paid cloud generation not exercised |
| Local gateway | Missing key returns 401; catalog, nonstream and SSE generation; matching output in control | NodeLift gateway itself, not all third-party clients |
| Export/About | JSON download parses and omits client key; project/version boundaries visible | Raw local exports contain local paths and are not published here |
| Localization | English, Simplified Chinese and Italian switch and persist; dynamic native failures translated | Physical mobile localization not tested |
| Attribution graph | Local-draft acceptance does not count as mobile contribution; no invented device measurements | Actual mobile accepted-token contribution not established |

The final isolated source suite passed 105 host tests. Focused JavaScript suites cover control state, model library, pairing, localization and device-graph accounting. Initial source-extraction failures caused by a missing tracked native lock file were corrected in the test fixture before the passing run. Synthetic checks are explicitly distinct from real browser and physical-device checks.

## Physical Xiaomi results and blockers

The owner opened companion 0.2.8 and completed the draft download. The host observed an authenticated node reporting `engine_ready=true` with nominal thermal status. A CPU job completed **5,227 iterations in 1,500.002 ms**, using the single-thread Kotlin/JVM FP32 256 x 256 matvec diagnostic. This is not an LLM tokens/s measurement.

Two Quick network jobs were claimed, then timed out at the host's 120-second deadline without returning samples. Host contact became stale while the owner reported that the app remained foreground and displayed connected/draft ready. CPU success demonstrates one successful job/result roundtrip; it does not rule out failures in the network loop, result payload handling, routing or connection lifecycle. No root cause is established without the companion diagnostic export or new instrumented evidence. The host intentionally suppresses raw HTTP access logging, so historical endpoint traces are unavailable.

A remote-draft probe waited 90 seconds for an eligible online-ready node and could not dispatch. **No accepted mobile token, reliable wireless inference route, sustained thermal result or speedup is established by this audit.** The host-only control completed, but there is no valid paired Mac-only/Mac-plus-phone performance comparison.

A legacy offline 0.2.6 enrollment and a newer 0.2.8 enrollment for the owner's Xiaomi coexist. This migration case remains open. No automatic consolidation by model name, IMEI or mutable hardware label was performed.

## Remaining gaps

- Capture the phone's local diagnostics and qualify stable contact, network jobs and actual remote token proposals before claiming the mobile route is ready.
- Qualify migration/re-pairing without duplicate physical-device presentation while preserving distinct phones of the same model.
- Restore historical run presentation after host restart; current run records are persisted as artifacts but not rehydrated into the live list.
- Expose interrupted-download cleanup state: abandoned owned partial files currently use the documented age-based cleanup path, without a dedicated UI recovery view.
- Test iOS pairing and sustained execution, HarmonyOS/NEXT, installed client integrations, private model access and long-running thermal behavior on the relevant devices.
- Capacity sharding and shared model RAM remain unimplemented. Draft delegation does not make arbitrary cloud GUIs use phone RAM.

## Evidence

[Desktop functional receipts](evidence/exploratory-qa-2026-11-01/desktop-functional-checks.json), [physical checks](evidence/exploratory-qa-2026-11-01/physical-checks.json), [gateway checks](evidence/exploratory-qa-2026-11-01/gateway-checks.json) and [export check](evidence/exploratory-qa-2026-11-01/export-check.json) contain sanitized observations. Raw session URLs, bearer tokens, device identifiers, user paths and browser account/sidebar content are excluded.

[External review record and adjudication](evidence/exploratory-qa-2026-11-01/external-review.md).
