# Add an Android phone

[Download the 0.2.10 ARM64 laboratory APK](https://github.com/sev7enITA/NodeLift/releases/download/v0.2.10/NodeLift-0.2.10-android-debug.apk). It is debug-signed, not a Play Store release. Update an existing same-key installation without uninstalling to retain pairing. If the OS reports a signature conflict, stop and report it; do not erase the app’s data as a first workaround.

1. Keep the computer and phone on the same private network. The phone may provide the hotspot, but this topology must be measured rather than assumed fastest.
2. In the authenticated host dashboard, choose **Add device**. In the companion choose **Scan QR**, scan the desktop code and confirm the computer. Invitations are single-use and expire after five minutes.
3. Allow the session and check that the dashboard shows the device. Network diagnostics can run at this point; this is not yet an LLM-ready node.
4. On the host, select and apply the small control target/draft pair. On Android choose **Download draft from Mac and enable**. The 0.5B control draft is about 491 MB; its SHA-256 is checked.
5. Wait for the draft-ready status, enable proposals and resume the node. Select **Phone proposals** and that node on the host.
6. Compare against **Computer only** and **Local proposals** with the same prompt, target, settings and actual output length. Record failed and slower attempts too.

The current worker uses ARM64 CPU. GPU/NPU acceleration is not enabled. The mobile GGUF limit is 1 GiB; context is 512–4096 and CPU threads 1–8. Battery and thermal checks may pause work. Changes to context/threads apply at the next model load.

**Language** supports English, 简体中文 and Italiano. Pairing does not automatically share the phone’s RAM. A foreground service is not evidence of sustained background execution on every Android vendor.

[Detailed engine guide](https://github.com/sev7enITA/NodeLift/blob/main/docs/ENGINE_0_2.md) · [Benchmark protocol](https://github.com/sev7enITA/NodeLift/blob/main/BENCHMARK_PROTOCOL.md)

See the [QR pairing guide](https://github.com/sev7enITA/NodeLift/blob/main/docs/QR_PAIRING.md) for camera permissions, manual fallback and invitation lifecycle.

Version 0.2.6 replaces the legacy QR scanner with CameraX, adds retry/cancel feedback, and distinguishes disabled, pressed and busy controls. Its Xiaomi scan repair still needs an on-device trial. See [validation scope](https://github.com/sev7enITA/NodeLift/blob/main/docs/evidence/companion-0.2.6/README.md).

Version 0.2.8 adds installation-scoped enrollment identity and local dashboard session recovery. In the November 1 exploratory test, a Xiaomi completed the draft download and CPU calibration, but two network jobs timed out and stable remote inference could not be qualified. A draft-ready label is not proof of a working inference route. See the [exploratory QA report](https://github.com/sev7enITA/NodeLift/blob/main/docs/EXPLORATORY_QA_2026_11_01.md).

Version 0.2.10 organizes the companion into Home, Activity and Settings. Export logs directly from Activity. See [device assessment and KPI definitions](https://github.com/sev7enITA/NodeLift/blob/main/docs/DEVICE_ASSESSMENT_AND_KPIS.md). Physical accessibility and LLM speedup remain unqualified.
