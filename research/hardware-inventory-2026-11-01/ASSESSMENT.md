# Hardware inventory and benchmark assessment

Reviewed on 2026-11-01 for NodeLift, a project by Fabrizio Degni. This is a source-level assessment of the two repositories requested by the author, compared with NodeLift source revision `acee71fa6ea55d11f08fc2ff3b0673c531699cc7` and current platform documentation. No upstream code or dependency was imported, no native build was started, and no physical-device benchmark was performed during this assessment. HarmonyOS/NEXT SDK installation and compilation remain deferred at the author's request because of limited disk space.

## Decision

Both projects offer useful hardware inventory ideas. Neither supplies a distributed inference engine or an LLM benchmark suite. Use inventory to identify a device and choose candidate backends; use measured, task-specific performance to decide whether to delegate work.

| Project and reviewed revision | Useful contribution | Adoption decision |
|---|---|---|
| [android-hrwinfo](https://github.com/nickayl/android-hrwinfo/tree/a23095fe6d0b15c130e06b23285d55c0eb0e99aa), `a23095f` | CPU/sysfs probes, memory, storage, battery, sensor and GLES identity interfaces | Reference for selective probes, not an unchanged dependency. Reimplement required probes with current public APIs and explicit unavailable states. |
| [DeviceHardware](https://github.com/Shakshi3104/DeviceHardware/tree/628aef9b48561b224d9cce18bb36874c549f9c8f), `628aef9` | Apple model identifier to commercial name/SoC mappings, runtime physical memory and Metal GPU name | Candidate for a small, versioned Apple catalog adapter after corrections and fixture tests. Keep catalog descriptions separate from observations. |

The reviewed licenses are [Apache-2.0](https://github.com/nickayl/android-hrwinfo/blob/a23095fe6d0b15c130e06b23285d55c0eb0e99aa/LICENSE) and [MIT](https://github.com/Shakshi3104/DeviceHardware/blob/628aef9b48561b224d9cce18bb36874c549f9c8f/LICENSE), respectively. If code or substantial mappings are later redistributed, retain applicable copyright/license notices, record the upstream revision and modifications, and handle any applicable NOTICE requirements. Listing a research reference does not mean its code is included in NodeLift.

## android-hrwinfo: useful probes, legacy assumptions

GitHub reported the last push as 2023-05-17 at review time. The [library build configuration](https://github.com/nickayl/android-hrwinfo/blob/a23095fe6d0b15c130e06b23285d55c0eb0e99aa/core-reference-impl/build.gradle) uses compile/target SDK 27 and support-appcompat 27.1.1. Its README's JitPack coordinate refers to `cyclonesword`, a different repository owner from the supplied `nickayl` URL; do not assume that artifact contains the reviewed source.

| Finding in reviewed source | Consequence for NodeLift |
|---|---|
| [CPUImpl, lines 348–381](https://github.com/nickayl/android-hrwinfo/blob/a23095fe6d0b15c130e06b23285d55c0eb0e99aa/core-reference-impl/src/main/java/org/javando/android/hrwinfo/core/impl/CPUImpl.java#L348-L381): the frequency monitor requests `System.gc()` every eight seconds | A request to collect garbage can perturb a measurement. Do not import this monitor into the benchmark loop. Measure telemetry overhead separately. |
| [CPUImpl, lines 389–427](https://github.com/nickayl/android-hrwinfo/blob/a23095fe6d0b15c130e06b23285d55c0eb0e99aa/core-reference-impl/src/main/java/org/javando/android/hrwinfo/core/impl/CPUImpl.java#L389-L427): assumes thermal zone zero is CPU temperature; core discovery has a hard stop at 24 | A thermal-zone number alone does not identify the sensor. Use OS thermal pressure for policy; expose a temperature only with identified source and units. Avoid fixed core-count limits. |
| [CPUImpl, lines 297–345](https://github.com/nickayl/android-hrwinfo/blob/a23095fe6d0b15c130e06b23285d55c0eb0e99aa/core-reference-impl/src/main/java/org/javando/android/hrwinfo/core/impl/CPUImpl.java#L297-L345): sysfs reads and frequency-based cluster inference | Treat sysfs access as optional and inferred clusters as estimates, with unknown results when inaccessible. Do not turn nominal frequencies into scheduling weights. |
| [DeviceImpl, lines 104–130](https://github.com/nickayl/android-hrwinfo/blob/a23095fe6d0b15c130e06b23285d55c0eb0e99aa/core-reference-impl/src/main/java/org/javando/android/hrwinfo/core/impl/DeviceImpl.java#L104-L130): memory in integer MiB; RAM fraction uses 0–1 while storage percentage uses 0–100 | Keep integer bytes in the protocol, convert only for display, and define each unit explicitly. NodeLift already collects system memory through ActivityManager. |
| [BatteryImpl, lines 229–248](https://github.com/nickayl/android-hrwinfo/blob/a23095fe6d0b15c130e06b23285d55c0eb0e99aa/core-reference-impl/src/main/java/org/javando/android/hrwinfo/core/impl/BatteryImpl.java#L229-L248): reflects the internal PowerProfile battery-capacity method and returns zero on failure | Do not rely on internal Android APIs. Unavailable capacity must be unknown, not zero. A capacity estimate is not measured inference energy. |
| [GPUImpl](https://github.com/nickayl/android-hrwinfo/blob/a23095fe6d0b15c130e06b23285d55c0eb0e99aa/core-reference-impl/src/main/java/org/javando/android/hrwinfo/core/impl/GPUImpl.java): creates an EGL context and pbuffer to read GLES strings; the inspected implementation has no corresponding EGL teardown or previous-context restoration | The renderer identity is useful, but the probe needs resource cleanup and isolation. A GLES name does not prove Vulkan support, available inference kernels, or NPU execution. |

Prefer the public [Build.SOC_MANUFACTURER and SOC_MODEL fields](https://developer.android.com/reference/android/os/Build#SOC_MODEL), available from API 31, alongside ABI, model and OS information. Older versions need an explicit fallback. Android's [non-SDK interface restrictions](https://developer.android.com/guide/app-compatibility/restrictions-non-sdk-interfaces) make internal reflection unsuitable as a dependable collector contract. This review does not establish that every sysfs path or internal call fails on every phone; those require device-specific checks.

## DeviceHardware: valuable Apple catalog, not live performance

GitHub reported the last push as 2026-10-13. The [manifest](https://github.com/Shakshi3104/DeviceHardware/blob/628aef9b48561b224d9cce18bb36874c549f9c8f/Package.swift) has no package dependencies and requires iOS 12/macOS 10.15; the README's iOS 8 statement is inconsistent with the manifest.

The [iOS lookup table](https://github.com/Shakshi3104/DeviceHardware/blob/628aef9b48561b224d9cce18bb36874c549f9c8f/Sources/DeviceHardware/UIDeviceHardware.swift) maps `iPhone16,2` to iPhone 15 Pro Max and A17 Pro, making it useful for the device graph. It also returns catalog CPU-frequency and Neural Engine descriptions. These are table entries, not samples of current clocks or evidence that NodeLift can execute on the Neural Engine. Unknown future identifiers must remain usable through their raw identifiers.

The [shared helper](https://github.com/Shakshi3104/DeviceHardware/blob/628aef9b48561b224d9cce18bb36874c549f9c8f/Sources/DeviceHardware/DeviceHardware.swift) reads physical RAM through ProcessInfo and the GPU name through Metal. Those calls complement model names; they do not measure per-process memory headroom or tokens per second.

Two issues need attention before adoption:

1. **Intel/Apple Silicon branching:** [MacDeviceHardware, lines 675–730](https://github.com/Shakshi3104/DeviceHardware/blob/628aef9b48561b224d9cce18bb36874c549f9c8f/Sources/DeviceHardware/MacDeviceHardware.swift#L675-L730) checks whether an optional Boolean is non-nil, rather than whether it is true. A successful false result can enter the Apple Silicon branch and miss the Intel branch. This is a source-level logic finding, not a reproduced physical Intel-Mac failure. A future adapter must distinguish true, false and unavailable explicitly.
2. **Validation scope:** the [tests](https://github.com/Shakshi3104/DeviceHardware/blob/628aef9b48561b224d9cce18bb36874c549f9c8f/Tests/DeviceHardwareTests/DeviceHardwareTests.swift) expect a particular Mac mini/M2 Pro/32 GB configuration. The performance test repeats a model-name lookup 10,000 times. It measures library-call overhead, not CPU/GPU inference performance. Replace host-specific expectations with catalog fixtures, unknown/simulator cases and independent runtime checks.

For GPU qualification, query supported [Metal families](https://developer.apple.com/documentation/metal/mtldevice/supportsfamily(_:)), then exercise the actual selected inference backend. Where available, [recommendedMaxWorkingSetSize](https://developer.apple.com/documentation/metal/mtldevice/recommendedmaxworkingsetsize) is a performance advisory for GPU resources, not extra RAM to add to system memory. Availability guards and physical-device qualification are still required.

## NodeLift gaps found during the comparison

At the reviewed NodeLift revision, the collectors already provide model, OS, app version, physical RAM, an available-memory value, CPU count, battery, thermal state and transport. Android also reports process PSS. The current [benchmark guide](../../docs/wiki/Benchmarking.md) already distinguishes synthetic diagnostics from native inference.

The most important gap is **memory scope in the protocol**:

- [Android NodeService](../../apps/android/app/src/main/java/dev/nodelift/companion/NodeService.kt) sends ActivityManager `availMem` as `available_memory_bytes`. Android documents this as [system available memory](https://developer.android.com/reference/android/app/ActivityManager.MemoryInfo#availMem), not a guaranteed app allocation budget.
- [iOS NodeModel](../../apps/ios/NodeLift/NodeModel.swift) sends `os_proc_available_memory()` under the same field. Apple documents this as [current app allocation headroom](https://developer.apple.com/documentation/os/os_proc_available_memory), an advisory value that can change during execution.
- The mobile displays and [desktop graph](../../host/nodelift/graph.js) already distinguish those labels. The graph infers scope from the OS string; the shared protocol field itself remains ambiguous. This is a contract improvement, not a claim that the current UI labels are identical or that a current scheduler has been shown to misallocate memory.
- The host's [capability sanitizer](../../host/nodelift/state.py) accepts a limited field list. New inventory data would be discarded without coordinated collector, protocol and host changes.

Proposed migration: separate `system_available_memory_bytes` from `process_memory_headroom_bytes`, retain `physical_memory_bytes` and scoped process footprint, and include source, sample time and unavailable reason. Preserve compatibility for older companions without silently converting system availability into an app budget. CPU counts likewise need semantics: logical/physical/active/worker-allowed are not interchangeable. Do not add CPU and GPU unified memory twice or present summed phone RAM as a single shared address space.

## Integration priorities and acceptance criteria

This is a proposed implementation sequence; the changes below are not included in this research commit.

| Priority | Change | Acceptance criterion |
|---|---|---|
| P0 | Explicit memory scope, units, unavailable states and sample freshness in the protocol | Android system availability and iOS process headroom cannot be aggregated as the same metric; old clients retain correct labels. Unknown battery/memory is distinct from zero. |
| P1 | Public Android SoC/ABI probes and a pinned Apple identity adapter | Known, unknown, simulator and unsupported-API cases work offline; catalog provenance is visible; no hidden APIs or benchmark-loop GC requests. |
| P1 | Backend capability records | Distinguish hardware advertised, backend built, runtime probe passed and inference qualified. A GPU/NPU name alone never enables a route. |
| P1 | Device graph enrichment | Separate catalog specifications, fresh telemetry and measured task profiles; display limits and unavailable values. Useful committed-token contribution remains distinct from compute utilization or acceleration. |
| P2 | Bounded native calibration and connected inference profiles | Reproducible workloads, correctness checks, transport and thermal records, host-only baseline, repeated trials and documented failures. |
| Deferred | Native HarmonyOS/NEXT collector and worker qualification | SDK/build work resumes only after the postponed work is reopened; neither reviewed library establishes native HarmonyOS/NEXT compatibility. |

Store per-field provenance (`catalog`, `OS API`, `backend probe`, `benchmark`), units, sample time, source revision where applicable and an explicit validity state. Inventory should not collect IMEI, serial numbers or account identifiers: the existing enrolled-node identity is sufficient for this purpose.

## Benchmark design derived from the review

The useful device weight is workload- and topology-dependent. GHz, TOPS, core count and RAM capacity alone are not performance weights. Extend the existing [benchmark protocol](../../BENCHMARK_PROTOCOL.md), preserving raw records and the distinction between planned tests and observed results.

| Layer | Measurement and controls | Interpretation |
|---|---|---|
| Collector overhead | Compare idle and fixed workloads with telemetry on/off; record polling interval, CPU time, allocations and latency | Confirm that observation does not materially distort the benchmark. Sample thermal state at a bounded rate outside the timed inner loop. |
| Transport | Actual HTTPS/protocol upload/download payloads, application RTT, jitter and p50/p95; persistent/cold connections and paced requests separately | Evaluate the actual phone-hotspot-to-host path. Compare USB/Ethernet only when those interfaces work on the particular device; a nominal Wi-Fi version is insufficient. |
| Native compute | Same native kernel/version, quantization, dimensions, thread settings and correctness checks; memory-bandwidth working sets beyond cache, within a bounded budget | Cross-device calibration must use comparable work. The existing Android single-thread Kotlin 256×256 FP32 matvec is a synthetic diagnostic, not an LLM throughput prediction. |
| Local inference | Exact model/hash, tokenizer, backend, context length, prompt/output tokens, prefill, decode, TTFT, warm/cold load and peak footprint | Establish whether that node can perform the proposed task, with correctness/output checks. Keep model loading separate from steady-state latency. |
| Delegated inference | Paired host-only, host local-draft and phone remote-draft trials; randomize order, retain failed/fallback trials, actual output token counts, accepted/rejected proposals and end-to-end elapsed time | Speedup = matched host-only elapsed time / delegated elapsed time. Compare single-response latency and aggregate throughput separately. Acceptance share alone is not speedup. |
| Sustained operation | Repeated runs long enough to observe thermal behavior, with battery/charging/lifecycle records and cancellation limits | Record throttling and variance rather than extrapolating from a short burst. Do not claim joules/token from battery percentage; energy needs a valid measurement method and baseline. |

Use a small pilot to choose safe durations and estimate variance, then repeated paired runs with reported uncertainty. Define a practical improvement threshold before evaluation; do not promote a route on a single faster run. Capacity expansion needs its own test proving that a supported partitioned workload executes when the matched host-only workload cannot fit. Draft offload and hardware discovery do not establish that result.

## Evidence and limitations

Reviewed repository READMEs, manifests, license texts and the implementation/test files linked above. Also inspected android-hrwinfo's `AdrenoGPU.java` (vendor-specific sysfs approach) and compared NodeLift's capability sanitizer, collectors, graph and benchmark documentation. Repository dates are metadata observed on the assessment date; they do not prove support for every listed device. Apple/Android API semantics were checked against the linked official documentation.

No runtime performance, hardware support, Intel behavior or physical-phone acceleration was newly validated. No GLM or Gemini review was performed for this assessment. Neither project was installed or added to dependency/license inventories because no code was adopted. This report records what to reuse conceptually, what requires correction and what must be measured before making performance claims.
