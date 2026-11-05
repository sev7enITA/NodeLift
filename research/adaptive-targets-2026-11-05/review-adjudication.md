# External static reviews and coordinator adjudication

5 November 2026. GLM 5.3 Max and Gemini 4 Argon High received descriptions of the frozen experiment and screening results through their browser interfaces. They did not inspect the source files or execute hardware tests. Model and effort selectors were verified in the UI. These are methodological critiques, not independent replication or code certification.

The initial OpenRouter attempts remain recorded in `external-review-status.json`: no complete answer from GLM at the output limit, and HTTP 402 from Gemini. The browser acquisition is a separate attempt; it does not retroactively complete those API calls.

## GLM 5.3 Max

The initial response supported exact-output admission and prompt-cluster statistics. It questioned three-prompt selection, scalar calibration and a permanent fallback after only three unprofitable blocks. These are valid limitations; selection and policy remain frozen for the current validation. A future policy needs a new protocol and fresh held-out prompts.

The coordinator challenged seven unsupported or incorrect statements. GLM returned a completed correction with a `Withdrawn` section:

- Loading was incorrectly included in its risk assessment. The runner excludes model load and retains the same resident model set for every arm.
- At k=2, accepted/k takes values 0, 1/2 and 1, not thirds. A threshold below 1/2 therefore requires zero accepted draft tokens.
- A serial-perfect oracle draft cannot separate logic bugs from numerical differences in batched verification.
- FP32 agreement on three prompts cannot identify the original cause, and persistent FP32 disagreement would not establish a logic bug.
- Draft cost and a numerical break-even threshold cannot be inferred from unrelated aggregate timing experiments.
- Complete vocabulary equality and per-request canonical token-ID equality remove the alleged initial prompt-token misalignment. Results remain limited to the common serialization, not native-template performance.
- Drafting cannot resume for free after permanent disable because the draft KV cache is stale. Any new probe needs explicit resynchronization charged to latency.

Retained next experiments: localize the first divergence on screening inputs, separately measure draft and target costs, and retain permanent fallback unless cache resynchronization is implemented and measured. An empirical logit-margin threshold is diagnostic only. It is not a correctness certificate, even if a reviewer describes it that way.

## Gemini 4 Argon High

The first completed response independently questioned scalar calibration, early permanent fallback, sample breadth and precision cost. It correctly stated that FP32 is not a general proof of numerical equivalence, but overstated several conclusions. The coordinator requested a correction:

- Sub-unity screening performance does not make validation failure deterministic.
- There are no native-arithmetic baselines for the held-out validation prompts, so a paired native/FP32 comparison cannot be derived from the existing validation logs.
- Resident memory, bandwidth dominance and page thrashing require measurement; they cannot be inferred from model size alone.
- A previous-token logit margin does not certify future tokens. Rechecking a block in FP32 with native-history KV cannot restore a serial oracle.
- Matching reduction tiling alone does not prove equality across every kernel and cache history.

Gemini returned a completed correction withdrawing deterministic validation failure, memory-thrashing attribution, unprofiled kernel explanations, guaranteed future FP32 divergence, and the proposed hybrid-oracle shortcut. Its suggested next experiment is an eight-token serial calibration within the request, with all synchronization and fallback charged. This is retained as a hypothesis for a new held-out set. Its remaining phrase that the controller "successfully limits downside" is stronger than the screening establishes; we report observed paired costs rather than infer a causal guarantee from three prompts.

No relaxed output contract, cross-precision speed claim or policy retuning was adopted from either review. No source code was provided to either browser reviewer, and no review is represented as a code audit.
