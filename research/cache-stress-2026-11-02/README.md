# Experimental draft-cache stress

2 November 2026. The [frozen plan](PLAN.md) compared default and deferred-draft native builds using 80 deterministic state transitions for each model/backend configuration. The [runner](stress.py) varied draft widths, controlled prefix retention and corrections, backtracks, explicit prefill and resets. Every call supplied the same authoritative prefix to both builds. The appended tokens simulate state transitions; they are not measurements of target acceptance.

| Model | Requested backend | Transitions | Output or EOS differences | Errors |
| --- | --- | ---: | ---: | ---: |
| Qwen2.5 0.5B Q4_K_M | Metal | 80 | 0 | 0 |
| Qwen2.5 0.5B Q4_K_M | CPU | 80 | 0 | 0 |
| Qwen2.5 1.5B Q4_K_M | Metal | 80 | 0 | 0 |
| Qwen2.5 1.5B Q4_K_M | CPU | 80 | 0 | 0 |

The four raw JSON records retain the exact native and model hashes, seed, configuration and per-transition outcomes. No difference was observed in 320 targeted calls. This is not a proof for other prompts, longer contexts, repeated cancellations, EOS boundaries, tokenizers, mobile backends or sustained sessions. See the separate [batch-shape study](../batch-numerics-2026-11-02/README.md): equal output in these traces cannot establish universal numeric identity. The deferred optimization remains off by default and no physical phone speedup has been measured.

Reproduce on a compatible machine with both builds available:

```sh
python3 research/cache-stress-2026-11-02/stress.py \
  /path/to/model.gguf 999 /path/to/default/libnodelift.dylib \
  /path/to/deferred/libnodelift.dylib /tmp/cache-stress.json
```

Use GPU layers `0` for the CPU-requested arm. Build both libraries with the same toolchain and source; set `NODELIFT_EXPERIMENTAL_DEFERRED_DRAFT=ON` only for the second. The script is research tooling and does not change the Python-free standalone distribution.
