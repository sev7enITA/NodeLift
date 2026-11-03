# Resumed external assessments, 3 November 2026

## Completed Gemini build/documentation review

The authenticated browser remained set to Gemini 4 Argon, High effort (`Argon Alta`). A complete response was received for four additional public fork files at commit `469f6272d365459e851e21be75bc811245fd0f96`: `examples/nodelift/README.md`, `validation/BUILD.md`, `native/CMakeLists.txt` and `LICENSE.nodelift`. The [supplied prompt](gemini-build-prompt.txt) and [verbatim response](gemini-build-review.txt) preserve the scope. Gemini did not run binaries, fetch other URLs or inspect unprovided files. Earlier core-source observations refer to commit `42458074580813661f1a35fa8da60107ee796fe7`, not automatically to the newer branch.

This completes that additional static review only. It is not product approval, a mobile UI review, or physical-device qualification. The [earlier adjudication](../prefix-cache-2026-11-02/REVIEW-2026-11-02.md) still applies to its named source and binary.

## Findings checked by NodeLift

| Reviewer observation | Independent check and disposition |
| --- | --- |
| B-01: the 31 strict checks do not cover the default batched verifier | Confirmed in source and already bounded in the build report. The fork README now explicitly says that `strict: true` selects the tested serial path. The batch response lacks `verification_mode`; absence must not imply serial validation. This is a coverage/observability gap, not a newly reproduced inference defect. Do not turn a known batch/serial counterexample into a passing test by changing its tolerance. |
| B-02: the library exports more than the NodeLift ABI | Confirmed on the published macOS library with SHA-256 `7e11b6cc52bba26f6fff1db3f7e5400c5edf7d7bc535c76760cb9a2295155332`: 4,655 global exports, including 252 `llama_*`, 1,253 `ggml_*` and four `sha256_*` symbols. [Symbol audit](symbol-audit.json). No actual collision or interposition failure was reproduced. Risk depends on the platform and loader. A blanket export restriction could break JNI or other required entry points, so no untested visibility patch was applied. The coexistence limitation is now documented. |
| B-03: the iOS framework omits its public header | Reproduced in a minimal real iOS arm64 framework build using CMake 3.22.1. `PUBLIC_HEADER core.h` without adding the file to target sources produced no `Headers/core.h`; adding it produced a byte-matching header. The existing NodeLift framework also lacked the header. The source fix adds `core.h` to `add_library` in NodeLift and its community fork. [Fixture evidence](framework-header-audit.json), [reproduction script](check_framework.py). This concerns framework packaging, not a demonstrated phone crash. |
| B-04: exact API bounds are not listed in the wrapper README | Confirmed documentation gap. The fork README now lists context, threads, requested GPU layers, proposal/output and message limits. These are API bounds, not per-device capacity guarantees. |
| B-05: missing mandatory C++ standard, and Android Debug optimization flags | `CXX_STANDARD_REQUIRED` is unset. [CMake documents](https://cmake.org/cmake/help/latest/prop_tgt/CXX_STANDARD_REQUIRED.html) possible standard fallback, but failure on a supported compiler was not demonstrated. The Android `-O3` setting is intentional, includes dependencies, preserves assertions and was already [checked in actual compiler commands](../performance-diagnosis-2026-11-02/android-optimized-flags.json). Multiple flags do not alone establish an optimization failure. Neither suggestion was applied without a demonstrated need. |

The framework's `PUBLIC_HEADER` purpose is described in [CMake's primary documentation](https://cmake.org/cmake/help/latest/prop_tgt/PUBLIC_HEADER.html). Our before/after build is the evidence for the specific source-list behavior.

## Corrections to the reviewer response

- Claims that the current benchmark still hard-codes a Llama label mix source revisions. That defect belongs to the original supplied runner; the newer branch already records the supplied model filename and complete shared-prefix length. Historical raw measurements remain unchanged.
- A duplicated initial BOS is not established for the tested chat templates. The earlier local tokenizer checks support the delimiter-in-content concern; they do not prove every template produces a leading duplicate BOS.
- The suggested fallback `CMAKE_CURRENT_SOURCE_DIR/../..` would resolve to `examples`, not the fork repository root, from `examples/nodelift/native`. The documented `-DLLAMA_SOURCE_DIR="$PWD"` override is correct when run from the repository root. No incorrect automatic fallback was added.
- The source's deferred-draft option is disabled by default and the binary's extra work is already disclosed. Static reasoning about saved operations is not a measured speedup.

## Actual framework rebuild

A fresh NodeLift framework cross-build completed for iOS arm64, deployment target 17.0, Release configuration, using CMake 3.22.1 and the pinned upstream source. `Headers/core.h` is present and matches the source byte for byte. [Build identity](ios-framework-build.json). The build ran from a temporary local source copy after generation in the iCloud-backed checkout stalled. This verifies the complete framework packaging fix, not just the minimal fixture. It does not exercise a phone, verify model output, or create a signed companion app.

## Release boundary and remaining work

The framework header change and documentation are source updates. The existing macOS prerelease tag, binary and published checks are immutable. No Android APK or iOS companion release, installation, camera/pairing test, sustained thermal test, or distributed speedup follows from this assessment.

GLM 5.3 Max returned its completed core-source review after the scheduled reset window. The completed response and our disposition follow below. Gemini has also completed scoped localization, graph, QR-protocol and About assessments; see the [product adjudication](PRODUCT-REVIEW.md). Historical records remain evidence of what happened at the time.

## Completed GLM core-source review

The browser's GLM 5.3 selection and Max effort were checked for this request. The [actual final response](glm-core-review.txt) reviews the supplied original `core.h`, `core.cpp` and `bench.py` at fork commit `42458074580813661f1a35fa8da60107ee796fe7`. It reports static analysis, not NodeLift execution. It also consulted upstream `master/include/llama.h`; we independently compared the relevant callback contracts against the pinned `ddf48f85c933c1f438212a02eb21e7b001d2d37d` header. Document-generation checks performed by the service are not software tests.

| GLM finding | Independent disposition |
| --- | --- |
| F1: hard-coded special-token parsing and sequence-start insertion | The delimiter behavior and extra shared BOS were already reproduced locally in the earlier tokenizer checks. No model-following exploit was demonstrated. Disabling special-token parsing on an entire rendered chat template would also remove legitimate template controls, so that suggestion is not a complete fix. The published input-trust limitation remains. |
| F2: all errors discard KV state; a narrower reset may expose stale logits | Source confirms the conservative reset, including invalid JSON. It also confirms that `cached.insert` precedes `best`. The outer reset currently protects that exception path. No incorrect output was reproduced. We retain the reset; improving cache retention requires fault injection and invariant tests rather than removing a safeguard. |
| F3: result serialization can throw outside the C-boundary catch | Confirmed as a static allocation-failure path, already identified by Gemini. No crash was reproduced. A bounded allocation-failure contract and fault tests remain open; `strdup` itself returns null on allocation failure rather than throwing a C++ exception. |
| F4: tokenizer fingerprint is not a model identity | True, intentional, and insufficient to establish an active identity defect. The committed host separately records target/draft SHA-256 and checks remote job/reply model hash, token-ID fingerprint, prefix hash, epoch and job ID. Different target and draft weights are expected. No model substitution was demonstrated. |
| F5: limited sample and ambiguous benchmark metadata | Six pairs per size are exploratory; no general confidence estimate is inferred. The current runner already fixed the model filename and shared-prefix accounting. The phrase `no model load` meant that loading was outside the timed intervals, but was ambiguous. Both future runners now say this explicitly. Historical measurements are unchanged. |
| F6: model loading cannot be interrupted via this wrapper; backend cancellation differs | Confirmed in the pinned source: the wrapper does not set the available model progress callback, and the context abort documentation is CPU-scoped. The overly broad `Cancel aborts the current call` header comment is corrected in both repositories. This is a contract correction, not newly implemented load cancellation or a measured GPU cancellation bound. A runtime change still needs cancellation-during-load tests. |
| F7-F12: detokenization, context/flash-attention limits, diagnostic wording and redundant cache work | The follow-up supplies individual triggers, adjudicated below. These are bounded interface/portability and exploratory-benchmark limitations, not demonstrated new speed or correctness failures. |
| F13/F14: cache and handle-lifetime invariants appear sound | This is the reviewer's static conclusion. Existing strict checks remain bounded to their named binaries; the review does not prove absence of races or memory errors. |

The [completed follow-up](glm-core-followup.txt) explicitly downgrades F4 to informational/by-design, retracts the alleged load-timing contradiction, recognizes the corrected current runner and agrees that preserving the conservative reset is appropriate. Its new context-quality claims remain hypotheses, not measured degradation.

- **F7:** `text` omits special-token spellings intentionally. The token array is the authoritative token record; rendered text is not promised to round-trip controls.
- **F8:** requested/effective context and model training limits are distinct. A context beyond training may need model-specific scaling/quality qualification; degradation was not measured here. Forced flash attention is a portability limit, not proof of failure on any named supported device.
- **F9:** a zero-token result can receive the misleading `prompt exceeds context` message. This is a source-visible diagnostic issue conditional on a tokenizer returning no sequence-start tokens for empty input; no model-specific reproduction was performed in this assessment.
- **F10:** the C ABI consumes NUL-terminated input and supplies `nl_free_string` for allocator compatibility. A raw embedded NUL is not valid JSON text; an escaped JSON `\u0000` is different. No truncation of valid escaped JSON or actual cross-CRT allocator failure was demonstrated.
- **F11:** the default path can re-evaluate one extra retained token. The experimental option already changes that condition and remains disabled by default. A reduced operation count alone is not evidence of a useful speed gain.
- **F12:** the original synthetic benchmark inserted a separately tokenized BOS in its suffix. Both arms shared it, and prior corrections record the actual prefix length. These remain synthetic prompts, not representative production workload evidence.

The initial answer is preserved where corrected. The separate GLM performance assessment remains in progress. All requested product assessments are not yet complete; the automation remains active.
