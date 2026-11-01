# Dashboard session recovery

Host source update, 2026-11-01. Companion release 0.2.7 remains unchanged.

A new browser tab has no sessionStorage credential, and a host restart replaces the administrator token. The previous dashboard only directed the user to a local script. The dashboard now offers **Restore local session**, with a busy state, duplicate-click guard, timeout and retry feedback in English, Simplified Chinese and Italian. Successful recovery reloads the page with the current key; a fragment fallback supports blocked session storage. Phone enrollment is preserved.

The recovery endpoint is restricted to the exact loopback origin with explicit Origin, Fetch Metadata and request-header checks. See [the local trust boundary](../SECURITY.md#local-dashboard-recovery).

Validation: four HTTP regression tests cover missing/stale keys, server key rotation, rejected cross-site/missing metadata/rebinding requests, method/body restrictions and unchanged bearer requirements for protected endpoints. UI checks cover retry, duplicate suppression and unavailable session storage. A live in-app browser test recovered a real stale session after a host restart, showed Local session active and retained two paired-device records. This does not qualify mobile pairing or inference.
