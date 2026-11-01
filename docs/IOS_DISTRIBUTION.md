# Installing NodeLift on iPhone and the distribution path

The current downloadable IPA is an **unsigned build artifact**. Downloading it in Safari does not install NodeLift. An IPA is a package format; it is not an Apple signing entitlement or an App Store approval.

## Personal device testing today

Use the source project with Xcode on a Mac:

1. Build the project following the [iOS instructions](wiki/iOS-and-iPadOS.md). Select your Apple development team in Signing & Capabilities and let Xcode create a valid development provisioning profile.
2. Connect and trust your iPhone, choose it as the run destination, and enable Developer Mode if iOS requests it.
3. Build and run the app with your own signing identity. Xcode can subsequently use wireless device connections once pairing and network requirements are met.

Alternatively, an Apple Developer Program member can export an **ad hoc signed** IPA for registered device identifiers and install it using Apple's supported device tools. The existing unsigned download cannot be converted to a generally installable app merely by renaming or unzipping it. No signing certificate, provisioning profile or private key belongs in the public repository.

## Planned companion distribution

| Stage | User experience | Remaining requirements |
| --- | --- | --- |
| Development / ad hoc | Xcode or an IPA provisioned for the specific device | Team, device registration where required, signing and actual installation test |
| TestFlight beta | Install TestFlight, accept an invitation and install the companion | Apple Developer Program, App Store Connect record, signed upload, processing and applicable beta review |
| App Store | Install and update the NodeLift companion normally | Final signed submission, accurate privacy declarations, screenshots, support/privacy URLs and Apple review |

The intended public product is a companion app. It does not require the whole desktop orchestration engine on the iPhone. It contributes only within supported iOS lifecycle, memory and thermal limits. Background execution is not guaranteed, and the current worker pauses when the app goes into the background.

TestFlight and App Store are distribution plans, not current availability claims. There is no public NodeLift TestFlight invitation or approved App Store listing in this release evidence. Do not label an unsigned GitHub IPA as an App Store build.

## Apple references

Checked 1 November 2026:

- [Distribution methods and signing](https://help.apple.com/xcode/mac/current/en.lproj/dev31de635e5.html)
- [Distributing to registered devices](https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices)
- [Beta testing and releases](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases)
