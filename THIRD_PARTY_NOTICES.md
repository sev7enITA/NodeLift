# Third-party components

- Native inference uses [llama.cpp](https://github.com/ggml-org/llama.cpp), MIT license, at the immutable revision in `native/llama.lock`. Its GGML backends and their upstream notices are retained in the downloaded checkout. It is not original NodeLift inference math.
- The native JSON ABI uses the nlohmann JSON header bundled by that checkout (MIT).
- The token-ID fingerprint uses Igor Pavlov's SHA-256 implementation bundled in llama.cpp `vendor/hash/sha256` (public domain) and its bundled rotate-bits helper; upstream notices accompany the checkout.
- `research/distai/source` is an attributed research snapshot, with its own LICENSE and THIRD_PARTY_NOTICES. NodeLift does not claim authorship of those files.
- Model weights are downloaded separately, never included in Git or APK. Follow the respective model repository licenses. Control-model revisions and SHA-256 values are in `profiles/control-models.json`.
- The NodeLift emblem was generated for this project with image generation; the compact geometric SVG is original project artwork. Neither uses film artwork, logos or characters.

Android APK and the iOS app bundle include copies of the llama.cpp, JSON and SHA-256 notices from `native/licenses`. The LM Studio adapter uses the separately installed `@lmstudio/sdk` package under its own package license; dependencies and integrity hashes are locked in its package-lock.
