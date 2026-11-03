# External review adjudication

2 November 2026. Reviews were requested through the user's authenticated browser using public project details, aggregate benchmark evidence and scoped code descriptions. No credential or private diagnostic payload was sent. A model response is advice, not execution evidence.

## Availability and provenance

- **Gemini 4 Argon, High reasoning:** the UI selector explicitly showed Argon Alta. Initial review and evidence-correction follow-up both completed. Its recommendations were checked against code and the physical width sweep.
- **GLM 5.3, Max effort:** the model menu showed GLM-5.3 and Max. The first request remained without an answer; reload did not recover one. It was stopped and a focused request submitted. The page then reported that the model was currently at capacity. No answer, approval or cross-review by GLM is claimed. No different model was silently substituted.

The [initial brief](review-brief.txt) and [focused follow-up](review-followup-brief.txt) are preserved. Raw browser outputs are retained locally as diagnostic artifacts, not presented as verified technical conclusions.

## Accepted directions

- Prioritize separating phone-native compute, worker overhead and host-observed dispatch/return cost before replacing transport.
- Treat Android build optimization as a confirmed packaging confound after matching its ELF build ID, then isolate its physical effect experimentally.
- Compare wider speculation by committed tokens and full round cost, not acceptance percentage. The subsequent width sweep independently confirms that width alone did not help in this scope.
- Evaluate bounded lookahead with exact prefix rollback and a larger compatible target against both host-only and best applicable host-local speculation.
- Preserve exact output, failed/missing attempts, fallback and sustained-load checks in the decision.

## Rejected or narrowed statements

- Gemini's initial table labelled predicted larger-model gains as real gains. Those timings were not measured here; they are excluded from the result and release claims.
- Universal timing thresholds for phone CPU, Wi-Fi power-save and thermal throttling were unsupported for these devices. They remain hypotheses.
- The three-second Android sleep was not in the ready inference branch. Long polling and host TCP_NODELAY already exist. We do not claim their introduction as a new fix.
- A matching model family name does not prove an identical tokenizer fingerprint. The actual artifacts must pass the existing fingerprint check.
- Advertised phone RAM bandwidth is not usable host spill bandwidth. Network transfer and graph partitioning remain separate costs; capacity speedup was not established.
- Finding an unoptimized build does not prove it caused the entire measured latency or rule out simultaneous network overhead.
- Subtracting worker duration from host round-trip duration gives an unattributed remainder, not an attested wire RTT. Absolute timestamps on different devices must not be subtracted.
- A native optimization cannot be accepted solely because a pass count dropped or a model predicted a percentage gain. Exact outputs and measured end-to-end effects are required.
- A proposed arbitrary accepted-token percentage must not be used to remove slow or fallback requests from service evidence. Clean delegation and full-denominator service are reported separately.
- Ordinary cloud CI does not validate physical device thermals, radio behavior or energy. Those require device measurements.

This original 2 November adjudication incorporated Gemini's useful suggestions while rejecting its unsupported certainty. At that time GLM was unavailable.

## Resumption on 3 November

GLM 5.3 Max has now completed the [resumed assessment and independent adjudication](../reviewer-resumption-2026-11-03/PERFORMANCE-REVIEW.md). The actual response is preserved there. The historical availability section above describes the original attempts; it is not the current review status. Static analysis did not add physical measurements.
