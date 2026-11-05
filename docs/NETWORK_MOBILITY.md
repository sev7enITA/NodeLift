# Network mobility and stable pairing

Status: implemented in experimental companion 0.2.14 (build 17) and the corresponding host source. Desktop TLS and Bonjour checks passed. Physical Android/iPhone network roaming is not yet qualified.

## How it works

The host checks its selected private IPv4 route every two seconds independently of Add device. It binds the current interface, closes the old listener and invalidates invitations for the departed endpoint. Loss of a usable route or bind failure closes the stale listener and triggers bounded retries. Enrollment records remain intact. An explicitly configured address remains fixed.

Protocol 2 separates the host's installation identity from its address. The host keeps an exact pinned certificate with a random logical DNS name under its private state directory. DHCP does not generate a new certificate. DNS-SD advertises `_nodelift._tcp` with the current private IPv4 endpoint and public fingerprint. No bearer credential, prompt or model data is advertised.

Android uses NsdManager and a scoped multicast lock. iOS uses NWBrowser and declares Bonjour service access. On a connection failure, companions look for the previously paired host, validate candidate addresses, authenticate the original certificate and its logical DNS name, then verify the saved token and node identity through `/v1/session`. Only then is the endpoint saved. Discovery announcements cannot replace trust material. Wrong keys and names are rejected before credentials are sent.

Discovery windows are bounded to eight seconds; candidate results are capped. Retry delay is capped at 60 seconds plus jitter. Pause cancels active requests and discovery. Connection generations prevent stale work from restoring a stopped session. Reconnection clears the in-memory draft state and lookahead; downloaded model files and settings stay on disk. These changes do not implement transparent migration of in-flight inference or establish output equivalence under physical roaming.

## Upgrade and recovery

1. Update the host and companion to this protocol-2 release.
2. Existing protocol-1 pairings need one new QR because the legacy certificate was tied to an IP. Enrollment scope and credential proofs preserve the existing node where available.
3. Subsequent address changes use rediscovery when both devices share a reachable local network. The user does not enter a fixed IP.
4. If local discovery or peer traffic is blocked, the app reports that the host was not found. A fresh QR at the reachable current address remains the recovery option. Manual endpoint recovery with the saved identity is not implemented.

The host defaults to protocol 2; `--legacy-pairing` temporarily retains protocol 1 for old companions. Protocol 1 has no automatic rediscovery.

## Limits

- Current endpoints are private IPv4 only. IPv6-only networks are not supported.
- A shared Wi-Fi name does not guarantee peer reachability. Client isolation, blocked multicast, VPN routing and hotspot restrictions can prevent recovery.
- The host uses native `dns-sd` on macOS or `avahi-publish-service` on Linux. Other hosts need a compatible publisher installed; discovery is reported unavailable if absent. No automatic installation or Windows qualification is claimed.
- iOS runs delegated work in the foreground. Discovery does not bypass OS suspension, local-network permissions or Android lifecycle limits.
- The pinned certificate lasts 365 days. Authenticated renewal is not implemented. Expired or incomplete identity is not silently replaced; explicit recovery and pairing are required. Back up the private host state securely.
- No arbitrary subnet sweep, public relay, shared RAM or inference speedup is introduced.

## Validation

175 host tests, 28 Android JVM tests, Android lint (zero errors, 18 warnings), unsigned iOS ARM64 compilation, pairing encoding and localization checks passed. A compiled client using the actual Swift protocol code authenticated two TLS endpoints with the same saved identity/node and rejected a wrong certificate and logical hostname. Actual NWBrowser discovery found an advertisement on the Mac's private network interface. These are desktop tests, not an iPhone roaming test.

The Android package preserves the existing laboratory debug signer. Both mobile packages reuse the exact native engine binaries from published 0.2.13. Later source-only native corrections are not included in these binaries. Hashes and validation scope are in [the build evidence](../research/network-mobility-2026-11-05/validation.json).

Physical checks still required: DHCP change, Wi-Fi A to B and return, Internet-free Wi-Fi with cellular default, simultaneous Ethernet/VPN paths, pause during recovery, denied permissions, revocation, spoofed discovery, blocked hotspot multicast and a network change during inference. Record fresh authenticated contact and stable node identity before treating a device as available for a benchmark.

## Primary platform references

- [Android network service discovery](https://developer.android.com/develop/connectivity/wifi/use-nsd)
- [Android NsdManager](https://developer.android.com/reference/android/net/nsd/NsdManager)
- [Apple NWBrowser](https://developer.apple.com/documentation/network/nwbrowser)
- [Apple local network privacy](https://developer.apple.com/documentation/technotes/tn3179-understanding-local-network-privacy)
