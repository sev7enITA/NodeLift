# Lessons from Locally Uncensored

Reviewed 1 November 2026. Credit: [PurpleDoubleD and contributors](https://github.com/PurpleDoubleD/locally-uncensored). This is a focused source inspection, not an independent audit or a run of the application.

## Useful work and NodeLift decisions

| Inspected source | Useful lesson | NodeLift decision |
| --- | --- | --- |
| [crash_report.rs](https://github.com/PurpleDoubleD/locally-uncensored/blob/master/src-tauri/src/crash_report.rs) | Persist a bounded final record, preserve the prior crash handler, label the version that wrote it and tolerate write failure | Native-platform implementation in NodeLift 0.2.6 records stable events and reporter build. Android preserves the default uncaught handler. No Rust code copied. |
| [phone_log.rs](https://github.com/PurpleDoubleD/locally-uncensored/blob/master/src-tauri/src/phone_log.rs) | A phone needs a shareable local diagnostic surface; operational identifiers should remain intelligible | NodeLift adds explicit JSON export from About. It omits arbitrary message content and paths instead of exporting generic tracing fields. |
| [phone_version.rs](https://github.com/PurpleDoubleD/locally-uncensored/blob/master/src-tauri/src/phone_version.rs) | Mobile and desktop build identities can differ; report the installed platform's identity | NodeLift reads package/bundle version and build, and keeps host preview version separate. |
| [tauri.conf.json](https://github.com/PurpleDoubleD/locally-uncensored/blob/master/src-tauri/tauri.conf.json) and [security policy](https://github.com/PurpleDoubleD/locally-uncensored/blob/master/SECURITY.md) | A signed updater channel is different from a signed first-install package | NodeLift's new check only discovers metadata over HTTPS. It does not claim signed update installation. Native package verification and platform distribution remain separate. |
| [vram_plan.rs](https://github.com/PurpleDoubleD/locally-uncensored/blob/master/src-tauri/src/commands/vram_plan.rs) | Derive memory from model tensors, layer-specific KV/state, context, slots and backend behavior; check estimates against the pinned runtime | Adopt this as a future planner requirement. Do not estimate useful capacity by adding device RAM or using one KV constant for every model. No planner code imported and no new memory-budget qualification claimed. |

The inspected memory planner distinguishes ordinary attention, sliding windows, recurrent state, shared KV, quantized cache types and workspace buffers. Its assumptions track its own pinned llama.cpp and server configuration. NodeLift must calibrate its own native backend and context/slot choices before using equivalent estimates for admission or sharding.

The project is an application studio with local/remote capabilities. Remote phone access alone is not evidence that a phone donates memory or executes target-model shards. This inspection found useful product and reliability work; it does not establish NodeLift-compatible distributed compute, benchmark superiority or compatibility with every backend.

## Reuse and acknowledgement

The repository identifies its code as [AGPL-3.0](https://github.com/PurpleDoubleD/locally-uncensored/blob/master/LICENSE). NodeLift has not copied, translated or linked that implementation into its MIT code. Any future code incorporation needs an explicit license-compatible design and preservation of its notices. The current changes are independently written Kotlin/Swift implementations using native Android/iOS APIs and general engineering lessons.

Thank you to PurpleDoubleD and contributors for making their implementation and limitations inspectable. See the [project acknowledgement register](../../docs/ACKNOWLEDGEMENTS.md).
