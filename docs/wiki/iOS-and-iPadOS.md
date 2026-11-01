# iPhone and iPad

The [public download section](https://www.fabriziodegni.com/NodeLift/#downloads) offers a **compiled, unsigned device build** as an IPA or `.app` ZIP. Both contain the same 0.2.6 app. It cannot be installed as-is: Apple signing and provisioning are required. There is no TestFlight or App Store release.

See the [download and signing guide](https://github.com/sev7enITA/NodeLift/blob/main/docs/MOBILE_DOWNLOADS.md) for package hashes and platform requirements.

To build from source, install Xcode and xcodegen, then run `./scripts/build-ios.sh`. Configure your signing team and provisioning in Xcode before installing on a device you own. The packaged native framework supports the candidate Metal/CPU path; compilation does not qualify it on a physical iPhone.

After installation:

1. Choose **Add device** in the authenticated host dashboard; use **Computer pairing → Scan QR** in the companion and confirm the computer.
2. In Files, choose the same complete GGUF draft configured on the host, up to 1 GiB. The companion imports and verifies it locally.
3. Set Metal/CPU, context, thread and battery limits; enable the draft engine and resume the session.
4. Keep the app in the foreground. Backgrounding or locking pauses the session.
5. Compare a small phone-proposal run with the same host-only baseline before longer trials.

English is the default; Simplified Chinese and Italian are selectable. OS permission-dialog language follows iOS policy. Local-network permission strings are included for all three languages.

**Qualification remains open:** physical installation, sustained Metal/CPU inference, thermal behavior and measured phone speedup. [Source and build evidence](https://github.com/sev7enITA/NodeLift/blob/main/docs/LOCALIZATION.md).

Huawei HarmonyOS NEXT needs the separate ArkTS candidate. An Android APK or this iOS build does not qualify it; no HAP is available.

See the [iPhone distribution guide](https://github.com/sev7enITA/NodeLift/blob/main/docs/IOS_DISTRIBUTION.md) for development signing, ad hoc devices, TestFlight and the intended App Store companion. The current IPA is unsigned.

Support logs can be exported without USB from **About & References → Diagnostics** in companion 0.2.6. [Diagnostic scope and limitations](https://github.com/sev7enITA/NodeLift/blob/main/docs/MOBILE_DIAGNOSTICS.md).
