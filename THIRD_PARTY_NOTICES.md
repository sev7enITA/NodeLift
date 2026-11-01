# Third-party components

- Native inference uses [llama.cpp](https://github.com/ggml-org/llama.cpp), MIT license, at the immutable revision in `native/llama.lock`. Its GGML backends and their upstream notices are retained in the downloaded checkout. It is not original NodeLift inference math.
- The native JSON ABI uses the nlohmann JSON header bundled by that checkout (MIT).
- The token-ID fingerprint uses Igor Pavlov's SHA-256 implementation bundled in llama.cpp `vendor/hash/sha256` (public domain) and its bundled rotate-bits helper; upstream notices accompany the checkout.
- `research/distai/source` is an attributed research snapshot, with its own LICENSE and THIRD_PARTY_NOTICES. NodeLift does not claim authorship of those files.
- Model weights are downloaded separately, never included in Git or APK. Follow the respective model repository licenses. Control-model revisions and SHA-256 values are in `profiles/control-models.json`.
- The NodeLift emblem was generated for this project with image generation; the compact geometric SVG is original project artwork. Neither uses film artwork, logos or characters.

Android APK and the iOS app bundle include copies of the llama.cpp, JSON and SHA-256 notices from `native/licenses`. The LM Studio adapter uses the separately installed `@lmstudio/sdk` package under its own package license; dependencies and integrity hashes are locked in its package-lock.

## QR pairing (companion 0.2.6)

- The desktop vendors Project Nayuki’s [QR Code generator v1.8.0](https://github.com/nayuki/QR-Code-generator/tree/v1.8.0), MIT. The upstream TypeScript source and generated JavaScript retain the license header in `host/nodelift/vendor`. Generation runs entirely on the local dashboard.
- Android uses [CameraX 1.6.2](https://developer.android.com/jetpack/androidx/releases/camera) from AndroidX for lifecycle-bound camera capture, and [ZXing core 3.5.3](https://github.com/zxing/zxing/tree/zxing-3.5.3) for offline decoding, both Apache-2.0. Notices are bundled under `assets/licenses`. No Google Play services or external scanner app is required. CameraX/AndroidX transitive dependencies retain their packaged notices.
- Companion 0.2.5 used ZXing Android Embedded 4.3.0. That legacy scanner dependency is removed in 0.2.6; its prior-release notice is retained for provenance.
- iOS uses Apple’s AVFoundation QR metadata API. Camera frames stay on-device.

## Research acknowledgements

See [Acknowledgements and research credits](docs/ACKNOWLEDGEMENTS.md) for named projects, contributors, study scope and direct visit links. Research citations are separate from the dependency notices above.
