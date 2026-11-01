# Security reporting

NodeLift is experimental. Its current prereleases are not a production security certification. Keep the dashboard/client gateway on loopback and pair only devices you trust: mobile drafting can disclose tokenized prompt context to the paired node.

Do not post working credentials, invitation links, private prompts, signing material or exploit details affecting users in a public issue. Use the contact options on [Fabrizio Degni’s website](https://www.fabriziodegni.com/) to arrange a private reporting channel. No response-time or bounty commitment is offered.

A useful report identifies the affected commit/release, platform, prerequisites, reproducible behavior and impact with synthetic/public data. The project distinguishes a reported concern, a reproduced defect, a patch and a verified fix.

For ordinary setup failures and sanitized bugs, use the repository issue forms. Dependency and model licenses are documented separately in THIRD_PARTY_NOTICES.md. Never attach model weights or the private NodeLift state directory.

## Local dashboard recovery

The dashboard is a trusted local application: a browser page served from its exact `http://127.0.0.1:<port>` origin may recover the current administrator session. Recovery requires a POST with explicit matching Origin, same-origin Fetch Metadata, a dedicated request header and an empty JSON object. The server also checks the Host header and loopback peer. Responses are not cached and no CORS access is enabled. Recovery does not rotate the server key, change phone enrollment or expose the route on the companion LAN listener. Other administrative endpoints still require their bearer credential.

This is not isolation between local OS users, browser extensions or processes able to access the Mac. A compromised same-origin dashboard script can act with dashboard privileges. Do not reverse-proxy the dashboard to a network interface or embed untrusted scripts.
