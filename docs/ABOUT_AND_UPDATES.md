# About, references and update discovery

The control room and companion 0.2.4/build 6 include **About & References**. English is the default; Italian and Simplified Chinese are available.

| Surface | Where to open it | Version source |
| --- | --- | --- |
| Desktop control room | Navigation rail or footer | Authenticated local `/admin/about`, using the running host package version |
| Android | About & References below the app heading | Android package version name and build code |
| iOS / iPadOS | About & References in the header | App bundle version and build |
| HarmonyOS candidate | Expandable About & References below the heading | Runtime bundle metadata; source remains uncompiled |

The section identifies **Fabrizio Degni** as the project's creator and author, with links to the project showcase, personal website and LinkedIn. It also links to the source repository, architecture, comparison research, third-party notices and original-code MIT license.

## Updates

**Check releases on GitHub** opens the official repository's release list in the browser. Compare the installed companion version with the release notes and follow the [installation guide](MOBILE_DOWNLOADS.md). The control room identifies its host source preview separately: the host and mobile companions do not share one version number.

This is manual update discovery. Opening About does not contact GitHub or download/install an update. No automatic “latest version” or “update available” result is asserted. The links are fixed public HTTPS destinations without pairing or model data.

On iOS and HarmonyOS, moving to the browser may pause the node under the existing foreground lifecycle. Return to NodeLift and resume when ready. Opening the About sheet/dialog alone does not alter engine settings or pairing.

## Verification scope

The Android APK and unsigned iOS device app compile as 0.2.4/build 6. The Android signing identity and the packaged Android/iOS native engine binaries match 0.2.3; this is a companion UI update, not a native-engine rebuild.

Desktop checks cover runtime host metadata, unavailable/unauthenticated behavior, localized labels, narrow-screen overflow and external-link attributes. Catalog parity, placeholder checks, JavaScript/Swift formatters and focused host protocol tests pass. Physical Android/iPhone UI and installation checks remain open; no ADB device was connected during packaging. HarmonyOS/NEXT still requires its SDK build, signing and physical-device qualification.
