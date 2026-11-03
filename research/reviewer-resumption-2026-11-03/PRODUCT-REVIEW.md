# Product assessment resumption, 3 November 2026

## Scope and evidence

Gemini 4 Argon High was explicitly selected in the authenticated browser. It completed the [public source packet](gemini-product-prompt.txt), an [initial response](gemini-product-review.txt), and a [correction follow-up](gemini-product-followup.txt) after receiving [independently checked facts](gemini-product-followup-prompt.txt). Source revision: `6ceedfd58c338294b84e39fab0fb45530decd770`.

The review covers 15 selected English, Simplified Chinese and Italian catalog entries; complete `graph.js`; selected CSS; the About HTML and Swift views; Android About/update sources; iOS `UpdateMonitor`; and the documented QR protocol. It does not review the entire catalog, HarmonyOS implementation, every dependency or live UI. QR scope is a protocol description, not pairing source or physical camera execution. No credentials, private logs or device telemetry were supplied.

The first CSS extraction accidentally removed standalone media-query wrapper lines. This was our packet-preparation error. The original source contained the wrappers. The reviewer retracted the resulting high-severity layout finding after receiving the complete relevant blocks. Future source packets must preserve complete syntactic units, including enclosing media rules. Neither that initial claim nor its retraction is evidence of a CSS fix.

## Checked findings and dispositions

| Finding | Disposition |
| --- | --- |
| F1: missing Italian draft qualifier and inconsistent Chinese companion term | Corrected the selected entry to retain the draft role and distinguish a real run from a test. Chinese now refers to the companion application performing draft generation. All generated platform catalogs were refreshed. This is a 15-entry review, not full linguistic certification. |
| F2: About translation key supposedly missing | Rejected and retracted. Both wording variants already exist in all three complete catalogs. No lookup defect was established. |
| F3: desktop layout supposedly collapses unconditionally | Rejected and retracted after correcting the incomplete CSS packet. Original media wrappers remain unchanged. |
| F4: zero accepted proposals only show a percentage | Reproduced in synthetic DOM. The participating device now explicitly shows `No accepted mobile proposals` when measured acceptance is zero. The percentage-based graph remains a token attribution display, not compute utilization. |
| F5: epoch-zero telemetry appears historical rather than unknown | Reproduced in synthetic DOM and fixed. A zero timestamp is unknown in both the freshness label and the dated inspector. |
| F6: unrelated jobs recreate the selected inspector | Reproduced in synthetic DOM and fixed by deriving the signature from the selected node's displayed measurements. Unrelated jobs preserve existing inspector nodes. Suggested ARIA changes are not applied: the exclusive selection contract and actual screen-reader behavior need separate qualification. |
| F7: mixed decimal and binary throughput units | Both old labels were mathematically valid, but their mixture complicated comparison. The graph now consistently uses MiB/s. A one-MiB/one-second fixture yields exactly 1 MiB/s. Historical raw measurements are unchanged. |
| F8: bearer invitation and consume/Close race | Documented trust boundary, not a newly found implementation flaw. Possession of a live invitation authorizes enrollment; Close revokes unused invitations, while Revoke pairing handles completed enrollment. Adding host approval would change protocol and UX. No interception or unauthorized enrollment was demonstrated. |
| F9: fractional QR scaling may impair scanning | Physical scan reliability remains unmeasured in this review. The full existing CSS already requests `image-rendering:pixelated`; the reviewer had not received that rule. Earlier isolated ZXing decoding remains separate evidence. No blanket blur or physical improvement claim is accepted. |
| F10: clock skew and startup IP binding | Known protocol limitations. A new state directory does not delete the old database. An arbitrary five-minute grace period or identity migration is not applied without source-specific trust/expiry tests. |
| F11: backward clock adjustment bypasses failed-check backoff | Reproduced against the original Kotlin and Swift policy. Future timestamps are now treated as unknown individually, preserving a recent failed attempt and its one-hour retry interval. Initial correction can still trigger a check; weekly scheduling and explicit manual checks are retained. |
| F12: remove monotonic-build/downgrade checks | Rejected and retracted. Both monitors retain verified details even for the current release; weakening validation could offer a downgrade. Globally monotonic build numbers are intentional. Documentation now explains this and that an older manifest invalidates details rather than establishing an update. |
| F13: stale-details warning initially visible | Source confirms the default-visible warning precedes the scheduled validity refresh. It now starts hidden. Kotlin compilation passes. A visible flash or TalkBack announcement was not reproduced on a device. |
| F14: About/update cleanup | Documented the second HTTPS changelog request and its validation dependency. Incident retention after export is intentional and was retracted as a defect. Android application startup initializes `UpdateMonitor` before activity resume, so the proposed missing-start failure was not established. Redundant translation and heading semantics remain optional accessibility cleanup, not validated runtime failures. |

## Verification

- [Four synthetic DOM checks](graph-after.json) pass; [the corresponding before-fix cases](graph-before.json) failed. These use jsdom 26.1.0, not a browser layout engine or screen reader.
- Android: the new backward-clock regression failed against the original policy; the corrected source passes all 22 JVM tests, including release metadata, QR and diagnostic policies. Kotlin compilation of the changed About source passed. The initial Java 25 toolchain failure was resolved using installed Java 21; it was not an application test failure.
- Swift: two of four focused clock cases failed before the correction; all four pass afterward. The existing support-policy checks also pass, including release ordering and journal privacy, rotation, restart, expiry and clearing. [Checks receipt](product-checks.json).
- Existing graph, control-state, localization runtime and catalog freshness checks pass. These do not establish physical accessibility, phone performance or update installation.
- The running host serves the updated graph asset byte for byte. No host inference was requested by these checks.

Reproduce the DOM regressions from the repository root:

```sh
npm install --prefix /tmp/nodelift-review-dom --no-audit --no-fund jsdom@26.1.0
NODE_PATH=/tmp/nodelift-review-dom/node_modules node research/reviewer-resumption-2026-11-03/check_graph_dom.cjs "$PWD" /tmp/nodelift-graph-checks.json
node scripts/check-device-graph.cjs
```

The mobile changes are source updates with policy and Kotlin compilation evidence. This assessment does not create or publish new APK/IPA packages, qualify the weekly timer on a physical phone, or change the published companion release. The native framework packaging build is documented separately in [the core/build assessment](REVIEW.md). GLM's separate [performance assessment](PERFORMANCE-REVIEW.md) is now complete and adjudicated. Physical validation remains separate.
