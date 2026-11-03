# Resumed performance assessment, 3 November 2026

GLM 5.3 Max completed a static review of the [supplied report](glm-performance-prompt.txt). After the service started generating a document, a [focused request](glm-performance-followup-prompt.txt) obtained the [actual text response](glm-performance-review.txt). The model selection and Max effort were checked when the original request was submitted. This review is of the supplied narrative and aggregate numbers, not independently inspected raw traces, code, binaries or physical devices. The service's document-generation activity is not NodeLift test evidence.

Gemini 4 Argon High had already completed the [initial performance review and correction follow-up](../performance-diagnosis-2026-11-02/REVIEW_ADJUDICATION.md). This completes the previously unavailable GLM assessment, without retroactively changing the history of the 2 November attempts.

## Independent adjudication

| Observation | Checked disposition |
| --- | --- |
| The supplied iPhone cells were slower than their Mac-only pairs | Supported within the named conditions. We reran the existing cost-decomposition script against the retained width 1/4/8 records and obtained the same three cells byte-for-value after JSON decoding. This is analysis replay, not new inference. |
| Remote wait is not pure network latency | Accepted and already explicit. Worker durations, queue phases, KV-sync bytes and wakeups are useful future diagnostics. Subtracting self-reported worker time leaves an unattributed remainder, not measured wire latency. |
| The approximately 15-fold break-even gap is robust even at small sample size | Narrowed. The descriptive arithmetic has a large gap in this trace, but its size does not create statistical confidence or a population bound. Current acceptance and local work are held fixed; a changed build or pipeline requires new measurement. |
| Three pairs do not establish width ordering; use at least ten pairs | Accepted limitation, arbitrary sample rule rejected. The report already rejects a universal width ranking and publishes individual paired points. A confirmatory sample plan must use variability, independent sessions and a declared practical threshold; ten correlated pairs do not automatically suffice. |
| Android optimization was built but not measured on the phone | Accepted and already stated. No new optimized-phone outcome was obtained during this assessment. The old Xiaomi local-work floor is conditional on that trace and configuration, not invariant after a build or scheduling change. |
| The iOS build was not audited | Too broad. The supplied report explicitly states that the retained iOS native cache was Release with `-O3`. That is not the same as binding every loaded instruction and effective Metal allocation to physical build 15. Artifact-to-session identity and effective backend attestation remain open. The new framework packaging rebuild is not a retroactive audit of the tested phone binary. |
| Host-local speculation was never run | Incorrect project-wide, valid as a limitation of this specific width sweep. The earlier [phone trade-off report](../phone-tradeoffs-2026-11-02/REPORT.md) retains three local-draft control pairs with a 32-token budget and 1.504x median candidate/host duration. They cannot substitute for a strongest-local arm matched to the new 128-token sweep or a future larger target. |
| One-block lookahead is sound and approximately 18 ms can be hidden | A plausible design, not correctness proof or a measured overlap bound. Actual queueing, contention, synchronization, cancellation and useful lookahead must be traced. Token acceptance alone is insufficient. Record full-block acceptance and the exact reusable prefix after target correction; partial acceptance does not by itself prove all cached suffix work is unusable in every implementation. |
| A three-second not-ready sleep implies up to three-second lease latency under bursty arrivals | Rejected as an inference about an already-ready node. `NodeService.kt` long-polls in the ready/enabled/energy-allowed branch; the three-second sleep is in the other branch. Transition-to-ready latency is a distinct hypothesis requiring its own trace. Bursty-load testing remains useful without assuming that delay. |
| Use a 1.05x success threshold | An example, not an adopted product gate. The practical gain, TTFT trade-off and measurement uncertainty must be declared before confirmatory tests. No universal threshold is inferred from a reviewer suggestion. |
| Matching outputs prove protocol faithfulness | Limited to the retained outputs and tested configurations. Eighteen matching primary outputs are useful evidence; they do not prove general batch/serial equivalence, absence of races, or correctness on arbitrary prompts. |

## Next measurable work

1. Instrument host monotonic phases and bounded self-reported worker durations, plus bytes and discarded work. Keep invalid telemetry separate from token-identity validation.
2. Build, identify and physically compare the optimized Android artifact with its original under matched conditions. Link future iOS measurements to the loaded binary and effective backend.
3. Compare host-only, strongest applicable local speculation and phone speculation on the same target, context, output and sampling configuration, including cold/warm conditions as declared in advance.
4. Prototype bounded lookahead behind an experimental flag. Retain authoritative-prefix checks, exact target verification, rejection/cancellation and fallback. Measure actual overlap and sustained/bursty behavior rather than predicting gains.
5. Use independent sessions and a justified sample plan; retain every planned attempt, failure and fallback. Energy remains unmeasured without suitable power instrumentation.

These are experimental requirements, not implemented features or promised gains. No physical inference, new APK/IPA release, energy measurement, pooled memory or distributed acceleration was demonstrated by this resumed assessment.

## Completion boundary

The requested availability-delayed reviews are now completed within their recorded scopes: core/fork, build/library, performance diagnosis, selected localization, graph source, QR protocol description and About/update sources. The [core/build](REVIEW.md) and [product](PRODUCT-REVIEW.md) reports retain unresolved risks and rejected findings. Static review completion does not qualify all application behavior or close the remaining physical validation work.
