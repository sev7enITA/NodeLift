# Resident models and bounded task segments: pilot plan

2 November 2026. Written before the first run. This is a local feasibility and quality probe, not a distributed performance benchmark or a shipped companion feature.

## Question

Can a resident small model execute a complete, independent extraction task from its relevant source segment, with less input processing than giving it the entire collection? Test correctness as well as latency. Do not equate a small model's output with the target model's verified tokens.

The existing mobile draft already keeps weights resident. This proposal changes the unit of delegated work from a short speculative token block to a complete task. It does not pool memory or split a large model.

## Fixed local experiment

- Models: the existing Qwen2.5 0.5B and 1.5B Instruct Q4_K_M artifacts, identified by SHA-256.
- Six synthetic English maintenance records, each with a manually specified answer. Include missing information, superseded values and distracting records.
- Four cells: each model with the full collection and with only the relevant record. The requested output contract is identical in all cells.
- Two repetitions per record/cell: 48 planned attempts. These repetitions measure short-run variation, not independent quality samples.
- Both model handles stay loaded. Reset KV for every task to isolate segmentation from prefix caching. Record load time separately.
- One excluded warmup per model/context cell. Fixed pseudorandom seed 20261102; randomized cell order within each record/repetition and shuffled record/repetition blocks.
- Greedy output, EOS respected, maximum 96 tokens, 2,048-token context, eight requested threads and 999 requested GPU layers. Requested GPU offload is not independently attested hardware allocation.
- Use the existing native library through its Python ABI. Generate the first token separately to time it, then the remainder. Do not modify the running dashboard or its engine configuration.
- Store all attempted rows, errors, raw output, token hashes, finish reason, prefill, first-token time, full task wall time, and exact serialized UTF-8 request payload bytes.
- Strict JSON scoring: exactly four string-or-null fields and exact fixture values. No substring acceptance or repair of malformed output. This is an offline answer key, not a production semantic verifier.
- Compare segmented/full times within the same model and record. Show incorrect/failed attempts; any success-only summary must expose its denominator. Do not present 0.5B/1.5B latency ratios as equivalent-model acceleration.

No wire traffic, transport latency, phone compute, thermal stability, energy, task parallelism, fallback, or aggregation speed is measured here. Payload bytes exclude HTTP/TLS and are not measured network bytes. Both models are resident on the same Mac, so this is not the strongest single-model deployment baseline. No broad quality or uncertainty claim follows from six fixtures.

## Physical follow-up gate

The current companions accept only `draft` work with 1 to 16 tokens, full-prefix identity and a matching draft model. They do not yet implement a whole-task protocol. Both known phones were offline at preflight. Do not bypass these facts by presenting a local probe as a phone experiment.

Next implement and qualify an explicit `task_v1` capability with a bounded prompt, model identity, session epoch, task/attempt ID, input hash, output contract, deadline, cancellation and duplicate/stale result rejection. Reuse authenticated pinned TLS and outbound workers. Keep the existing draft verifier independent.

For each physical device/model/link, alternate: optimized Mac-only workflow, same workflow with one resident remote worker, and the strongest applicable Mac-local batching/parallel-task baseline. Where smaller models are used, run those same models on the Mac too. Count planning, queueing, transfer, computation, validation, reduction, retries, fallback and discarded work in final completion time. Measure TTFT to usable user-visible output separately from the first intermediate worker token. Track quality on held-out tasks, complete/failure denominators, cold versus resident state, sustained load and measured energy only where instrumentation exists.

Predetermine a useful improvement threshold after this pilot and before confirmatory trials. A worker is useful only if the complete workflow improves at the required quality, or if it provides a separately reported capacity or throughput benefit.
