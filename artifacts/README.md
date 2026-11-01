# Current packages and historical evidence

Current companion: **0.2.5 / build 7**, [published assets and hash manifest](https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.5). Android is a debug-signed laboratory build; iOS is unsigned and needs provisioning. See [localization validation](../docs/LOCALIZATION.md) and [host integration validation](../research/integrations-2026-11-01/VALIDATION.md).

The dated sections below retain historical results; they are not the latest release index.

# NodeLift 0.2.1: build and validation

31 October 2026. Experimental native inference release. **No physical-phone LLM speedup, pooled RAM or production readiness is established.**

| Component | Observed result | Boundary |
|---|---|---|
| Host / protocol / HTTP | 26 automated tests passed, including fresh startup, authorization separation, lease failures and split Unicode streaming | Contract tests use stub inference where explicitly labelled |
| Native core | 29 real-weight correctness checks passed on M3 Max / Metal | Four prompts, bounded outputs; not universal numerical equivalence |
| Remote work | Four real-weight TLS fault cases passed: valid/wrong/error/dropped proposals | Emulated local node, not a physical phone |
| Client gateway | Live real-weight normal/stream equality, Unicode, disconnect cancellation passed | One configured small target, greedy only |
| LM Studio adapter | TypeScript build, three stream tests, real SDK handler → live engine passed | CLI installation stalled and was stopped; GUI/plugin runtime remains unverified |
| Android | 0.2.1 build 3 ARM64 APK built; APK signature verified; native library and license notices packaged | Debug-signed lab build; updated native APK not physically exercised yet |
| iOS | Complete Release device build including native Metal/CPU framework and notices succeeded | Unsigned; physical installation/rendering/inference open |
| HarmonyOS NEXT | Separate source candidate retained | No native engine, SDK build or HAP |
| External reviews | Actual Gemini 4 High and GLM 5.3 Max design and source responses received and adjudicated | Static model advice, not device/runtime certification |
| UI | Desktop functional checks and first Gemini visual review; iOS build/parse passed | Post-fix visual recheck limited, no physical iOS UI test |

Local artifacts: `NodeLift-0.2.1-android-debug.apk`; release packaging adds a source ZIP, an explicitly unsigned iOS app ZIP and a SHA-256 build manifest. Artifacts/logs are ignored by Git; downloadable assets belong on the GitHub prerelease. Weights, private state, signing keys and user prompts are excluded.

The observed Xiaomi test still refers to the 0.1 qualification companion. The new connected benchmark runner refuses offline/legacy nodes; its full physical sequence remains pending. See [engine guide](../docs/ENGINE_0_2.md), [measured results](../research/measurements/ENGINE_RESULTS.md) and [review adjudication](../research/reviews/ENGINE_REVIEW.md).

## Historical 0.1 checkpoint

The section below records earlier evidence only; current status is above.

# NodeLift 0.1.0: build and checks

31 October 2026. **Qualification companion: no distributed LLM engine implemented at this checkpoint.**

Same-day dashboard update: access restoration verified in the owner's tab, explicit missing-session warning, unauthenticated actions disabled and local `scripts/open-dashboard.command` launcher. Source archive/manifest updated; Android APK unchanged.

Later physical update: the owner installed the Android companion on Xiaomi 17 Ultra; pairing/heartbeat and four real jobs completed (quick network, paced network, CPU and a paced repeat). [Report and data](../research/measurements/2026-10-31-xiaomi-hotspot/REPORT.md). No LLM benchmark or sustained thermal test. The table preserves initial build checks before that session.

| Component | Observed result | Boundary |
|---|---|---|
| Host HTTPS + dashboard | 14 automated tests passed; invitation flow checked in browser | No physical phone paired during initial verification |
| Android | `NodeLift-0.1.0-android-debug.apk` and instrumented test APK compiled | Instrumented test did not run: ADB emulator offline/mprotect error; HyperOS/ColorOS still to test |
| iOS | Release device and simulator builds succeeded | Signing disabled; not installed on iPhone |
| Swift client | Pairing, transfers, heartbeat and wrong-certificate rejection checked over local HTTPS | Execution on macOS, not iOS |
| HarmonyOS | ArkTS candidate included in sources | DevEco/SDK/signing absent; no HAP produced |
| Gemini 4 High review | Design review completed and findings adjudicated | Not a source audit or hardware measurement |
| GLM 5.3 Max review | Attempted with Max effort | Service at capacity; no completed review |

Local historical deliverables:

- `NodeLift-0.1.0-android-debug.apk`: Android debug test build, not the Huawei NEXT companion.
- `NodeLift-0.1.0-source.zip`: host, apps, scripts, tests, documentation and attributed research. No pairing credentials, laboratory database or signing keys.
- `build-manifest.json`: SHA-256 hashes and source inventory. Binaries/logs are excluded from Git through `.gitignore`; this README remains tracked.

Logs: `host-tests.log`, `swift-protocol-check.log`, `android-build.log`, `android-test-build.log`, `ios-build.log`, `ios-device-build.log`, `android-emulator.log`.

These initial checks establish neither LLM speedup nor hotspot performance. See the [historical companion guide](../docs/COMPANION_0_1.md), [current changelog](../CHANGELOG.md) and [current downloads](../docs/MOBILE_DOWNLOADS.md).
