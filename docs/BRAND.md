# NodeLift identity and control room

Original identity created for NodeLift on 31 October 2026. The visual direction is a precise spatial-computing instrument: graphite, icy aqua, readable operational data, and restrained orbit geometry. The science-fiction reference is a mood, not a copy of film artwork or marks.

## Assets

- `assets/brand/nodelift-emblem.png`: original image generated with OpenAI image generation, transparent background, 1280 × 1280 pixels. Interconnected rising N with an orbital path. Use for larger presentation and repository artwork.
- `assets/brand/nodelift-mark.svg`: independently drawn simple geometric small-size mark, with current-color-independent aqua/white strokes. Use for the app/header favicon at small sizes.
- NodeLift wordmark: plain text, with a single aqua slash. Keep text live in the interface for clarity and accessibility.

Do not treat this as a trademark availability clearance. No third-party stock imagery, film asset, external image service, font service or CDN is used.

## Palette and type

| Role | Value |
|---|---|
| Canvas | `#091216` |
| Panel | `#101D22` |
| Primary text | `#EDF8F9` |
| Secondary text | `#9BB1B8` |
| Operational aqua | `#A0FFF1` |
| Secondary cyan | `#54D9D4` |
| Attention | `#FFD28A` |
| Error | `#FFB5AC` |

Local system sans-serif is paired with system monospace for measurements and labels, so the interface works without network font downloads. Visible focus, labeled controls, reduced-motion preference, and small-screen layouts are included.

## Product design rules

The network diagram reflects enrolled nodes and their observed availability. It does not imply that the displayed RAM is allocated or pooled. Unavailable engine controls remain disabled. There are no fabricated token rates, memory totals, benchmark curves, cloud activity or speedup badges.

The control room includes node association/revocation, grouped RTT results, payload-specific transfer goodput, filtering and JSON export. Engine controls support local model selection, context, CPU threads, GPU layers, host/local-draft/remote-draft comparisons, prompt, output limit, proposal block size, cancellation and real run results.

The web interface is responsive; this does not itself constitute the native Android/iOS interface. The native companion lifecycle, resource controls and model management are developed separately.

## Backend contract

The existing `/admin/status`, `/admin/invite`, `/admin/job` and `/admin/revoke` routes keep bearer authentication. Browser session tokens are retained per tab; ordinary section hashes are never interpreted as credentials. No credentials are included in the JSON export.

The engine UI consumes `/admin/engine/status` and posts to `/admin/engine/configure`, `/admin/engine/run`, `/admin/engine/stop`. If engine routes are absent, qualification functionality stays available and the page explains the limitation. Model choices come from the server catalog, not hardcoded model names.

Serve both brand files from `/brand/` on the local dashboard server. No external content policy changes are required.

## Verification record

Initial UI verification on the live local server:

- JavaScript syntax check passed.
- Browser authenticated and unauthenticated states observed.
- Actual enrolled Xiaomi and four actual measurement jobs rendered.
- Internal section navigation retained authentication.
- Actual invitation generation/close and CPU-only/all-results filtering verified in the browser.
- Engine endpoints were not yet enabled during the initial UI check; engine UI showed the unavailable state rather than synthetic results.
- Desktop screenshot captured at `artifacts/ui/control-room-desktop.png`; the initial screenshot predates activation of the brand asset routes, so it is not the final branded screenshot.

Engine configuration/run/cancellation verification and small-screen visual QA remain to be completed with the integrated engine. The browser's DOM-evaluation operation timed out and its exposed tab capabilities did not provide viewport resizing; no mobile screenshot is claimed. A generated emblem is not evidence of a measured performance improvement.

## Evaluation refinements

The first external design evaluation used Gemini 4 Argon with reasoning Alta and real desktop/tablet/mobile screenshots captured by the evaluator. It passed the visual direction with refinements. The implementation then corrected unapplied configuration ambiguity and the missing-session filter exception, grouped RTT values with their units and percentile labels, retained mobile readiness badges, added persistent navigation, separated revocation styling, and improved operational typography.

Nonmutating browser checks verified that selecting a different target and entering a prompt leaves Start disabled until applying or reverting. Revert restored the actual applied model and eligibility without changing backend configuration. The missing-session measurement filter is disabled and its renderer also accepts a null snapshot.

A local API access panel fetches connection details only after an explicit click. The key is held in transient memory, absent from exports, and not inserted into the DOM unless the user deliberately reveals it. Revealed text hides after 30 seconds; closing the panel, switching tabs or two minutes after opening clears the access data. Copy is an explicit action. No API key was revealed, copied, logged or captured during the initial panel test; the then-running server did not yet expose the new route. Reassessment and post-restart integration verification are tracked separately by the root agent.
