# NodeLift Impact v1

NodeLift Impact is an original measurement and decision policy for a specific model, host, candidate device and connection. It uses established paired statistics. It is not a new statistical theorem, a universal device score, shared RAM, or a qualified inference accelerator.

## Current implementation

- `scripts/benchmark-impact.py collect` explicitly runs a frozen, balanced AB/BA plan against the local native OpenAI-compatible gateway. Three public prompts, fixed greedy decoding, a fixed draft policy and token budget are used. One unscored pair warms the run first. The collector does not change engine configuration.
- The collector captures actual SSE arrivals with its monotonic clock, matches the exact native run ID, checks target/draft/config identity, and retains failed, cancelled, missing, fallback and mismatched attempts. It checks companion readiness, address and observed session continuity before and after runs. Output token arrays are hashed in full; hashes and counts are compared.
- Each primary attempt is atomically persisted after completion. The frozen plan is saved before inference; a crash during a run leaves that slot missing. No retry silently replaces a failed attempt. These are checksummed local records, not signed or tamper-proof evidence.
- `host/nodelift/impact.py` calculates the vector below. Authenticated `POST /admin/impact/analyze` accepts a session object within the existing 1 MiB request limit.
- **Measurements > What did delegation change?** imports a session JSON, explicitly analyzes it on the local host and exports its report. It does not start inference or send records to a cloud service. Imported records are reported evidence, not live device attestation.

## Five dimensions

| Dimension | Definition | Interpretation |
| --- | --- | --- |
| Time saved | Median of paired `host duration - candidate duration`, and median paired percentage | Positive is faster. Primary estimate requires complete, output-equivalent, fallback-free pairs. |
| TTFT change | Median of `candidate TTFT - host TTFT` | Negative is earlier first response text. |
| Reliability | Completed, output-equivalent strict successes, fallback, failure, cancellation and missing counts, all divided by planned attempts | Fallback completion is service recovery, not successful device acceleration. Equality is not semantic correctness. |
| Measured energy | Median paired `host joules - candidate joules`, from matched meter scope and complete traces | Positive means less energy to completion for the declared components. Missing measurements remain unavailable. |
| Uncertainty | Approximate percentile bootstrap resampling whole sessions, with counts, exclusions and qualification gates | Below 10 sessions: no interval. Identical bootstrap bounds: interval unavailable, not zero uncertainty. |

The report also includes `service_time_saved_ms` and `service_ttft_change_ms` over completed, equivalent-output pairs **including fallback overhead**. These are separate from the clean mechanism estimate. Failed or missing completions are not assigned an invented duration; they remain in reliability. Neither conditional estimate is an unconditional production benefit.

TTFT starts immediately before the HTTP request and ends at the first nonempty `delta.content` event. Empty role chunks and heartbeats do not count; whitespace is deliberately nonempty text. This is client text arrival, not the backend's internal first-token timer or screen rendering. End-to-end duration ends at `[DONE]`; a stream without it fails. Chunk bursts are recorded as bursts and never interpolated into token timestamps. A wall-clock/monotonic discontinuity above one second invalidates a run.

The returned `correct` compatibility field means **output-equivalent, successful and fallback-free**, not factually correct. When two completed outputs differ, neither has an external correctness oracle and neither is credited with verified equivalence. Completion counts remain intact. Output counts and stop/length reasons must also agree.

## Scope and qualification

One report contains exactly one scope: target and draft hashes, native library file hash, configuration hash, opaque host/device identifiers, hashed connection description/address combination, candidate mode and warmup policy. Different scopes cannot be merged. Paths, admin/client credentials, raw IP addresses and user prompt history are not exported. The prompts are the fixed public examples in the collector.

The selected native library is hashed as a file. That is not proof of the library actually mapped in the server or the companion's loaded binary. Model/config hashes are reconciled with each final native run. Artifact metadata drift stops further collection. Effective GPU offload, native process residency, thermal recovery, stable load, mobile binary attestation and physically independent sessions are still unqualified.

**`qualified_recommendation` is always false in v1.** No report enables delegation automatically. Directional sample signals are reported separately and cannot become a qualified improvement or regression. The gates show output validity, sample size, missing execution/residency attestation, unverified session independence and energy coverage individually.

The fixed, versioned descriptive policy uses a minimum of 10 independent sessions and 30 eligible pairs, a time-saving margin above 5%, and no TTFT deterioration. These are engineering thresholds, not a proof of statistical validity. Any planned exclusion blocks an improvement signal. Synthetic and host-versus-host evidence can never establish phone acceleration. Duplicate session IDs, run IDs and primary slots are rejected.

Calling the collector ten times consecutively does **not** establish ten independent sessions. The software cannot establish independence from file names. Thermal state, carryover, restart and connection boundaries require a controlled protocol; the independence gate stays unverified. Confidence intervals, when present, are conditional on that assumption. The collector currently records one warm session per invocation and does not force cool-down or restart another application.

