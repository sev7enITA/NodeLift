# Mobile downloads and installation

Updated 1 November 2026. Companion version **0.2.6**, build **8**.
The [public download section](https://www.fabriziodegni.com/NodeLift/#downloads)
links directly to the [GitHub prerelease assets](https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.6).
The companions offer English (default), Simplified Chinese and Italian.

| Platform | Download | Installation status |
| --- | --- | --- |
| Android ARM64, API 26+ | Debug-signed APK | Laboratory package; physical native-inference qualification remains open |
| iPhone / iPad, iOS 17+ | Unsigned IPA or compiled `.app` ZIP | Compiled for physical ARM64 devices; requires your own signing and provisioning |
| HarmonyOS devices retaining APK support | Same Android APK, for a compatibility trial | Requires ARM64 and Android API 26+ compatibility; Huawei installation has not been tested |
| Native HarmonyOS / HarmonyOS NEXT | No compiled HAP available | ArkTS source candidate only; SDK build, signing and device qualification pending |

## Android and APK-compatible HarmonyOS

1. Confirm the OS accepts Android APKs and meets the ARM64 / API 26 requirements. A HarmonyOS marketing version alone does not establish compatibility. The APK is **not a native HarmonyOS package and is not the NEXT installation path**.
2. Download `NodeLift-0.2.6-android-debug.apk` from the release. Verify its SHA-256 against the public build manifest.
3. Install with Android's package installer, authorizing that source only as needed. The laboratory build uses the existing debug signing identity. Keep the earlier app's data unless you deliberately intend to reset it.
4. Start NodeLift on the computer, open its dashboard and choose Add device. Tap **Scan QR** in the companion, scan the desktop code, confirm the computer, then keep the companion visible for the first test. See the [QR pairing guide](https://github.com/sev7enITA/NodeLift/blob/main/docs/QR_PAIRING.md).

Huawei documents APK and native HAP as separate package paths for its older and newer OS generations; this does not qualify NodeLift on a particular handset. See [Huawei's package distinction](https://developer.huawei.com/consumer/en/doc/harmonyos-guides/gameservice-gameplayer-huawei).

## iOS and iPadOS

`NodeLift-0.2.6-ios-unsigned.ipa` contains the same compiled device app as the ZIP under `Payload/NodeLift.app/`. All app file bytes are identical to `NodeLift-0.2.6-ios-unsigned.zip`; the IPA is a packaging convenience, not a new build. macOS ZIP metadata is excluded. The native Metal/CPU framework and third-party notices remain included.

**Neither archive installs by tapping its link in Safari.** There is no Apple distribution signature, embedded provisioning profile, TestFlight invitation or App Store release. The archives do not contain a developer's keys or device provisioning data.

For an existing developer signing workflow, use the unsigned IPA and sign the app and embedded framework with an appropriate profile for your device and app identifier. Follow that workflow's documented entitlement and provisioning requirements. Installing this package has not been tested on a physical iPhone.

The reproducible Xcode route is:

1. Check out the `v0.2.6` source tag, including the pinned native dependencies. Follow the repository's native build prerequisites.
2. Run `./scripts/build-ios.sh` on a Mac with Xcode, CMake and XcodeGen. This compiles an unsigned device app.
3. Open `apps/ios/NodeLift.xcodeproj`, select the NodeLift target and configure **Signing & Capabilities** with your own Apple development team and an app identifier that team can provision. Do not reuse another project's provisioning profile.
4. Connect an iPhone or iPad, select it as the run destination, and let Xcode create the required development provisioning. Complete the device's trust / Developer Mode steps when required by Xcode and iOS.
5. Run the companion, allow local-network access and pair it with the computer. Keep it in the foreground during initial tests.

For distributing signed builds to testers, use Apple's supported registered-device or TestFlight route. A generic unsigned IPA download does not grant installation rights. See [Apple: distribute to registered devices](https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices).

## Native HarmonyOS and HarmonyOS NEXT

The [ArkTS project](https://github.com/sev7enITA/NodeLift/tree/main/apps/harmony) currently targets API 23 or later and implements a network-qualification candidate. It has **no native model loader or LLM worker**. Its TLS, pinning and lifecycle behavior still need toolchain and physical-device validation.

On 1 November, this build environment had no DevEco Studio, HarmonyOS SDK, `ohpm`, `hvigor` or `hdc`. The official [DevEco Studio download](https://developer.huawei.com/consumer/en/deveco-studio/) led to HUAWEI ID sign-in. No compiler run or HAP was produced. The owner subsequently reported completing Huawei sign-in and requested postponement because the build Mac has insufficient free disk space. SDK acquisition and the native build are therefore deferred; no HAP was produced.

Remaining release steps: obtain the official SDK covering API 23, compile and resolve ArkTS/API diagnostics, sign for the intended test device, verify pairing/network/cancellation behavior on Huawei hardware, then publish a versioned HAP and checksum with its exact compatibility scope. A model worker requires additional implementation and inference testing.

Huawei requires signing for installation on physical devices; debug profiles restrict the permitted device IDs. An AppGallery `.app` distribution bundle is not the same as a locally installable HAP. See [Huawei: package and signing FAQ](https://developer.huawei.com/consumer/fr/doc/app/agc-help-releasefaq-0000001110342644).

## About, references and updates

Open **About & References** in the control-room navigation or from the companion header. The section shows the installed component version, Fabrizio Degni’s authorship, official websites, repository, technical references and licenses. **Check releases on GitHub** opens the release list in your browser; compare its release notes with the installed version. It does not run a background check or automatically install an update. On iOS and HarmonyOS, opening the browser can pause the worker through the existing background lifecycle.

## Integrity and measured scope

`NodeLift-0.2.6-build-manifest.json` inventories the APK, ZIP and IPA. `NodeLift-0.2.6-ios-ipa-manifest.json` also records the IPA input hash and byte-identical app payload. The portal's `data/mobile-downloads.json` records platform availability, sizes, SHA-256 values and download URLs.

Hash verification establishes the identity of the downloaded file. Compilation and packaging establish neither successful installation nor device inference acceleration. Phone memory is not yet exposed as shared model capacity; capacity sharding remains planned.

See the [iPhone distribution guide](https://github.com/sev7enITA/NodeLift/blob/main/docs/IOS_DISTRIBUTION.md) for development signing, ad hoc devices, TestFlight and the intended App Store companion. The current IPA is unsigned.

Support logs can be exported without USB from **About & References → Diagnostics** in companion 0.2.6. [Diagnostic scope and limitations](https://github.com/sev7enITA/NodeLift/blob/main/docs/MOBILE_DIAGNOSTICS.md).
