# Mobile downloads

The [NodeLift portal download section](https://www.fabriziodegni.com/NodeLift/#downloads) links to companion 0.2.6/build 8 packages and checksums.

| Platform | Current artifact |
| --- | --- |
| Android ARM64 / API 26+ | Debug-signed laboratory APK |
| iOS / iPadOS 17+ | Compiled ARM64 app, unsigned IPA and ZIP; personal signing and provisioning required |
| APK-compatible HarmonyOS | Same APK for an unverified compatibility trial; requires ARM64 and API 26+ support |
| Native HarmonyOS / HarmonyOS NEXT | ArkTS source candidate only; no compiled HAP or native LLM worker yet |

The iOS IPA is a byte-identical repackaging of the published device app, not a new binary build. It is not directly installable from Safari. There is no TestFlight or App Store release.

Read the [full installation and signing guide](https://github.com/sev7enITA/NodeLift/blob/main/docs/MOBILE_DOWNLOADS.md), [machine-readable platform inventory](https://www.fabriziodegni.com/NodeLift/data/mobile-downloads.json) and [release assets](https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.6).

A compiled or signed package does not establish physical-device installation, sustained inference or a speedup. The HarmonyOS native SDK build, signing and device qualification remain open.

[Release history](https://github.com/sev7enITA/NodeLift/blob/main/CHANGELOG.md) · [Portal changelog](https://www.fabriziodegni.com/NodeLift/#changelog)
