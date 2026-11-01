# NodeLift and Apple MLX distributed inference

1 November 2026. **NodeLift has not demonstrated superiority to Apple's distributed inference.** The useful opportunity is to make heterogeneous personal devices participate when measured benefit justifies the cost, with explicit evidence and graceful fallback. This is an architecture assessment, not a new benchmark result or an implementation of model sharding.

## Comparison grounded in current evidence

Apple's [15 October research article](https://machinelearning.apple.com/research/mlx-distributed-inference) reports multi-Mac pipeline and tensor inference over Thunderbolt RDMA. It measures TTFT, decode and peak power with specified models and context lengths. Its four-M5-Ultra example reports 36.73 tokens/s for Muse Spark Open at 8,192-token context. This is a published vendor result, not a NodeLift reproduction. Pipeline depth partitioning expands capacity; tensor width partitioning adds frequent communication and benefits from the fast interconnect.

[MLX distributed documentation](https://ml-explore.github.io/mlx/build/html/usage/distributed.html) supplies the backend/collective interface and deployment details. A NodeLift backend adapter could use these primitives on compatible Macs; it would not make Thunderbolt RDMA available to ordinary Android/iOS hotspot nodes.

The distinction is between Apple's published Mac experiment and the whole MLX framework: current communication documentation also lists MPI, TCP RING and NCCL for CUDA. MLX must not be described as exclusively a Mac-to-Mac runtime. JACCL currently requires a fully connected supported Thunderbolt topology. The owner's [M3 Max MacBook Pro has Thunderbolt 4](https://support.apple.com/en-us/117737); it is not the Thunderbolt 5 RDMA hardware demonstrated in the article.

There is also a configuration issue to qualify: the article enables `MLX_METAL_FAST_SYNCH=1`, while the current documentation recommends leaving it unset because of a possible GPU deadlock, referencing [upstream issue 3142](https://github.com/ml-explore/mlx/issues/3142). Record versions and flags and test the actual configuration. This warning is not evidence that every MLX backend or the published benchmark is invalid.

| Dimension | Apple MLX comparison point | NodeLift implemented/observed state |
| --- | --- | --- |
| Capacity | Target model can be partitioned across Macs | Target-model capacity sharding is not implemented; phone draft weights do not extend target-model memory |
| Acceleration | Published homogeneous-cluster inference measurements | Small-pair local drafting was slower; no phone LLM speedup demonstrated |
| Hardware | Published multi-Mac test; MLX also documents CUDA/NCCL and other communication backends | M3 Max host; Android ARM64 CPU and iOS Metal/CPU companion code; physical inference qualification open |
| Network | Low-latency wired collectives | Hotspot application HTTPS p50 around 6–9 ms, with substantial tails; no sustained under-load link qualification |
| Reliability and control | Framework/runtime capability, separate from a consumer companion lifecycle | Pairing, identity checks, consent, thermal/battery limits and bounded fallback exist; effect on long real sessions remains unqualified |
| Evidence | Vendor benchmark configuration is published | Raw local results, failures and limits are published; model reviews are advisory |
| Governance | The cited research is not a complete governance audit | Implemented controls do not prove superior governance, independent security assurance or policy compliance |

NodeLift evidence: [engine results and numerical divergence](../measurements/ENGINE_RESULTS.md), [physical hotspot diagnostics](../measurements/2026-10-31-xiaomi-hotspot/REPORT.md), [architecture](../../docs/ARCHITECTURE.md). The 0.719× local-draft result did not use a physical phone. Its cause cannot be attributed to hotspot or mobile CPU performance. Network diagnostics are not tokens/s measurements.

## Proposed execution architecture

These are proposed lanes, not newly shipped backend capabilities:

The concrete [distributed execution RFC](../../docs/RFC_DISTRIBUTED_EXECUTION.md) now specifies admission, context synchronization, cancellation, shard recovery, evidence contracts and acceptance gates. It preserves capacity and acceleration as separate core workstreams.

1. **Fast wired compute.** Keep a single public local gateway and backend adapters. Use the selected optimized host backend as baseline. Add optional MLX multi-Mac execution only after capability discovery, pinned runtime configuration and repeatable deployment checks. Distinguish model capacity from speed.
2. **Heterogeneous wireless assistance.** Retain host-only default. Admit remote drafting only from observed complete round timings, accepted-prefix results, failure rate and thermal headroom. Separately investigate coarse independent jobs such as embedding batches or document preprocessing; they can amortize one network exchange without serial per-layer synchronization. These job types are not current worker capabilities.
3. **Capacity research.** Investigate contiguous target-layer partitions with local KV ownership and chunked prefill when the model does not fit the host. Report extra capacity, TTFT, inter-token latency, recovery cost and output behavior separately. A disconnected required shard cannot fall back to a host that cannot fit the model. Checkpoint/restart and explicit failure must be designed before promising continuity.

An application using the gateway can select a supported local route. A cloud GUI does not gain local RAM merely by running on the same computer; it needs an actual custom-endpoint/provider interface. Nor can the OS transparently combine phone RAM into the host's unified memory through this application.

## Admission rule and benchmark contract

For an observed run or block, use:

`effective cost = total elapsed wall time / actually committed output tokens`

`paired speedup = host-only completion time / delegated completion time`

Measure wall time across draft dispatch, device work, verification, synchronization, serialization, transport, rejected work, timeout, cancellation and fallback. Component timings are useful only when their intervals and overlap are defined. Do not add TLS/serialization costs again if they are already inside application HTTPS RTT. Do not replace accepted-prefix length with an unconditional per-token acceptance percentage. Compare identical workload and output contracts, recording EOS and actual output lengths.

Qualification requires frozen model/runtime/source hashes, context, sampling settings, warm/cold policy and backend; randomized paired order over representative prompt groups; multiple independent sessions; sustained thermal runs; and raw failure/cancellation retention. Report prefill, TTFT, decode rate, total completion time, memory headroom, battery/energy where measured, per-node useful and discarded work, and uncertainty. Confidence intervals must respect prompt/session grouping. Small samples do not justify stable p99 claims. Avoid selecting only same-output successes without reporting the excluded cases and denominator.

A positive performance claim needs a prespecified minimum worthwhile improvement and uncertainty bounds, plus correctness and reliability gates. Operational fallback can respond immediately to heat, network loss or a worsening measured cost; publication should not use repeated uncorrected significance peeking as proof of superiority.

## Correctness before speed

The existing 96-token experiment found a greedy batch/single mismatch beyond the earlier 64-token sample. That is a real counterexample to universal exact-output claims. The precise numerical cause is not established here. Logit margins can help diagnose it but cannot prove equivalence or justify an arbitrary epsilon-exact label. A strict mode would need reference-path recomputation and tested state rollback before committing output; its cost belongs in the speed comparison. Stochastic distribution preservation is a separate contract from matching a greedy token sequence.

## External review and adjudication

An actual Gemini 4 Argon High browser request reviewed this comparison on 1 November. Accepted: distinguish capacity/acceleration, separate wired and wireless execution, measure complete cost, retain failure evidence and avoid governance-superiority claims. Rejected or qualified: invented phone/host token timings, a claimed causal explanation for the local 0.719× result, a confirmed numerical root cause, an arbitrary epsilon-exact threshold, universal capacity-mode slowdown, and description of current pairing as mutual TLS client-certificate authentication. No such measurements or guarantees are adopted.

The first requested GLM 5.3 Max attempt was rejected by the service's peak-hours capacity limit. A subsequent browser request on the same date, with GLM-5.3 and Max selected, completed an independent architecture review. No Flash substitution was accepted. It agreed that superiority is unproved and recommended measured profiles, context deltas, cancellation accounting and explicit shard-loss behavior. These are advisory recommendations, not execution evidence.

A fresh Gemini request with the UI's Argon High setting also completed. Its first response in the earlier mixed-purpose conversation was a generic refusal; the isolated technical conversation produced the assessment. The substantive answer still contained unsupported conclusions. The requested corrective follow-up returned another generic refusal; no second-round Gemini approval is claimed.

The [review adjudication](REVIEW_ADJUDICATION.md) records both models' contributions and rejected claims. In particular, neither a local slowdown nor a sequential pipeline dependency proves universal failure of remote execution. An epsilon in logits does not establish exact token equivalence, a missing mTLS client certificate is not automatically a security defect, and measured request intervals must not have TLS overhead added twice. Reviewer agreement is not a benchmark or security audit.

No large model was downloaded or executed for this assessment. The suggested model's [actual README](https://huggingface.co/AtomicChat/DeepSeek-V4.1-Flash-1017-Uncensored-GSQ-RCO-GGUF/blob/main/README.md), rather than the hosting site's generic usage widgets, states a Strata-specific execution path and a separate 110 GB Engram table. It lists roughly 231–266 GB total across quantization choices and says this split architecture is not yet supported by llama.cpp at the time of writing. The reported 12 GB GPU configuration also uses system RAM and SSD storage; it does not mean a 12 GB total-memory requirement.

Repository metadata identifies revision `4f1d2f730cff977961db81789e81bfc0d3e6dd2e` and MIT licensing. The lowest listed four-shard set alone totals 120,721,120,256 bytes, before the separately hosted Engram table and execution state. This does not fit the current 64 GiB host as a resident model, and current NodeLift does not implement this backend or distributed architecture. The model is a possible later capacity experiment, not a reviewer we actually ran. The uncensored label is not evidence of better engineering reasoning; evaluate task accuracy, license, runtime and resource fit independently.

## Next engineering gate

Finish physical companion pairing and diagnostic export, then obtain an eligible phone draft and supported large target. Complete the already separate benchmark runner qualification before executing a sustained Mac-only versus delegated study. Until those gates pass, publish the architecture as a research direction and keep host-only as the default.
