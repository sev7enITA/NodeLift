# NodeLift 0.1 — qualification companions

Historical checkpoint, 31 October 2026. The owner selected **NodeLift** as the name; the original ExpandMyHW directory preserves paths and research. This first pairing/measurement implementation was **not a distributed inference engine**. For the current release, use the [engine guide](ENGINE_0_2.md), [QR pairing guide](QR_PAIRING.md) and [changelog](../CHANGELOG.md). Implementation gaps below describe version 0.1, not all later versions.

## Implemented at this checkpoint

- Host Python without PyPI dependencies: HTTPS node server, loopback web dashboard, five-minute single-use invitations, registration/revocation, jobs restricted to known tests and exportable results.
- Android Kotlin: native UI, `connectedDevice` service, model detection, physical/system-available RAM, thermal state, transport and battery indicator; session encrypted with Android Keystore.
- iOS SwiftUI: native UI, explicitly verified host TLS certificate, Keychain credentials, thermal status and process memory headroom; background pause, with no permanent-daemon claim.
- HarmonyOS ArkTS: **source candidate** with UI, pairing, SPKI pinning and foreground network tests. In-memory tokens only; CPU tests, RAM readings and inference disabled. Requires SDK API 23+ to disable redirects. Not compiled or installed: DevEco/SDK and Huawei signing were unavailable in the inspected environment.
- Quick network test: 32 application RTTs with a 64-byte response and four downloads/uploads per 16 KiB/1 MiB size; one warmup excluded. Diagnostic only: p95 from 32 samples is exploratory, not a stable tail estimate.
- Android/iOS paced network test: 600 RTTs in three 200-sample groups with requested pauses of 0/30/60 ms. Dashboard shows groups separately. Server-assigned connection IDs expose TCP/TLS reuse. Actual OS delays may exceed requested pauses.
- Android/iOS synthetic FP32 256×256 matvec CPU test, approximately 1.5 seconds, one thread. Measures that kernel/runtime, mostly in cache; **does not predict DRAM bandwidth, GPU, NPU or tokens/s**.

Not implemented in 0.1: phone GGUF loading, distributed KV cache, remote draft/verify, layer sharding, Harmony GPU/NPU backend, LM Studio generator or Ollama integration. No advantage over the Mac had been demonstrated.

## Starting the computer host

Historical host prerequisites: Python 3.11+ with SQLite 3.35+ and OpenSSL on PATH. Do not install certificates in the computer/phone's global trust store: the companion uses the invitation identity only for NodeLift.

```sh
cd host
python3 -m nodelift.host --address YOUR_PRIVATE_LAN_IPV4
```

Use the Mac's private IPv4 on the same network/hotspot as the devices. Default 127.0.0.1 works only for same-computer tests. Open the private dashboard link printed by the process. Its fragment token is a local secret; never publish it.

1. Select **Add device** in the dashboard.
2. Transfer and paste the invitation into the phone companion. It lasts five minutes and can be used once; do not forward it to outsiders. Pairing was manual in 0.1, without QR scanning or mobile discovery.
3. Select **Pair and enable node**. The companion only makes outgoing connections to the computer; it exposes no phone server.
4. Start **Quick network**, **Paced network** or **CPU test** from the dashboard where supported.
5. Export JSON samples without credentials. **Pause** on the phone stops availability; **Revoke** on the computer invalidates the token. **Forget computer** removes only local credentials; use Revoke to invalidate the server token too.

The server listens only on the selected address. The OS must allow incoming local connections to Python. Firewall, hotspot, system permissions and router settings were not changed. Optional `--bonjour` announces the service through `dns-sd` where available; it does not replace pairing or enable discovery in 0.1 companions.

### If Add device does not respond

Opening only `http://127.0.0.1:9868` in a new tab does not transfer the original tab's private session. The corrected 0.1 dashboard displayed an Italian warning and disabled actions until authentication was valid. Reopen the complete server-printed link. For an assistant-started session with private log `~/.local/share/nodelift/host-session.log`, double-click `scripts/open-dashboard.command`: it verifies the session and opens the browser without printing the secret. Reinstallation is unnecessary.

Browser verification on 31 October covered the unauthenticated warning/disabled controls, restored authentication and successful invitation creation. Opening a session link in the same tab also reloads when only the URL fragment changes. No mobile protocol or permission changes were needed.

The initial certificate lasts 30 days. An IP change requires a new `--state` and pairing because the identity contains the IP SAN. Guided rotation, stable DNS and QR UX were future work at this checkpoint. Default state is private `~/.local/share/nodelift`; server tokens are stored only as hashes, while certificates/private keys remain on the computer.