The estimator gives equal weight to eligible pairs and resamples their session clusters whole using Python's isolated seeded RNG, 2,000 replicates and linear 2.5/97.5 percentiles. It does not resample tokens or the two arms separately. The Wilson intervals on completion are explicitly IID descriptive, not cluster-adjusted guarantees. Calibration and systematic uncertainty are separate. BCa, simultaneous/multiple-comparison correction, censoring models, holdout qualification and automatic scheduler calibration are not implemented.

## Run a session

Start NodeLift normally, configure a supported target and draft, and leave the native engine idle. For remote draft, keep the selected companion in the foreground with its matching draft enabled. Use the node ID shown by the authenticated local state, never an IMEI.

```sh
python3 scripts/benchmark-impact.py collect \
  --native-library native/build/host/lib/libnodelift.dylib \
  --candidate remote_draft \
  --node NODE_ID \
  --connection xiaomi-hotspot-mac \
  --tokens 32 --repetitions 1 \
  --output /tmp/nodelift-session.json
```

On Linux select the actual `.so` library. `--candidate host` runs an instrumentation control; `local_draft` compares local speculation, not mobile delegation. Credentials are read from the existing private host session and never passed on the command line or exported. A stale dashboard session fails closed.

```sh
python3 scripts/benchmark-impact.py analyze /tmp/nodelift-session.json \
  --output /tmp/nodelift-report.json
python3 scripts/benchmark-impact.py merge /tmp/session-1.json /tmp/session-2.json \
  --output /tmp/combined-sessions.json
```

A partial session remains analyzable after interruption. The collector stops only its own known native run. No native run ID means no blanket stop. It refuses to overwrite an existing collection file. Merging preserves sessions and rejects different scope/evidence kinds, duplicate run IDs and duplicate session IDs. Merging cannot manufacture independence.

## Energy input

No reliable whole-system power meter is connected in the current laboratory. The collector therefore leaves energy unavailable. Battery percentage, rated TDP, nominal FLOPS and capacity are not converted into joules.

An instrument adapter can add an `energy` object to each attempt:

```json
{
  "source": "calibrated-meter-identifier",
  "scope": "whole-system",
  "components": ["host", "phone", "router"],
  "clock": "run_relative_monotonic_ms",
  "unit": "W",
  "max_gap_ms": 1000,
  "calibration_relative_uncertainty": 0.01,
  "samples": [[0, 20], [500, 22], [1000, 21]]
}
```

Samples must bracket the **entire actual attempt duration**, be strictly ordered and finite/nonnegative, and satisfy the maximum gap. Integration uses trapezoids with boundary clipping, no extrapolation. Both arms must have the same source, scope and component list. Calibration uncertainty is retained separately in paired observations and may be unknown. Imported measurements are not independently authenticated.

For whole-system claims, the phone and network idle energy must also be in the host-only measurement, with no double counting of host-powered USB devices. Charging, battery discharge and sensor clock alignment require instrument-level control. A host-only meter supports a host-only claim. V1 reports energy **to each task's own completion**, not equal-horizon energy, battery lifetime or a thermally sustained workload saving. Equal-horizon idle-tail accounting and energy-delay optimization need separate protocols.

## Evidence and references

See [initial physical observations and model-review adjudication](../research/impact-2026-11-02/REPORT.md). Automated fixtures exercise arithmetic and failure handling; they are not physical speedup evidence.

- [llama.cpp llama-bench](https://github.com/ggml-org/llama.cpp/tree/master/tools/llama-bench): backend prompt-processing and generation baselines. NodeLift's client SSE metric has a different scope.
- [vLLM serving benchmark](https://docs.vllm.ai/en/latest/cli/bench/serve/): latency, throughput and serving workload metrics.
- [NVIDIA AIPerf](https://github.com/ai-dynamo/aiperf): reference for serving load and latency tooling. NodeLift v1 does not replace concurrency or service-level goodput tests.
- [SciPy bootstrap documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html): percentile/BCa methods, reproducibility and degenerate-data cautions. V1 uses its own standard-library implementation, not SciPy or a claim of BCa coverage.
- [NIST confidence intervals](https://itl.nist.gov/div898/handbook/prc/section1/prc14.htm): intervals require explicit assumptions and do not guarantee an individual outcome.
- [MLCommons edge inference](https://mlcommons.org/benchmarks/inference-edge/): whole-system measured power reference. NodeLift is not MLPerf-certified.

Project and policy author: [Fabrizio Degni](https://www.fabriziodegni.com/). GLM 5.3 Max and Gemini 4 Argon with High reasoning provided methodology reviews; they did not independently operate the physical phones or validate the measurements.
