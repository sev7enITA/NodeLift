# Network mobility and stable pairing

Status: host listener recovery implemented in source; transparent companion roaming is a proposed protocol change, not shipped functionality.

## Current correction

The host now checks the selected private IPv4 route every two seconds independently of Add device. It binds the new interface, closes the previous listener and invalidates invitations referring to a departed endpoint. Loss of a usable route or bind failure closes the stale listener and triggers bounded periodic retries. Enrollment records and node bearer credentials remain intact. Returning to the same address reuses its existing TLS identity. An explicitly configured address remains fixed; it is never silently replaced by a different interface.

The dashboard reports network loss and address transitions in English, Simplified Chinese and Italian. This does not turn a historical engine-ready flag into an online node. The loopback dashboard stays independent of the LAN listener.

## Existing limitation

Protocol 1 stores an IP URL and pins the exact certificate issued for that IP. Its Android and iOS clients have no authenticated endpoint rediscovery. A move to a different address therefore still requires a fresh invitation with current companion builds. Rebinding the server is not an end-to-end roaming implementation. The optional existing Bonjour advertisement alone does not solve identity, endpoint validation or credential migration.

## Required protocol contract

1. Separate stable, installation-scoped host identity from transient addresses. No IMEI, MAC address or IP should be used as identity. Keep the node enrollment identity and token across endpoint changes.
2. Discover candidates locally using DNS-SD/Bonjour. Android uses NsdManager; iOS uses NWBrowser. Discovery results and TXT records are untrusted hints, never proof of identity. Permissions, cancellation, duplicate names and multiple interfaces must be handled explicitly.
3. Authenticate a candidate against the previously paired host identity before sending bearer credentials, prompts or model data. Define a versioned certificate/authority scheme that preserves hostname validation and supports authenticated certificate renewal. Do not accept a new certificate merely because an announcement contains the expected identifier.
4. Store the new endpoint atomically only after authenticated validation. Maintain a connection generation so late callbacks or responses from an old path cannot revive the old session. Cancel stale inference leases and lookahead; revalidate model and tokenizer identities before scheduling new work.
5. Show distinct states: finding the paired computer, authenticating, connected, waiting for network, local discovery blocked, and identity changed. Only fresh authenticated traffic establishes connected status. Draft files remain on disk throughout the transition.
6. Retry with capped backoff and jitter, bounded candidate count and energy-aware foreground/background behavior. Stop immediately on user pause. Never scan arbitrary subnets or fall back to an unauthenticated/public cloud route.
7. If multicast is blocked, allow a user-supplied local endpoint that must pass the same existing-identity check. A new QR is a recovery/migration option, not the normal response to DHCP. If devices are on separate non-routable networks, show that condition rather than claiming local connectivity.

A one-time, explicit migration from legacy IP certificates may be necessary. Upgrading must not silently trust a different key, create duplicate nodes or broaden a revoked enrollment.

## Qualification before claiming seamless roaming

| Scenario | Required observation |
|---|---|
| DHCP change on the same LAN | Same host/node identities, authenticated new endpoint, no repeated enrollment |
| Laptop moves from Wi-Fi A to B | Offline while unreachable; rediscovery only once both devices share a reachable network |
| Return to the earlier network | No duplicated node or lost model configuration |
| Wi-Fi without Internet and cellular default | Correct local interface, without global process routing changes |
| VPN, Ethernet and Wi-Fi together | Explicit eligible path selection; no accidental VPN/public endpoint |
| Spoofed discovery, same name, changed key | Rejected before credentials or prompt transmission |
| Network changes during inference | Expired work discarded, bounded fallback, no duplicate output commit |
| Pause/background/permission denial | Discovery stops or follows platform lifecycle; honest UI state |
| Revocation and certificate renewal | Revoked tokens remain revoked; only authenticated identity continuity accepted |
| Hotspot blocks multicast or peer traffic | Actionable fallback or unavailable state, no claimed successful recovery |

The source correction has local socket/TLS regression tests with simulated route transitions. It has not physically switched the user's Wi-Fi, validated Android/iOS roaming or established any LLM performance result.

## Primary platform references

- [Android network service discovery](https://developer.android.com/develop/connectivity/wifi/use-nsd)
- [Android NsdManager and network lifecycle](https://developer.android.com/reference/android/net/nsd/NsdManager)
- [Apple NWBrowser](https://developer.apple.com/documentation/network/nwbrowser)
- [Apple local network privacy](https://developer.apple.com/documentation/technotes/tn3179-understanding-local-network-privacy)
