# Matched upstream API timing control

After the planned 90-run probe, the upstream assisted arm appears faster on some workloads while the custom arms are slower overall. Its instrumentation differs from the custom reference. Before interpreting those ratios as an algorithmic benefit, compare upstream greedy generation and upstream fixed-k=4 assisted generation through the exact same helper and streamer. Preserve every original result.

Reuse all six frozen prompts, maximum 64 tokens, EOS respected, same pinned models, float16 MPS, both models resident, one warmup per arm and three shuffled paired repetitions per prompt with seed 20261105. Fresh KV state per request. Keep tokens, elapsed time and first-token readiness. Compare equality within each pair and repeat consistency within each arm. This follow-up is post hoc and not an independent workload set. No energy, phone or network claims.
