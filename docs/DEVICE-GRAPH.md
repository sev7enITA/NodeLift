# Device graph and contribution

The desktop **Devices** section exposes an interactive relationship graph of the computer and paired companions. Select an entity to inspect its hardware, role, reported limits and measured contribution. The run selector provides the context: a previous run is historical evidence, even while devices are currently online. Existing network/CPU diagnostics and pairing controls remain available.

The selector covers up to 30 runs in the current host process. Restarting the host clears that in-memory list; native experiment files remain in private host storage. [Verification and limitations](evidence/device-graph-2026-11-01/README.md) distinguish real host checks, synthetic fixtures and device qualification.

## Reading the graph

| Field | Meaning and limits |
|---|---|
| Online / offline | Last authenticated contact within 20 seconds, excluding revoked nodes. Reachability alone does not prove inference readiness. |
| Telemetry time | Host receipt of pairing/heartbeat capabilities. Contact can be newer than telemetry. Legacy records have an unknown sample time until their next heartbeat. |
| Host hardware | Operating-system inventory cached at process startup/first access. No machine name, serial number or identifier is collected. Live RAM utilization and accelerator speed are unknown. |
| Mobile hardware | Companion-reported model, OS, CPU cores and physical memory where available. No chip throughput is inferred from a marketing name. |
| Android available memory | System available memory; process memory, when present, is PSS. |
| iOS available memory | Process allocation headroom, not whole-system free memory. These quantities cannot be summed into a shared RAM pool. |
| Network measurement | Dated application-level HTTPS RTT and payload goodput. Direction, payload size and pacing affect results; these are not a continuous network monitor. |
| CPU measurement | Dated synthetic kernel rate; it does not predict LLM tokens/second. |
| Native readiness | Companion reports a loaded draft and model/tokenizer identities. It is not proof of sustained performance or compatibility with every target. |

Offline samples remain historical. Unknown data is displayed as unmeasured rather than zero. Default limits documented for a companion build are not current user-selected settings; current heartbeats do not report the draft-size/context/thread/battery thresholds.

## Output attribution, not compute attribution

For a native run, the accepted mobile draft share is:

```text
sum(block.accepted where block.effective_mode == remote_draft)
----------------------------------------------------------------
sum(block.generated over all completed native blocks)
```

The numerator belongs only to that run's `node_id`. Local draft acceptance and context-reuse proposals never count as phone work. Counts include committed EOS/EOG token IDs. Proposal tails that were never examined after a mismatch, EOS or output limit are **not committed**, rather than necessarily rejected by the target.

The complementary output count combines ordinary host generation, target corrections, bonus tokens and any local proposals. The host verifies all phone proposals before committing output. A 40% accepted mobile draft share therefore does **not** mean the phone performed 40% of the computation, saved 40% of the time or supplied 40% of model RAM.

Host-observed remote wait includes phone computation, transfer, polling, scheduling and failed leases. It cannot be separated into network and phone-compute time using current evidence. Native-call, block and round timings are nested and must not be added as independent slices. Decode tokens/second excludes load/prefill; a matched baseline is needed to measure acceleration. Loading or a pending remote lease may have no completed block yet, which is unknown progress rather than zero activity.

An external provider run has no native per-phone attribution. A missing measurement, empty/loading run or incomplete record must not invent a zero-percent result. The current engine uses at most one remote drafter in a run; multiple paired entities do not imply simultaneous multi-phone execution.

## Product shape

NodeLift's core product is a **shared local execution service that aims to supply device RAM and compute to everyday AI interfaces**. Its desktop application is the control room; mobile companions provide resources and adapters connect clients. Today the desktop interface is served by the Python host in a browser. A signed native desktop installer and OS-integrated lifecycle remain packaging work. The local service, gateway and drafting core exist; capacity sharding remains to be implemented. The [product roadmap](ROADMAP.md) separates these milestones.

| Environment | Relationship to NodeLift | Current status |
|---|---|---|
| NodeLift control room | Configure models, pair devices, run experiments, inspect evidence | Implemented browser interface on loopback |
| Android / iOS | Native draft companion with lifecycle and resource guards | Source and companion artifacts; physical inference qualification remains separate |
| HarmonyOS NEXT | Separate companion path | Source/qualification work; no Android APK compatibility assumption |
| LM Studio GUI | Generator adapter routes supported text requests to NodeLift | Adapter and SDK/live-gateway checks; complete GUI installation/generation not qualified |
| LM Studio / oMLX server | Explicit external text backend used by NodeLift | Loopback API bridge; no mobile drafting on this route |
| Ollama | Separate runtime; compatible clients may choose NodeLift's endpoint instead | No injection into Ollama, no automatic distribution of an Ollama-loaded model; server bridge must be qualified separately |
| Z.ai web GUI | Hosted chat application; its API is a separate provider route | Official API assessed; no direct provider adapter or browser extension implemented |
| Xiaomi MiMo web GUI | Hosted demo/platform; API is a separate provider route | Official API assessed; no direct adapter or reuse of the web GUI's compute implemented |
| OpenRouter | Explicit opt-in cloud provider | Existing integration; model availability and charges belong to the provider |
| Hugging Face / local files | Source of compatible model weights | Public single-file GGUF import; architecture/license/device fit still required |

Z.ai documents an [OpenAI SDK-compatible API](https://docs.z.ai/guides/overview/quick-start). Xiaomi documents its [API credentials and OpenAI-compatible endpoint](https://mimo.mi.com/docs/en-US/quick-start/summary/first-api-call), separately from the [web demo](https://mimo.xiaomi.com/). Those documented APIs are the intended integration surface. There is no demonstrated custom-local-endpoint route from their hosted GUIs to NodeLift; browser login is not an API credential. Future provider adapters must remain explicitly cloud-routed and must not appear as local hardware contribution.

See [integration details](INTEGRATIONS.md), [engine architecture](ARCHITECTURE.md) and [benchmark methodology](wiki/Benchmarking.md).