## Compilation and installation

### Android

JDK 21, Android SDK 36 and Gradle wrapper 8.13. Build checked with Android Gradle Plugin 8.12.0 and Kotlin 2.1.20.

```sh
./scripts/build-android.sh
```

APK: `apps/android/app/build/outputs/apk/debug/app-debug.apk`; deliverable copy: `artifacts/NodeLift-0.1.0-android-debug.apk`. This was a **debug build**, not a Play Store release. Initial checks did not include physical installation or OEM HyperOS/ColorOS tests; the later Xiaomi session is recorded below. Do not treat this APK as a native Huawei NEXT companion.

### iOS

```sh
./scripts/build-ios.sh
```

`apps/ios/NodeLift.xcodeproj` is regenerated from `project.yml` with XcodeGen. Release simulator/device builds succeeded with signing disabled. **An unsigned app cannot be installed directly on an iPhone**: select a development team and device in Xcode, then sign/install through the account's supported process. No Apple certificate/account was created or altered; nothing was submitted to TestFlight/App Store.

The iOS companion does not automatically disable screen locking. Keep it active during measurement; locking/backgrounding pauses it. Report screen-on trials separately because they affect thermals.

### HarmonyOS NEXT

Open `apps/harmony` in DevEco Studio with a compatible API 23+ SDK, configure device signing and resolve toolchain differences. This is **an unperformed step**, not a verified procedure. “HarmonyOS NEXT 7” is the owner's reported OS name/version; read actual API level/build on the phone. No unbuilt HAP has verified compatibility.

## Protocol and boundaries

`POST /v1/pair` consumes the invitation; other node APIs require a revocable bearer. `/v1/heartbeat` updates telemetry and delivers a job once. `/v1/probe` and `/v1/upload` cap payloads at 1 MiB. `/v1/result` accepts only the running job's owner within 120 seconds; replays, revoked tokens and late results are rejected. Clients stop tests after approximately 90 seconds and check thermals between requests/iterations. One operation's network timeout may extend the between-operation limit.

If a client closes during a test, the job can remain running until timeout; it is not automatically resumed and receives no fabricated result. Credentials do not authorize shell execution, code downloads or server-requested arbitrary allocations. Inference required a separate protocol design.

Android “available memory” and iOS `os_proc_available_memory()` have **different meanings**: system-level availability versus process headroom. Do not add them or treat them as validated allocatable budgets. The dashboard reports observed platform data, not promised reclaimed RAM.

HTTPS tests include application stack, queueing, TLS and copies. They are not iperf, PHY bandwidth or a future tensor protocol's latency. The quick test does not establish reliable p99; large-transfer samples remain few. More samples, randomized order, sessions, concurrent load and sustained physical tests are required by `BENCHMARK_PROTOCOL.md`.

## Verification status

**Later physical update, 31 October:** the owner installed the companion on the Xiaomi 17 Ultra and confirmed its hotspot served the Mac. Pairing, heartbeat, two paced tests, one quick test and synthetic CPU work completed on the device. [Samples and report](../research/measurements/2026-10-31-xiaomi-hotspot/REPORT.md). This supersedes the initial absence of a physical Android test below; other devices, sustained thermal tests and LLM inference remained open. The Android 0.1 paced-test summary displays only the first 32 RTTs: use the dashboard/report for full groups; a mobile correction had not yet shipped at this checkpoint.

Initial build checks, before the Xiaomi session:

- 14 host tests passed: untrusted TLS, expired/reused invitations, authentication/revocation, payload limits, job ownership/lease, replay, timeout, dashboard origin and secret-free exports.
- Actual Swift client tested against local HTTPS on **macOS**: pairing, authenticated download/upload, heartbeat and rejection of an altered fingerprint. Not an iPhone test.
- Android instrumented test written and test APK compiled. The dedicated emulator failed to finish startup (`mprotect ... Permission denied`, ADB offline); no instrumented Android pass was claimed.
- Dashboard browser checks covered loading, empty state and invitation creation/closure. Screenshot capture timed out; no full visual qualification was claimed.
- No physical phone was connected to the tools during those initial checks. No hotspot, sustained thermal or LLM benchmark was performed in that initial phase.
- Gemini 4 High completed a **design** review with documented adjudication; GLM 5.3 Max was still capacity-limited. Neither was credited with a source audit at that checkpoint.

Logs are in `artifacts/`. Research details remain in the DistAI dossier and initial assessment.
