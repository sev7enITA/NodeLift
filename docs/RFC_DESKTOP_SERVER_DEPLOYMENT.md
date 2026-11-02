# Desktop, workstation and server deployment

Status: accepted product scope, proposed implementation. 2 November 2026. This document extends the [distributed execution contract](RFC_DISTRIBUTED_EXECUTION.md); it does not ship a Windows/Linux worker, server installer or a qualified mixed-backend cluster.

## Product boundary

NodeLift is a local execution service with a control room and device workers. Windows and Linux PCs, GPU workstations, macOS computers and dedicated servers are first-class target nodes alongside mobile companions. The coordinator and the target-model executor are separate roles: the Mac need not remain the fastest or primary executor. The user's Lenovo P16 is the first proposed non-Mac qualification device; its OS, generation, GPU, VRAM, RAM and usable connection are not yet verified.

Keep the two user objectives explicit:

- **Acceleration:** lower single-request completion time against the best eligible standalone machine and applicable local speculation. Concurrent-user throughput is reported separately.
- **Capacity:** complete a model/context that exceeds a declared single-node budget by placing weights and working state on multiple nodes. A summed RAM inventory is not an allocatable coherent address space.

A router that sends the entire request to the P16 can be useful, but is whole-request routing, not combined inference. Do not label it multi-device acceleration. Distributed model execution remains a separate qualification gate.

## Proposed deployment units

| Unit | Responsibility | Initial delivery target |
| --- | --- | --- |
| Coordinator and local API | Admission, user/project access, queue, topology, run identity, evidence and cancellation | Existing Mac host extended first; headless Linux coordinator later |
| Desktop worker | Explicit enrollment, bounded native execution, model cache, telemetry and a visible pause control | Windows or Linux P16, chosen after inventory |
| Dedicated worker | Same bounded protocol, unattended lifecycle, resource reservations and structured logs | Linux server; Windows service only after its lifecycle is tested |
| Mobile companion | Optional draft work and, only after qualification, eligible model partitions | Existing Android/iOS enrollment and experimental draft path |
| Backend adapter | Advertise verified operations and model/backend compatibility | Pinned native backend first, upstream comparison paths separately |

Service installation, startup persistence and remote administration require a deliberate operator action. Discovery only offers candidates for enrollment; a discovered office PC is not authorized to execute work. QR and one-time enrollment codes should converge on the same authenticated node identity and revocation policy. No generic remote shell is part of the worker protocol.

## Backend candidates, not a support matrix

| Hardware/runtime family | Candidate | Qualification boundary |
| --- | --- | --- |
| NVIDIA workstation/server | llama.cpp CUDA | Exact GPU, driver, runtime, allocation and actual inference must pass; no GPU use inferred from the product name |
| Apple silicon | Existing Metal path; MLX comparator/adapter | Single-node Metal and multi-Mac JACCL are separate capabilities; no JACCL promise for Windows/Linux/phones |
| AMD / Intel / other GPUs | Applicable upstream HIP, Vulkan or SYCL backend | Per OS/GPU/model qualification; no automatic interchangeability or NPU claim |
| CPU-only computers | Optimized native CPU backend | May be excluded from a latency route while useful for an independently qualified task |
| Heterogeneous model partitions | Prima.cpp as reproducible reference; bounded native partition adapter | Source revision, license, tensor/state contract, cancellation and authenticated transport reviewed before incorporation |

