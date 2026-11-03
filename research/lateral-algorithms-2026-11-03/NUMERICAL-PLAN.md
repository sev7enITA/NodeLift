# Predeclared numerical isolation probe

This is a diagnostic of one known divergent prefix, not a performance benchmark or a general correctness qualification. No phone is involved. The existing application remains unchanged.

Reuse the frozen `shape-history-cases.json`: the same prompt and generated token IDs, history widths 2/3/5, current widths 1/5, at offset 36. Use the existing probe whose SHA-256 is `c5e6a757d0888cab9f148711221836c648cd848464a7949bdbdbce8ee5980cc7` and the previously recorded Llama 3.1 8B Q4_K_M artifact. Eight threads, context 2048, serial reference history enabled. Each window has separate candidate, serial-reference and serial-repeat contexts.

Run profiles serially in this diagnostic order: Metal requested + flash attention requested, Metal requested + flash attention disabled, CPU requested + flash attention requested, CPU requested + flash attention disabled. Retain logs to distinguish requested settings from effective backend support. One invocation per profile, with a ten-minute safety timeout. Do not retry errors silently. Record file hashes, exit codes and the complete results. No inference or compilation runs concurrently in this experiment.

For every position, report serial/candidate argmax and serial/repeat argmax, maximum absolute logit differences, and serial top-two margin. Compare each candidate with its own profile's serial reference, not a cross-backend oracle. Record whether changing backend/attention removes this observed flip, introduces other flips, or leaves it unchanged. A disappearing flip only narrows hypotheses; it cannot establish the unique root cause, universal determinism, a production fix or a speed advantage. The elapsed times in the probe are diagnostic only.

Stop this diagnostic for nonfinite logits, context/model failure, timeout, or a serial-repeat discrepancy. Preserve partial files and the failed profile. Additional instrumentation of first-divergent-layer activations is a later experiment, not implied by this probe.
