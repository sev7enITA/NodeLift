# Adaptive scheduling and larger targets: predeclared Mac experiment

5 November 2026. This experiment seeks a repeatable gain, not a guarantee that one exists. It changes backend to MLX and targets to official Qwen 14B and 32B four-bit snapshots; it is not a direct speed comparison with the previous float16 PyTorch experiment. Every candidate is compared with its identical target artifact and upstream backend.

## Resources and candidates

Download pinned official Qwen3 MLX four-bit target models at 14B and 32B, and draft models at 0.6B and 1.7B. Preserve all existing user models and files. Retain at least 12 GiB disk space. Before loading a pair, require estimated weights plus working allowance to fit currently available RAM. Record RAM, swap and process state. Abort a stage if available memory falls below 1.5 GiB or a resource/error limit is reached. A skipped model is not a performance result.

Use greedy target decoding and `enable_thinking=False`, verifying complete tokenizer vocabulary and chat-prefix equality. Generated code is data, never executed. Keep model loads outside timed requests, fresh KV per request, EOS respected and identical output cap (128 tokens). Retain TTFT, complete token sequences, request elapsed time, candidate work and fallback. No phone, P16, network or energy measurement is implied.

## Separate screening and validation

Freeze three screening prompts and eight distinct validation prompts before model runs. For each target, screen both drafts with upstream fixed k=2,4,8 and the adaptive policy below, plus a target-only control. Use one shuffled pass; its results select configurations and cannot qualify them.

Select the fastest fixed configuration and fastest adaptive draft using screening paired elapsed-time ratios, prioritizing zero observed output mismatches. Retain disqualified candidates and selection rationale. Freeze selected configurations before opening validation results. If an entire category fails screening correctness, do not present its selected representative as qualified; validation may still diagnose it.

For each admitted target, run validation in two fresh processes, two shuffled paired repetitions per process and all eight validation prompts. Compare target-only, selected fixed and selected adaptive paths. A candidate needs exact tokens and finish reason on every completed pair, no hidden failures, median paired speed ratio above 1.05 in each process, and a paired bootstrap lower bound above 1 for workload-level median ratios before being described as a bounded repeatable gain. Also report regressions by workload and TTFT, not just aggregate means. These are experiment admission criteria, not a universal speed guarantee. Four repeats of one prompt are correlated, not four independent workloads.

No policy will be promoted on screening results. If only some workloads benefit, state that scope and retain baseline fallback; do not claim universal acceleration or shared memory.

## Adaptive policy

Start with k=2; cap at 8. Estimate serial token cost from a separate target-only calibration prompt, never from the paired validation reference or future results. At each speculative block, compare measured draft+verification wall time per emitted token with the calibration cost. Increase k when acceptance is high and observed cost has at least 10% margin, reduce k on low acceptance or loss, and permanently disable further draft work for that request after three consecutive unprofitable probes. Reset per request. All startup, discarded proposals and fallback overhead remains included in request timing.

The policy is a heuristic, not a correctness mechanism. Continuing width-one steps after batch work does not restore serial numerical history. Exact output checks remain mandatory. Instrumented adaptive code is a small attributed MIT-derived variant of installed MLX-LM; compare a fixed-policy variant with upstream output in the smoke test before interpreting it.

## Bounds and provenance

Use isolated pinned dependencies and model revision hashes. Preserve failed attempts, warmups, screening, validation and evidence derivation. Source hashes identify every executed runner. Limit each measured request to 180 seconds and each process stage to 30 minutes. Stop and report numerical mismatches or resource constraints honestly; do not change precision, output contract or stopping criteria after observing a favorable result without a separately labelled follow-up.
