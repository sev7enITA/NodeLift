# Companion 0.2.7, build 9

This release corrects the full-color identity and pairing failures caused by a host address retained after a hotspot/DHCP change. The host default is now `--address auto`; Add device checks the current private IPv4 route and binds that interface before issuing a QR. An explicit `--address` remains fixed and is rejected when no longer assigned. The loopback dashboard remains available while the network is unavailable.

A new address uses its own pinned TLS certificate. Existing saved endpoints do not silently migrate: scan a fresh QR and confirm the computer identity. Enrollment, revocation and measurement records are retained. No certificate or hostname checks are disabled, and no wildcard LAN listener is introduced.

The provided Oppo Find N5 log showed two camera-ready/result sequences followed by socket timeouts of about six seconds, with no recorded camera failure. The owner confirmed both devices were on the Xiaomi hotspot. Inspection found the running host bound to an address no longer assigned to the Mac. The exported `default_network_transport` was cellular, which does not prove Wi-Fi was absent. Raw owner diagnostics, addresses, invitations and device identifiers are not included in this evidence directory.

Android now selects a matching connected Wi-Fi/Ethernet route for paired-host requests when available, retaining OS routing for hotspot/tethering cases. This routing code compiled; physical route selection remains unqualified. Diagnostic export adds available transport categories and stable route events without addresses or credentials. A timeout and a TLS failure produce different localized guidance.

The approved 3D emblem is packaged in Android/iOS icons and headers and shown in the GitHub README. HarmonyOS source artwork is updated; no native HAP was built. Android uses the simplified mark for its monochrome notification icon.

Graph motion and color were checked in an isolated browser fixture. All values in [the screenshot](graph-synthetic.png) are synthetic. Color and width represent accepted draft token share, not compute utilization or pooled memory. Offline/unknown/history/fallback branches have automated coverage. The toggle was checked in the browser; reduced-motion and hidden-tab behavior are implemented but were not manually OS-qualified.

See [build checks](build-checks.json). The 24 host tests include a simulated address change with real TLS/SAN verification; macOS loopback binding is adapted in that test, so this does not constitute a physical hotspot migration test. Thirteen JVM tests passed, iOS was built unsigned and native inference libraries are byte-identical to 0.2.6. No additional GLM/Gemini review was obtained for this patch. Earlier reviews remain scoped to their original changes.

There is no physical-phone inference speedup or target-model RAM pooling claim in this release. iOS still requires personal Apple signing/provisioning; TestFlight/App Store distribution is not available.
