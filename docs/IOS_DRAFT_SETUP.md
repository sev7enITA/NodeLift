# iOS draft setup

## Implementation and development build

The iOS 0.2.8 app supported manual GGUF import but did not have Android's direct Mac download action. The published 0.2.11 iOS source also lacked it. A translation string was not evidence that the iOS action existed.

Private development build **0.2.12 (14)** adds **Download draft from Mac and enable** to Settings > Draft model, with EN, Simplified Chinese and Italian labels. It was signed with the owner's existing development identity and installed over 0.2.8 on a physical iPhone 15 Pro Max on 2026-11-02. The bundle ID and signing team remain unchanged. This is a local development installation, not an App Store, TestFlight or public binary release. Public download manifests remain at 0.2.11 (13).

1. Pair with the Mac and select its draft model in the desktop LLM engine configuration.
2. Open **Set up draft** and select **Download draft from Mac and enable**. This pauses the active work session.
3. Keep the app foregrounded while it downloads, verifies and imports the file. The maximum size is 1 GiB.
4. After **Draft verified · proposals enabled · resume the session**, return Home and select **Resume session**.
5. Wait for **Draft ready** and a fresh host heartbeat before benchmarking. Imported, enabled and loaded are distinct states. Battery, thermal state and process memory headroom can prevent loading.

If the owner explicitly requests a development transfer, Xcode's `devicectl` can copy the selected GGUF to the app's `Documents/NodeLift-draft.gguf`. The **Use transferred draft and enable** action appears when that file exists. It fetches the paired Mac's current draft hash, verifies the imported file against it and removes the staging copy only after success. No hash or consent is injected into preferences by the Mac. Pairing secrets remain in Keychain.

## Transfer behavior

The transfer uses the saved bearer credential and pinned Mac certificate. It requests only the fixed local model endpoint, rejects redirects, requires matching Content-Length, bounds received bytes and disk requirements, checks SHA-256 and GGUF magic before replacing the active draft, and removes partial files on errors or cancellation. The request idle timeout is 30 seconds and resource timeout is 15 minutes. Backgrounding cancels an active transfer. Setup stays locked until cleanup finishes; cancelled transfers do not automatically restart. The previous valid draft stays intact when validation fails.

The native library is unchanged. Download transport and preparation do not establish faster inference, effective Metal offload or shared RAM. The transferred file was approximately 491 MB, not new pooled host memory.

## Validation and reproduction

The iOS ARM64 Release build compiled. The installed version/build was read back from the physical phone. Swift protocol, support/update-policy and localization checks passed. Actual transfer code was exercised against a synthetic pinned TLS server on macOS for success, hash mismatch, incorrect length, truncation, redirect, unauthorized access, cancellation, wrong certificate and temporary-file cleanup. These are network integration checks of the Swift source, not physical iPhone wireless download throughput measurements.

```sh
swiftc -O apps/ios/NodeLift/Protocol.swift apps/ios/NodeLift/DraftTransfer.swift scripts/swift-draft-transfer-check.swift -o /tmp/nodelift-draft-check
python3 scripts/run-swift-draft-transfer-check.py --binary /tmp/nodelift-draft-check
```

The private development app was built from the current iOS source with the existing pinned iOS native framework and Xcode overrides `MARKETING_VERSION=0.2.12 CURRENT_PROJECT_VERSION=14`. Repository release defaults remain 0.2.11 (13) until a public release is prepared. Private provisioning profiles and signed development packages are not published.

The physical phone has received and imported the staging file. Host-observed native readiness and the planned [iPhone performance comparison](../research/iphone-tradeoffs-2026-11-02/PLAN.md) remain separate acceptance checks.

## Build 15 follow-up

Private development build **0.2.12 (15)** was installed after the physical build-14 benchmark. It handles authenticated HTTP 400 rejections for expired/replayed leases or superseded draft identity as discarded job output, rather than escalating them into connection retries. Rejected tokens are never accepted or resubmitted. The local journal now records `draftDiscarded`. Other request failures retain their error handling.

The transfer/protocol integration suites and iOS ARM64 build passed again. Physical post-fix readiness and inference remain separate from installation. The original benchmark, including the interrupted fixed-128 cell, is retained in the [iPhone report](../research/iphone-tradeoffs-2026-11-02/REPORT.md). Public binary downloads remain 0.2.11 (13).
