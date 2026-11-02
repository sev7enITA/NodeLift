# Run a useful comparison

Measure **single-response latency**, **capacity** and **aggregate throughput** separately. More total RAM does not prove shared target memory; more concurrent requests do not prove one response is faster.

Before a physical-phone run, confirm the current companion is online and its draft engine is ready. Use the same target/model revisions, quantization, prompt set, sampling rules and output limits across host-only, local-draft and remote-draft runs. Preserve actual token counts, load/warmup boundaries, output comparisons, rejected work, fallback and failed trials.

```sh
python3 scripts/benchmark-connected.py   --topology "Phone hotspot to Mac over Wi-Fi"   --tokens 128 --repetitions 3
```

Use an accurate topology label; the example above is not a universal recommendation. The runner refuses offline or unready nodes and writes a fresh `artifacts/connected-benchmark` directory. Inspect outputs before publishing. Do not upload invitations, client keys, private prompts or the private state database.

Record device/OS, NodeLift revision, native pin, battery, thermal status, foreground/background state, network topology and elapsed session duration. Compare Wi-Fi/hotspot with USB/Ethernet only after measuring those actual connections. Repeat in randomized order and report variation and negative outcomes.

The initial small-pair trials found local drafting slower than the same host-only path. The phone’s existing hotspot measurements cover application HTTPS and synthetic CPU, not native mobile LLM inference. A CI correctness pass establishes neither physical-phone acceleration nor thermal endurance.

[Benchmark protocol](https://github.com/sev7enITA/NodeLift/blob/main/BENCHMARK_PROTOCOL.md) · [Published results](https://github.com/sev7enITA/NodeLift/blob/main/research/measurements/ENGINE_RESULTS.md) · [Contribution requirements](https://github.com/sev7enITA/NodeLift/blob/main/CONTRIBUTING.md)

## Visual comparisons

[Open the localized benchmark gallery](https://www.fabriziodegni.com/NodeLift/#benchmark-charts) or [read the reproducible visual report](https://github.com/sev7enITA/NodeLift/blob/main/research/visual-benchmarks-2026-11-02/README.md). Four chart families show paired total duration, first-token delay, fallback-inclusive adaptive timing and proposal acceptance with incomplete requests retained. Individual observations and sample sizes accompany medians; no confidence interval or energy result is inferred.

![Measured fixed-delegation duration ratios](https://raw.githubusercontent.com/sev7enITA/NodeLift/main/site/NodeLift/assets/benchmarks-2026-11-02/01-total-time.en.png)
