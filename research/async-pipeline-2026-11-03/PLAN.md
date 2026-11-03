# Instrumentation and bounded lookahead experiment

3 November 2026. Planned before new measurements.

Implement native sync/decode durations and work counts; record host enqueue, dispatch, receipt and expiry using host monotonic time. Worker durations are self-reported and never trusted for routing or token identity. Retain late results with zero committed credit and bounded trace retention. Do not call the unattributed remainder network RTT.

Correct C ABI allocation failure handling, cooperative load cancellation and stale-logit invalidation. Preserve the conservative reset after native errors. Reject recognized control-token spellings and embedded NUL in untrusted chat content while retaining genuine template controls. Raw tokenization exposes explicit special/add-special options. Serial verification is the safe default; batch remains explicit experimental and must retain exact-output failures.

The Android experiment permits one speculative next block only after submitting the current result. Reuse requires epoch, model, tokenizer, authoritative-prefix and sequential identity agreement. Return no unverified tokens to the user. Bound speculative work, expiry and terminal cleanup; record computed, reused, consumed-prefix and discarded token counts separately. Run matched host-only, local serial draft, local experimental batch, local bounded lookahead, remote serial and remote bounded-lookahead arms where the actual artifact compatibility permits. Benchmark controls must include the strongest applicable measured local option, including upstream where available.

First use the resident Qwen2.5 1.5B/0.5B pair to check protocol. Select a larger dense target only after its actual token-ID fingerprint matches the mobile draft. Existing Qwen2.5 7B Ollama was incompatible; do not bypass that guard. Preserve all planned attempts, error/fallback rows and exact token hashes. Use fixed public prompts, greedy sampling, 128-token budget, context 2048, unchanged quantization/backend per matched comparison, randomized paired ordering and explicit warmup. Three pairs per exploratory cell are a pilot, not confidence qualification. No performance inference while compilation or other experimental model runs compete for resources.

Build and identify an optimized Android APK. Where install access allows, compare otherwise identical instrumented O0 and O3 artifacts; a comparison with the historical 0.2.8 binary cannot isolate optimization from intervening code changes. Mobile install and foreground availability are required. Capture thermal/battery snapshots, not inferred energy. Record loaded artifact and model identity, requested versus observed backend and connection fingerprint.

Promote no batch or asynchronous optimization without correctness qualification and repeated end-to-end gain against a strong local baseline. No shared-memory or capacity claim is intended.

## Frozen local pilot

Llama 3.1 8B Q4_K_M from the existing Ollama blob and Llama 3.2 1B Instruct Q4_K_M, verified matching token-ID fingerprint. `benchmark-bounded.py` freezes three public prompts, three repeats and eight arms before generation. Local draft remains resident in every arm to keep memory pressure consistent. Upstream comparison uses the same target/draft, prompt tokenization and output budget, with draft-simple and ngram-mod widths 1, 4 and 8 plus target-only. Upstream HTTP timings are paired only within that harness, not ranked against direct controller timing. Every exact-output mismatch remains in the exported result and disqualifies that comparison as an exact-output speedup.