Primary upstream references checked on 2 November 2026: [llama.cpp build/backends](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md), [MLX distributed communication](https://ml-explore.github.io/mlx/build/html/usage/distributed.html), [Prima.cpp](https://github.com/OpenCPIL/prima.cpp). These describe upstream functionality, not NodeLift support. Preserve upstream authorship and notices in any incorporation.

The [llama.cpp RPC example](https://github.com/ggml-org/llama.cpp/blob/master/tools/rpc/README.md) explicitly describes itself as a fragile, insecure proof of concept. It is a lab comparator, not an office-facing daemon. Wrapping it in TLS alone does not establish safe parsing, authorization or resource isolation.

## Office and construction-site operating profiles

**Dedicated pool:** operator-reserved servers/workstations can hold required partitions. Reserve RAM and each GPU's VRAM separately, account for weights, KV/state, scratch, loading transients and concurrent runs. A reported free-memory snapshot is not a reservation.

**Shared workstation pool:** lend resources only within user-approved schedules and budgets. Support pause, drain and return-to-user behavior. UI activity and battery/thermal signals can stop new admission; cancellation and resource release need measured bounds. A process priority setting does not guarantee that CAD, BIM or other interactive GPU work is unaffected. Measure interference before calling the profile non-disruptive.

**Site-local pool:** a local coordinator and cached model artifacts allow qualified execution without external internet. Treat Wi-Fi movement, power loss, sleep and worker disappearance as ordinary conditions. Wired Ethernet is the first comparison where available; qualify actual application-level latency, goodput and contention on each link rather than deriving performance from a port label. Cross-site/WAN execution is out of the initial scope.

Required capacity partitions must not depend by default on opportunistic workers. An operator can opt into a fragile topology only with an explicit interruption policy. If a required shard disappears and the remaining nodes cannot hold it, the run must report interruption or use an already qualified recovery route. It cannot promise host-only fallback. Draft loss can fall back when a complete target remains resident.

## Data and organizational boundaries

All prompt-bearing flows, including token IDs, activations and KV state, stay within the selected trusted pool. Node admission is per owner/project; a workstation approved for one project is not automatically approved for another. Model distribution respects access conditions and pinned artifact hashes. No ambient directory sharing, unrelated file indexing or silent cloud fallback is implied by enrollment.

The first office pilot is restricted to approved machines and public test prompts. Multi-user authentication, queue isolation, per-project scheduling, cache ownership, revocation and retention controls are production prerequisites, not capabilities asserted by this design. Logs should retain resource and run diagnostics without prompts by default. The user explicitly chooses diagnostic export.

## Capability record and graph requirements

Record independently:

- Private installation identity, OS/runtime/build revision and last successful contact/session.
- CPU capabilities; GPU devices and backend probe results; system RAM, per-GPU dedicated VRAM and any shared/unified memory relationship. Never double-count shared memory as RAM plus VRAM.
- Current user-approved resource ceiling and active reservations, power/thermal availability, and operating profile.
- Supported model architecture/quantization/context, exact artifact identities, tested operations, correctness contract and evidence timestamp. Unknown remains unknown.
- Per-link measured connection identity, latency/goodput distribution and topology generation. An IP address is not a stable identity or performance profile.
- Current role: coordinator, whole-model executor, verifier, drafter, capacity partition, idle or excluded. Show the exclusion reason.

The device graph should expose reserved versus available memory and the actual selected role. Link animation reflects active work; accepted draft share, bytes transferred, GPU utilization and wall-time benefit are distinct metrics. Missing power telemetry cannot become zero consumption. A model/backend/topology change invalidates the relevant qualification profile.

## First P16 experiment

1. Obtain a local inventory without serial numbers, usernames, credentials or document contents. Establish OS, GPU/VRAM, RAM, driver/runtime and Ethernet/Wi-Fi options. No remote access to the Lenovo has been established.
2. Build/load the same compatible target and draft artifacts on P16 and Mac. Verify optimized kernels and actual accelerator allocation. Record output-contract differences across Metal/CUDA rather than assuming bitwise equality.
3. Compare Mac alone, P16 alone, Mac verifier plus P16 draft, P16 verifier plus Mac draft, and best applicable local speculation on each machine. Whole-request routing is a separately labelled control. Keep failed, cancelled and fallback runs in the service denominator.
4. Introduce a third opportunistic node only after the two-machine path works. Measure marginal benefit by adding/removing that node, including user-workload interference; never force all enrolled devices into the run.
5. Qualify contiguous resident partitions with a small compatible model first. Then test an honestly disclosed capacity-limited workload. Artificial memory caps and a target exceeding physical memory are different experiments and must be labelled separately.
6. Compare stable wired and available wireless routes in separate cells, with repeated sessions and sustained load. Include node sleep, disconnect, drain, cancellation, concurrent client admission and recovery where implemented.

The primary speed baseline is the fastest eligible standalone configuration under the same declared model, precision, context and output policy. A mixed cluster that beats the Mac but loses to the P16 alone has not established a distributed speed advantage. A whole-model execution route on the P16 may still be the correct product decision.

For office scale, additionally measure queue delay, p50/p95 TTFT and completion time, completed requests per interval, failure rate and interference with representative local work. Throughput and capacity gains do not replace the single-request latency requirement. Total energy requires aligned, measured power traces for the complete participating set.

## Delivery gates

1. Inventory and standalone P16 baseline.
2. Authenticated desktop worker and lifecycle, exercised with a single bounded task and disconnect/cancel tests.
3. Matched two-machine draft experiment and timing decomposition.
4. Resident partition experiment and honest capacity demonstration.
5. Multi-user admission, resource isolation and an approved office/site pilot.
6. Signed installers/service packaging and an explicitly tested platform/backend/version matrix.

At this revision, these are planned gates. No Lenovo benchmark, Windows/Linux worker, enterprise deployment or new mobile build is claimed. Existing physical phone evidence remains in the [performance diagnosis](../research/performance-diagnosis-2026-11-02/REPORT.md).
