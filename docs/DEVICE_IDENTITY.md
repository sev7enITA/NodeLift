# Device identity and repeat pairing

NodeLift 0.2.8 uses an installation identity for Android and iOS. It does not collect IMEI, serial numbers, Wi-Fi MAC addresses or a hardware fingerprint. Model names and memory sizes are descriptive telemetry, never identity evidence.

## Enrollment behavior

The companion creates a random 256-bit secret before its first pairing request. Android stores it encrypted under an Android Keystore key, with application backup disabled. iOS stores it in Keychain with WhenUnlockedThisDeviceOnly accessibility. Forgetting a computer clears its session credential, not the installation secret.

The pinned TLS host exposes a persistent random pairing scope in `/health`. The companion derives a host-specific key with HMAC-SHA256 over `nodelift-device-v1\n` followed by that scope. Only this derived key is sent during a valid QR enrollment; the root secret never leaves the companion. The host stores only its SHA-256 digest, with a unique database index. The stable host scope is independent of IP address and TLS certificate rotation.

A fresh, single-use invitation remains mandatory. Matching installation identity reuses the existing node ID, refreshes telemetry, rotates the access credential and cancels pending diagnostic jobs from the superseded session. Expired invitations cannot reactivate revoked nodes. A new owner-issued invitation can explicitly enroll them again. Different installations of the same phone model remain distinct. Pairing transactions serialize concurrent requests; the last completed enrollment owns the current credential.

## Upgrading existing installations

The previous saved node ID is accompanied by an HMAC proof bound to the new invitation. Its key is the SHA-256 digest of the saved access token, and its message is `nodelift-repair-v1\n` followed by the invitation. The host verifies this against its stored credential digest before adopting a legacy enrollment. The old raw credential is never disclosed to a newly scanned host. Unknown IDs from another host do not cause a merge. Invalid proofs for a known legacy ID are rejected without consuming the invitation.

Once established, the installation key supports retry with another QR after a lost pairing response, even if credential rotation already occurred. Update the desktop host before installing this companion version: a host without a valid pairing scope is rejected with upgrade guidance.

## Older duplicates and limitations

Legacy records have no installation identity. They must not be automatically merged by name, model, RAM or IP address. The owner can confirm a specific historical duplicate for local maintenance. `State.merge_nodes` preserves the retired record, revokes its credential, retains an audit entry and moves completed jobs to the retained node while recording `original_node`. A private SQLite backup should be made first. Active jobs prevent this operation. The retired source must have no established identity; the retained active enrollment may already have one. Established identities are never retired by this maintenance path. Assessment associations are transferred alongside their completed jobs.

Deleting app data, losing secure storage or reinstalling can create a new installation. Physical-device identity after such a reset is not guaranteed. This is credential continuity, not hardware attestation or proof against a compromised companion. HarmonyOS/NEXT remains a source candidate without this persistent identity flow; do not assume parity with Android/iOS.

## Validation

Ten host regression tests cover stable enrollment, distinct same-model phones, legacy adoption, forged/replayed proofs, credential rotation, interrupted responses, host restart, concurrent enrollment, revocation and history-preserving consolidation. Kotlin and Swift HMAC vectors match the host. The real Swift TLS client pairs twice against an isolated host and leaves one enrollment; its old session credential is rejected. These client protocol tests run on macOS and do not replace physical phone qualification.
