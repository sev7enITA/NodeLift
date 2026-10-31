<img src="assets/brand/nodelift-mark.svg" width="88" alt="NodeLift symbol">

# NodeLift

**Give the hardware you already own another useful role in local AI.**

NodeLift is an experimental local inference workbench and mobile companion system. A small model on a phone proposes tokens; a larger model on the computer verifies them before anything reaches the user. The project measures when delegation helps and when the computer alone is faster.

**0.2.1 experimental, 31 October 2026.** Native inference, authenticated mobile work leases, an OpenAI-style text gateway, Android/iOS companion sources and an LM Studio generator adapter are implemented. **Phone inference speedup, pooled RAM, large hybrid-model speculation and sustained mobile operation are not yet qualified.** The first real-weight control experiments found local drafting slower than target-only inference on the small test pair. Negative results are published.

## Implementation and evidence

| Component | Implemented | Observed evidence / limit |
|---|---|---|
| Native core | Locked llama.cpp, greedy block verification, correction/bonus, EOS, KV resynchronization | Real-weight M3 Max/Metal tests; no universal bitwise-equivalence claim |
| Remote work | Pinned TLS, lease, epoch, prefix/vocabulary/model identities | Real-weight loopback tests including wrong proposals and lost replies; emulated node |
| Android | ARM64 CPU draft worker, checked LAN model transfer, battery/thermal controls | APK built; physical Xiaomi measurements used the earlier 0.1 qualification app |
| iOS | Native Metal/CPU worker, GGUF import, foreground lifecycle, user limits | Unsigned device build compiled; physical iPhone inference remains open |
| HarmonyOS NEXT | Separate ArkTS qualification candidate | No HAP or native inference worker |
| Desktop | Control room, pairing, telemetry, diagnostics, model settings, run history | Browser functional checks and Gemini design review; post-fix visual recheck limited |
| Integration | Authenticated text chat gateway and LM Studio generator | Real-weight HTTP/adapter-handler tests; LM Studio GUI qualification open |

This is **not an Ollama backend patch**. Clients with a custom OpenAI-style endpoint can call NodeLift within its text/greedy subset. The LM Studio adapter selects NodeLift as a generator; it does not split LM Studio's own loaded model across phones.

## Start on the host

Requirements: Python 3.12+, C++17 compiler, CMake 3.22+, Git and locally licensed GGUF weights. The verified native host build is Apple Silicon macOS/Metal. Other host platforms/backends are not qualified.

```sh
git clone https://github.com/sev7enITA/NodeLift.git
cd NodeLift
./scripts/build-native.sh
python3 scripts/fetch-control-models.py
PYTHONPATH=host python3 -m nodelift.host --address YOUR_PRIVATE_LAN_IPV4
```

The optional control-model download is approximately 1.61 GB, with fixed [revisions and hashes](profiles/control-models.json). Open the **private dashboard link printed by the host**, select target/draft, apply the configuration and begin with Host only. Keep invitations and client keys private.

- [Engine and companion guide](docs/ENGINE_0_2.md)
- [API and LM Studio integration](docs/INTEGRATIONS.md)
- [Build and verification status](artifacts/README.md)
- [Measured results](research/measurements/ENGINE_RESULTS.md)
- [Architecture and remaining work](docs/ARCHITECTURE.md)

## Evidence before acceleration claims

The primary objective is lower single-chat latency than the best applicable local baseline at the same target, sampling rules and actual output length. Capacity expansion and multi-user throughput are separate experiments. Reported physical RAM is not memory already shared with the host.

- [DistAI source study and lessons](research/distai/LESSONS_LEARNED.md)
- [October 2026 research update](research/RESEARCH_2026_10_31.md)
- [Gemini 4 High / GLM 5.3 Max reviews, adjudicated](research/reviews/ENGINE_REVIEW.md)
- [Physical Xiaomi hotspot measurements](research/measurements/2026-10-31-xiaomi-hotspot/REPORT.md)
- [Benchmark protocol](BENCHMARK_PROTOCOL.md), [initial assessment](ASSESSMENT.md), [device inventory](profiles/devices.json)

## Reproduce checks

```sh
PYTHONPATH=host python3 -m unittest discover -s host/tests -v
python3 scripts/check-native.py
python3 scripts/check-remote-loopback.py
python3 scripts/benchmark-engine.py
cd adapters/lmstudio && npm ci --ignore-scripts && npm test
```

Native tests require the built library and weights. Network/CPU qualification tests are not LLM benchmarks. The upstream comparison script additionally requires llama-server built from the pinned checkout. Weights, pairing databases, private prompts and signing secrets do not belong in Git.

Contributions are welcome: reproducible device measurements, backend bring-up, failure tests and improvements against an appropriate local comparator. See [CONTRIBUTING](CONTRIBUTING.md), [license](LICENSE), [third-party notices](THIRD_PARTY_NOTICES.md) and [brand provenance](docs/BRAND.md).
