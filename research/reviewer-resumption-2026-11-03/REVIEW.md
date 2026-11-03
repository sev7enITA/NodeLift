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

GLM 5.3 Max was retried after the scheduled reset window. Availability and any completed review are recorded separately; an in-progress request is not an assessment. Localization, graph, pairing and About reviews must each be completed within their actual source/UI scope before their unavailable-review notes are replaced. Historical records remain evidence of what happened at the time.
