# External review ledger and adjudication

Status: this cycle is a static research review, never external execution of NodeLift.

| Reviewer | Material | Actual outcome | Use |
|---|---|---|---|
| NVIDIA Nemotron 3 Ultra 550B A55B, free endpoint, medium effort | `reviewer-prompt.txt`, then explicit correction request | Two complete responses retained | General measurement questions retained; unsupported mechanisms rejected |
| Cohere North Mini Code, free endpoint | Same five-case brief plus instruction against invented claims | Complete response retained | Cost-accounting question retained; most specific proposed diagnoses rejected |
| Gemma 4 31B IT, free endpoint | Original brief, later a second request with new local results | Both requests returned HTTP 429, no assessment received | None |
| Gemini 4 Argon High | Browser session requested | Current-cycle submission not completed because the browser was being used concurrently | Previous-cycle review is not relabeled as this review |
| GLM 5.3 Max | Browser session requested | Current-cycle submission pending browser availability | Previous-cycle review is not relabeled as this review |
| Kimi | Browser session requested | Current-cycle submission pending browser availability | None |

OpenRouter reported zero available credits. Only catalog-confirmed free endpoints were called. Availability and response quality, rather than the number of agreeing models, limit the evidence. Raw responses deliberately remain uncorrected as audit evidence. They are not instructions or citations to adopt.

## Claims rejected or corrected

- Nemotron supplied hardware cache sizes, a processor parking threshold, memory-copy timings and a fixed divergence horizon without evidence. These are not measured facts. No operating-system tuning command was run.
- Sharing a draft and target KV cache is not valid merely because tokenizers match. Different model parameters, layer counts and hidden states require an explicit compatible-state contract.
- Drafting on a CPU and observing a slowdown would not isolate memory bandwidth as the cause: the device, kernels, transfer path and contention also change.
- Raising sampling temperature changes the output contract and cannot qualify greedy equivalence. An empirical KV or logit tolerance is not proof of exact sampling or output equivalence.
- Cohere described an isolated-host and placement-speed claim that the supplied brief explicitly did not make. The 1.307x historical result failed equivalence and was never promoted.
- Cohere's named papers by Kudo/Sagawa, Liu, Zhou/Sun and Kumar were not independently verified. They are excluded from the source bibliography. Dettmers' quantization work does not establish this run's root cause.
- Clearing cache without rebuilding the full committed prefix is an invalid ablation. Our history/current-width experiment rebuilds the same token history with fresh caches and compares only populated KV entries.
- `time.perf_counter` measures elapsed wall time, not host CPU time. Synchronized phase measurements include scheduling and kernel execution; their labels do not claim pure GPU kernel duration.
- A teacher-forced replay with free candidates is intentionally optimistic. It does not measure live draft acceptance, does not establish a deployable lower bound, and is not invalidated merely because real candidates cost time.
- Comparing draft and target logits at an arbitrary epsilon does not localize target serial/batch divergence. The models are supposed to differ. Our comparison holds the target and token prefix fixed.
- Temperature thresholds or frequency-drop limits proposed without sensor evidence are not adopted. OS thermal pressure is recorded separately from unknown device temperature and unmeasured energy.
- A Python `finally` block does not inherently swallow exceptions. Bounded child-process logs and completion status retain failures even before a per-request row can be written.

## Useful questions retained

1. Does startup amortization change controller decisions, while complete request timing remains the final outcome?
2. Does a fixed prefix diverge with only current batch width changed, only cache construction history changed, or both?
3. How much candidate production, network delay and rollback could the measured verifier path tolerate under explicit idealized assumptions?
4. Would a controlled idle/power experiment reproduce diagnostic results? This is still required for qualification.

These questions were already present in the frozen protocol. Their repetition by reviewers is not independent experimental confirmation.
