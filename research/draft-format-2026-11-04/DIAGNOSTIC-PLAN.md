# Follow-up diagnostic after the first paired observations

The first ten available pairs showed two output differences in aligned batch verification and none in the serial control. This is an observed screening result, not yet a numerical-cause attribution. Preserve the frozen benchmark source and finish its original plan.

Then replay one mismatching prompt with the same batch implementation, capturing target input history and logits. If the replay differs from the serial reference, find the target logits that emitted the first differing token. Reconstruct exactly that token prefix using a fresh target cache and serial one-token history. Compare next-token argmax and logits. Confirm the retained cache token IDs agree with the intended prefix. Instrumented timing is not benchmark timing. If instrumenting changes the observed mismatch, report that limitation rather than claiming a cause.

This can distinguish an observed context-ID mismatch from a final-logit discrepancy under different execution history. It cannot identify a unique layer/kernel, establish general determinism, or qualify a production fix.
