# Integration validation — 1 November 2026

This change is host 0.3.0 preview. Mobile binaries remain the previously released 0.2.2. No phone speedup or pooled-memory claim is added.

## Automated checks

- 75 host tests: existing inference/protocol/gateway/startup checks plus model imports, invalid headers/split files, offsets/overruns, actual file length, cancellation, stale transfer identities, crash-leftover cleanup, immutable Hub metadata, SHA-256 corruption and size mismatch, redirect allowlist, provider key isolation, loopback endpoint restrictions, no automatic retry/fallback, SSE completion/Unicode/truncation, partial-line deadline/size checks, retained socket cancellation, explicit client backend routing, unknown usage omission, HTTP admin/origin separation, worker-start failure recovery, partial disk-write rejection, cleanup errors, registry backup recovery, malformed network data and generator cleanup.
- LM Studio adapter: TypeScript build and all 3 stream tests pass.
- Canonical English/Chinese catalog parity and generated asset freshness pass; JS runtime tests pass for default language, persistence, switching, fallback, parameter isolation and blocked storage.
- Existing DistAI evidence verifier passes. This is reproducibility of published evidence, not a new DistAI hardware test.

Network tests use mocked metadata/transports or local test servers unless explicitly listed below. Tiny GGUF header fixtures test the importer; they are not executable language models.

## Real observations

[Sanitized dashboard evidence](live-evidence.json) contains:

1. Public Hugging Face repository inspection from the GUI, exact Qwen commit `9217f5db79a29953eb74d5343926648285ec7e67` and license link.
2. Actual download of `qwen2.5-0.5b-instruct-q4_k_m.gguf`: **491,400,032 bytes**, verified SHA-256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`, completed atomic import. The browser then selected that downloaded file, applied native configuration and generated **HELLO**. Previous target configuration was restored.
3. An existing GGUF path was registered from the GUI without copying its weights.
4. Public OpenRouter catalog request succeeded, with 433 text-output models in the filtered snapshot. No key was entered and **no cloud generation was sent**. Catalogs/prices change over time; this is a point-in-time observation.
5. Actual NodeLift → local LM Studio server → `qwen3.8-27b` text generation succeeded, returning **HELLO**, with provider-reported usage. An earlier 8-token request completed with no visible text; the UI now explains this case instead of implying a visible response. A 128-token budget returned 30 provider-counted completion tokens and visible text. These counts include whatever the provider counts as completion; they are not equivalent to visible words or NodeLift token IDs.
6. The revised `read1` stream parser was separately exercised against the real LM Studio server: [stream-evidence.json](stream-evidence.json) records output, usage and the source digest used for that probe.
7. [Final host/gateway probe](final-smoke.json) records the tested implementation commit, an actual call through NodeLift’s client-facing OpenAI gateway to local LM Studio, a native run, and both catalogs after the GLM-driven fixes. No cloud generation was sent.
8. Browser DOM/AX checks confirmed native/cloud/local-server controls, catalog/model loading, key-free public catalog retrieval and Chinese/English model-library messages. Screenshot capture timed out on the computer; no screenshot-based visual pass is claimed.

Tiny one-prompt timings in these files are **smoke-test timings**, not statistically controlled speed comparisons, and must not be promoted as acceleration results. The imported 0.5B native model and the 27B LM Studio model are different models with different runtime states.

## Limits and remaining qualification

- oMLX was source-reviewed and its documented OpenAI text contract is supported by the generic loopback bridge. **An oMLX runtime was not installed or exercised**; its cache/distributed scheduler is not incorporated into NodeLift.
- OpenRouter SSE/error handling is tested with fixtures, and its public catalog is live-tested. Real authenticated generation, billing, provider policy compliance and model-specific sampling remain unqualified.
- Public single-file GGUF downloads only; gated/private models must be downloaded manually after accepting their own terms. Split GGUF, safetensors/MLX directory import, automatic format conversion and download resume are not implemented. Recent crash partials are retained outside the catalog; owned partials older than 24 hours are cleaned on the next library initialization.
- Full multi-gigabyte browser file upload was not separately exercised through the native file chooser; chunk/offset/finalization paths have automated checks. Actual Hugging Face download and path import were exercised through the GUI.
- Keys/endpoints/catalogs for external engines are session-scoped. Stop cancels NodeLift's request but cannot undo provider work already accepted or charges incurred. Silent cloud fallback is never used.
- No Android/iOS physical-device run, sustained thermal test, new phone inference benchmark or new mobile package was produced for this host integration update.
- [GLM 5.3 Max reviewed the initial two new backend modules](GLM-REVIEW.md). [Independent adjudication and fixes](REVIEW-RESOLUTION.md) address its confirmed findings. The final fixes were tested locally; GLM did not re-review the final revision. No Gemini 4 High review was performed for this patch.
- [GitHub CI for the initial integration commit](https://github.com/sev7enITA/NodeLift/actions/runs/41254977792) passed on Python 3.12/3.14, with the adapter/localization jobs also green. Follow-up source-check results are available in the repository Actions tab.
