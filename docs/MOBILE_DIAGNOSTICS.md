# Mobile diagnostics and wireless support

Companion 0.2.6 adds an on-device support journal to Android and iOS. No USB connection or developer mode is needed to export it.

## After an error or crash

1. Reopen NodeLift if it closed. Leave the log in place until you have exported it.
2. Open **About & References → Diagnostics → Export diagnostics**.
3. Save the JSON report to Files or select a recipient in the system share sheet. Preparing the report does not prove that it was sent.
4. Include the action you took, approximate time, device model and whether the phone provided the hotspot. Do not send passwords, pairing invitations or model prompts.
5. **Clear diagnostics** deletes the app's journal and temporary export after confirmation. Copies you already saved or shared remain under your control.

English, Simplified Chinese and Italian labels are available. Diagnostic event identifiers stay stable across languages so reports can be compared.

## Recorded information

- App version/build, OS version/API and timestamped lifecycle, camera, connection, model-loading, job and update events.
- The Android export includes current default-network transport, thermal status, session and engine readiness. Version 0.2.7 also records available transport categories and `ROUTE_WIFI`, `ROUTE_ETHERNET` or `ROUTE_SYSTEM` when the request routing choice changes. These categories do not prove end-to-end reachability. That default route may differ from the hotspot interface used by the Mac. It never records SSIDs, IP addresses or host identities.
- Android managed exceptions: exception class plus at most 12 NodeLift stack frames, reduced to method symbols and line numbers. Exception messages, thread names and file paths are excluded.
- Android 11/API 30 and newer: historical process exit reason codes supplied by Android, including native crash and ANR reasons when available. Raw traces and OS descriptions are excluded.
- iOS: stable event identifiers and numeric error codes. MetricKit crash signal and hang events are reduced locally; the original diagnostic payload is never included.
- `reporter_build` identifies the build that wrote each record. An OS exit record collected after an upgrade does not establish which older build caused the exit.

The journal accepts no free-form prompt, QR, token, credential, model-path or network-response field. Diagnostic data is not attached to update checks, host heartbeats or browser links.

## Storage and limitations

The private journal rotates across three files of at most 128 KiB each. Exports exclude records older than seven days; expired records are pruned on subsequent journal use. A temporary JSON export is created only on demand and removed at the next app start, next export or explicit clear. Android disables app backup; the iOS journal is excluded from backup and protected by the platform's file protection. User-exported copies follow the storage/sharing service the user selects.

Recording is best effort. A full disk, termination during a write, severe memory pressure, native failure or unavailable OS diagnostics can leave a partial record. Android retains the system uncaught-exception handler. iOS does not install an unsafe signal handler. An iOS previous-active-session marker means **interruption of unknown cause**, not a confirmed crash. MetricKit delivery may be delayed or absent.

The release compiles and journal/privacy policies have automated checks. No physical Xiaomi crash reproduction or iPhone export test is claimed. Reproduce the reported scanner issue once on the new APK, then export the log if it persists.

## Platform references

- [Android ApplicationExitInfo](https://developer.android.com/reference/android/app/ApplicationExitInfo)
- [Apple MXDiagnosticPayload](https://developer.apple.com/documentation/metrickit/mxdiagnosticpayload)
- [Apple diagnostic subscriber](https://developer.apple.com/documentation/metrickit/mxmetricmanagersubscriber/didreceive(_:)-9yd4u)
