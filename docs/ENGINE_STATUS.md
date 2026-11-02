# What NodeLift executes today

Status reviewed on 2 November 2026 against the released host source and running local host. Companion packages remain 0.2.11/build 13. This is a capability assessment, not a new inference benchmark.

NodeLift has a working experimental inference path and a device orchestration layer. It does not yet deliver its central capacity objective: a model that cannot fit on the host cannot be made to fit by adding phones.

## Original code and dependencies

The original NodeLift code is MIT-licensed, not a closed proprietary inference runtime. Its host controller, authenticated device work protocol, verification wrapper, measurement presentation, companions and adapters are project code. Tensor kernels, model loading and device execution depend on the pinned llama.cpp revision in [native/llama.lock](../native/llama.lock). Remote speculation and prompt lookup are existing techniques; using them does not establish a new algorithm or superiority over another runtime.

## Capability matrix

| Capability | Current behavior | Limit or evidence boundary |
|---|---|---|
| Native model execution on the Mac | Loads supported complete GGUF files and generates text using the native core | Host must fit target weights, KV cache and runtime overhead. Import success does not establish load compatibility. |
| Local drafting | A smaller model proposes a block; the target verifies it | Compatible token vocabulary required. Both models use host resources. No general speedup demonstrated. |
| Phone drafting | A selected companion receives an authenticated lease and proposes token IDs; the host verifies every accepted token | One selected remote drafter per run, not a joint multi-phone target. Stable physical inference and speedup remain unqualified. |
| Prompt lookup | Proposes repeated context continuations without another model | Useful only when matching text occurs; target verification still runs. |
| Adaptive draft control | Measures initial host and draft steps, returns to host-only when observed delegation loses | Experimental request-local heuristic, not automatic best-device selection or a no-regression guarantee. |
| Hugging Face and direct import | Public GGUF search, metadata, immutable file selection, verified download and complete local-file import | No automatic safetensors conversion, split-GGUF assembly or gated-license acceptance. |
| Local API bridge | Routes text to a separately running LM Studio/oMLX-compatible loopback server | The external runtime owns execution. NodeLift does not inject phone acceleration into that runtime. |
| OpenRouter | Explicit cloud text route with a configured session key | Can incur charges; does not use phone compute or expand local RAM. |
| Client integration | Restricted OpenAI-style text API plus an LM Studio generator adapter | Full LM Studio GUI/plugin installation is separately unqualified. Not an internal Ollama plugin. No qualified Z.ai/MiMo GUI integration. |
| Device assessment | Sequential connection diagnostic and synthetic CPU calibration, with history and readiness classification | These are not model-specific LLM benchmarks and cannot predict tokens/s or speedup. |
| Contribution view | Shows accepted draft-token attribution for a selected run, recorded wait and fallback | Token share is not CPU/GPU utilization or saved wall time. Host verifies all native output. |
| Memory expansion | Phone RAM can hold its own draft model | No target-weight partitioning, shared KV cache, coherent memory pool or capacity sharding. |

## Native limits that matter

The native path is greedy only. Its configuration currently accepts context sizes from 256 to 8192 and output budgets from 1 to 512 tokens. The real limit also depends on the model and available memory. Recurrent/hybrid models are rejected by the wrapper because checkpoint rollback is not qualified. There is one active generation, without continuous batching or asynchronous multi-device execution.

The local gateway supports a text-only subset, not full OpenAI API compatibility. Tool calls, multimodal input, arbitrary sampling and structured response formats are unsupported. See [integration parameters and explicit rejections](INTEGRATIONS.md).

The phone drafting protocol sends the full prefix each round. Serialization, transfer and remote prefill can therefore grow with context. Acknowledged context deltas, resident target partitions and recovery when a shard disappears are design work, not shipped features.

## What the measurements establish

The frozen small-model study found local drafting slower than target-only execution: block size 4 produced a median paired end-to-end ratio of 0.719x. A later study found adaptive local drafting close to, but below, host-only on its general-prompt sample (0.961x median). A narrow repetitive-text case benefited from lookup. These are different studies with documented denominators, not current release certification.

A longer-output test also exposed a numerical batch-versus-single decoding mismatch at token 75. Target verification is implemented, but universal exact token equality with host-only generation is not established. There is no demonstrated physical-phone inference speedup. The published [engine measurements](../research/measurements/ENGINE_RESULTS.md) retain both the negative results and the correctness limitation.

The existing automated tests establish specific protocol and application behaviors. They do not prove sustained phone performance, battery benefit, thermal stability or a successful matched Mac-only/Mac-plus-phone benchmark. The separate benchmark-runner changes in the local workspace remain unfinished and are not treated as released functionality.

## Next engine gates

1. Qualify stable real-device work delivery, cancellation, thermal behavior and failure recovery with the installed companion.
2. Resolve or precisely constrain the known numerical mismatch before broader equivalence claims; support hybrid rollback only with evidence.
3. Run repeated matched Mac-only versus Mac-plus-device tests, recording end-to-end latency, prefill, decode, acceptance, wasted proposals and fallback under the same output policy.
4. Reduce context-transfer overhead only after acknowledged state synchronization and recovery are tested.
5. Implement a separate capacity path with resident target partitions, memory accounting and recovery for models that cannot fit on the Mac. Drafting alone cannot satisfy this objective.

## Contextual help

The desktop control room provides explicit information buttons beside the main controls. Open Options to disable or restore contextual help. The preference belongs to the current browser and is saved when browser storage is available; essential warnings remain visible. Help explains behavior and limitations, and does not start a benchmark or change engine configuration.

## Scoped impact measurement

[NodeLift Impact v1](IMPACT_BENCHMARK.md) now collects paired native SSE sessions and analyzes time saved, TTFT change, full-denominator reliability, instrumented energy availability and uncertainty for one model/device/connection scope. The dashboard imports recorded sessions in Measurements. This is an explicit benchmark collector and evidence analyzer, not automatic routing or qualified mobile acceleration. The [initial physical pilot](../research/impact-2026-11-02/REPORT.md) found no speed benefit; energy and independent-session confidence remain unavailable.
