# Lessons from Locally Uncensored

Reviewed 1 November 2026 at commit [`5c9c4441c9cf`](https://github.com/PurpleDoubleD/locally-uncensored/commit/5c9c4441c9cfd7240ee05ae4bb597077e8d89ff8). Credit: [PurpleDoubleD and contributors](https://github.com/PurpleDoubleD/locally-uncensored). This is a focused source inspection, not an independent audit or a run of the application.

## Useful work and NodeLift decisions

| Inspected source | Useful lesson | NodeLift decision |
| --- | --- | --- |
| [crash_report.rs](https://github.com/PurpleDoubleD/locally-uncensored/blob/5c9c4441c9cfd7240ee05ae4bb597077e8d89ff8/src-tauri/src/crash_report.rs) | Persist a bounded final record, preserve the prior crash handler, label the version that wrote it and tolerate write failure | Native-platform implementation in NodeLift 0.2.6 records stable events and reporter build. Android preserves the default uncaught handler. No Rust code copied. |
| [phone_log.rs](https://github.com/PurpleDoubleD/locally-uncensored/blob/5c9c4441c9cfd7240ee05ae4bb597077e8d89ff8/src-tauri/src/phone_log.rs) | A phone needs a shareable local diagnostic surface; operational identifiers should remain intelligible | NodeLift adds explicit JSON export from About. It omits arbitrary message content and paths instead of exporting generic tracing fields. |
| [phone_version.rs](https://github.com/PurpleDoubleD/locally-uncensored/blob/5c9c4441c9cfd7240ee05ae4bb597077e8d89ff8/src-tauri/src/phone_version.rs) | Mobile and desktop build identities can differ; report the installed platform's identity | NodeLift reads package/bundle version and build, and keeps host preview version separate. |
| [tauri.conf.json](https://github.com/PurpleDoubleD/locally-uncensored/blob/5c9c4441c9cfd7240ee05ae4bb597077e8d89ff8/src-tauri/tauri.conf.json) and [security policy](https://github.com/PurpleDoubleD/locally-uncensored/blob/5c9c4441c9cfd7240ee05ae4bb597077e8d89ff8/SECURITY.md) | A signed updater channel is different from a signed first-install package | NodeLift's new check only discovers metadata over HTTPS. It does not claim signed update installation. Native package verification and platform distribution remain separate. |
| [vram_plan.rs](https://github.com/PurpleDoubleD/locally-uncensored/blob/5c9c4441c9cfd7240ee05ae4bb597077e8d89ff8/src-tauri/src/commands/vram_plan.rs) | Derive memory from model tensors, layer-specific KV/state, context, slots and backend behavior; check estimates against the pinned runtime | Adopt this as a future planner requirement. Do not estimate useful capacity by adding device RAM or using one KV constant for every model. No planner code imported and no new memory-budget qualification claimed. |

The inspected memory planner distinguishes ordinary attention, sliding windows, recurrent state, shared KV, quantized cache types and workspace buffers. Its assumptions track its own pinned llama.cpp and server configuration. NodeLift must calibrate its own native backend and context/slot choices before using equivalent estimates for admission or sharding.

The project is an application studio with local/remote capabilities. Remote phone access alone is not evidence that a phone donates memory or executes target-model shards. This inspection found useful product and reliability work; it does not establish NodeLift-compatible distributed compute, benchmark superiority or compatibility with every backend.

## Reuse and acknowledgement

The repository identifies its code as [AGPL-3.0](https://github.com/PurpleDoubleD/locally-uncensored/blob/5c9c4441c9cfd7240ee05ae4bb597077e8d89ff8/LICENSE). NodeLift has not copied, translated or linked that implementation into its MIT code. Any future code incorporation needs an explicit license-compatible design and preservation of its notices. The current changes are independently written Kotlin/Swift implementations using native Android/iOS APIs and general engineering lessons.

Thank you to PurpleDoubleD and contributors for making their implementation and limitations inspectable. See the [project acknowledgement register](../../docs/ACKNOWLEDGEMENTS.md).

## Additional source findings

- [Live memory-plan checks](https://github.com/PurpleDoubleD/locally-uncensored/blob/5c9c4441c9cfd7240ee05ae4bb597077e8d89ff8/src-tauri/src/commands/vram_plan_live.rs) compare three different quantities: the planner prediction, runtime-reported allocations and observed host/GPU memory. These tests are ignored by default and require models and the engine binary; their presence is not evidence that NodeLift passed them. Adopt the same separation in a future admission planner, with NodeLift's own backend revision and contexts.
- [Cancellation registry](https://github.com/PurpleDoubleD/locally-uncensored/blob/5c9c4441c9cfd7240ee05ae4bb597077e8d89ff8/src-tauri/src/cancel_registry.rs) documents the race where cancellation arrives before work is registered. A short-lived bounded cancellation marker prevents the later registration from starting cancelled work. NodeLift's future distributed task leases should test cancel-before-dispatch, late results, identity/generation changes and bounded cleanup. No registry code was imported.
- The inspected crash logger caps retained history, but its final append can exceed that cap for an unusually large panic message. Its UTF-8 tail slicing also deserves care. NodeLift deliberately accepts bounded, allowlisted symbols/events instead of arbitrary panic payloads. This is a source observation, not a demonstrated upstream exploit or a complete audit.

## Priority for NodeLift

| Priority | Work | Current status | Required evidence |
| --- | --- | --- | --- |
| P0 | Reach the correct local endpoint after a hotspot address change | Implemented in 0.2.7 host source, with fresh QR/TLS identity on a new address | Automated bind/identity/history tests; physical reconnection still needs confirmation |
| P0 | Make phone failures inspectable without a cable | Bounded export implemented in 0.2.6; route categories and actionable failure guidance added in 0.2.7 | A real exported Android log identified successful camera decoding followed by network timeouts; this does not prove every crash is captured |
| P1 | Model-aware memory admission | Design requirement, not implemented by this artwork/connectivity release | Predicted vs runtime vs observed memory on each pinned backend, context and cache configuration |
| P1 | End-to-end cancellation accounting | Existing runtime cancellation is not a qualified distributed lease protocol | Cancel-before-registration, deadline/fallback, stale-result and discarded-work tests |

These are engineering lessons from credited source inspection. They do not establish that either application adds phone RAM to a target model, or that NodeLift outperforms Locally Uncensored.
