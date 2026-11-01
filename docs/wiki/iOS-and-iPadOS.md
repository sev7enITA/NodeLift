# iPhone and iPad

The [0.2.3 iOS ZIP](https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.3) contains an **unsigned device build**. It cannot be installed as-is: Apple signing and provisioning are required. There is no TestFlight or App Store release.

To build from source, install Xcode and xcodegen, then run `./scripts/build-ios.sh`. Configure your signing team and provisioning in Xcode before installing on a device you own. The packaged native framework supports the candidate Metal/CPU path; compilation does not qualify it on a physical iPhone.

After installation:

1. Associate using a fresh invitation from the authenticated host dashboard.
2. In Files, choose the same complete GGUF draft configured on the host, up to 1 GiB. The companion imports and verifies it locally.
3. Set Metal/CPU, context, thread and battery limits; enable the draft engine and resume the session.
4. Keep the app in the foreground. Backgrounding or locking pauses the session.
5. Compare a small phone-proposal run with the same host-only baseline before longer trials.

English is the default; Simplified Chinese and Italian are selectable. OS permission-dialog language follows iOS policy. Local-network permission strings are included for all three languages.

**Qualification remains open:** physical installation, sustained Metal/CPU inference, thermal behavior and measured phone speedup. [Source and build evidence](https://github.com/sev7enITA/NodeLift/blob/main/docs/LOCALIZATION.md).

Huawei HarmonyOS NEXT needs the separate ArkTS candidate. An Android APK or this iOS build does not qualify it; no HAP is available.
