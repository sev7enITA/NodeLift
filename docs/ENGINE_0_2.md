# NodeLift laboratory guide (companion 0.2.11)

The native engine was introduced in 0.2.1. The current companion is **0.2.11 / build 13**, with desktop QR pairing, local diagnostic export, automatic update discovery, default English, Simplified Chinese and Italian. **No inference speedup on a physical phone has been demonstrated.** See the [changelog](../CHANGELOG.md) and [installation requirements](MOBILE_DOWNLOADS.md).

## Computer

1. Build with `scripts/build-native.sh`; llama.cpp must match `native/llama.lock`.
2. Download the control pair with `python3 scripts/fetch-control-models.py`, or place compatible GGUF files in `.models`. The dashboard also reads the LM Studio catalog.
3. Start the host on its private IPv4 address: companion HTTPS on port 9867; dashboard/client API on loopback port 9868.
4. Open the private link printed at startup. An unauthenticated address displays the page but does not authorize commands.
5. Select target/draft, context, threads and GPU settings, then choose Apply. Unapplied changes block a run.
6. Start with Host only. Weights remain resident; loading is timed separately. Stop the host process to release them.

Configuration stays in the private state directory. The dashboard token rotates on restart; the client API key is separate and persistent. Update and restart the host to use QR pairing.

## Main model, draft and execution backend

Main model lists local GGUF files discovered in NodeLift's `.models` directory, the user's `.lmstudio/models` directory and registered Model library imports/downloads. Entries are deduplicated by resolved path, not content hash. Two copies of the same weights can appear separately. This is an inventory, not a hardware recommendation, compatibility certification or a list of every Hugging Face model. Architecture support is checked when the native runtime loads the file.

The main model generates and verifies output. A draft is an optional smaller model that proposes token blocks, used only by Local proposals or Phone proposals. The target and draft must share token-ID semantics. Computer only and Context reuse require no draft. The Qwen2.5 1.5B/0.5B pair is a control fixture, not a best-model recommendation.

Execution backend selects where inference runs. Native uses the applied local GGUF configuration. OpenRouter and Local API use Provider model from that backend's own catalog; native configuration is disabled for those routes. Select **Load backend models** next to the execution selector to load the chosen backend's catalog. **Configure selected backend** opens the matching access panel and focuses its key or URL. Catalog errors are displayed beside the selector. OpenRouter public catalog retrieval requires no key and does not generate text, but cloud generation requires session access and may incur charges.

For Local API, the server must already be running. Set its actual loopback URL, such as `http://127.0.0.1:1234/v1` for the common LM Studio configuration, save session access and load its models. A different port is not automatically discovered. Provider keys, URL configuration and catalogs are held in memory for this host session and must be set again after a restart. Connecting this route does not add NodeLift phone drafting to LM Studio.

## Android ARM64

Version 0.2.11 retains the existing laboratory debug signing identity. Updating an installation requires the same signing key. Install over the existing app to preserve saved pairings; do not uninstall first. This is a laboratory build, not a Play Store release.

1. Install the updated APK and open NodeLift. For an existing pairing, choose Resume session. For a new pairing, choose **Add device** on the desktop and **Scan QR** on the phone, then confirm the computer address and fingerprint. See [QR pairing](QR_PAIRING.md).
2. On the Mac, select `qwen2.5-1.5b-instruct-q4_k_m.gguf` as target and `qwen2.5-0.5b-instruct-q4_k_m.gguf` as draft; apply the configuration.
3. On the phone, choose Download draft from Mac and enable it: approximately 491 MB over the local network. SHA-256 is verified before loading.
4. Wait for Draft ready and an online node with native-engine availability in the dashboard.
5. Select Remote draft and the node. Start with 32–64 tokens and block size 4; compare Host only / Local draft on the same prompts. The remote deadline is adjustable from 0.5 to 60 seconds (default 30); exceeding it falls back to the Mac.

The worker uses ARM64 CPU, not NPU/Vulkan. Limits: files up to 1 GiB, context 512–4096, 1–8 threads. The battery threshold is configurable; moderate or higher thermal status interrupts native work. Thread/context changes apply on the next load. A foreground service does not establish freedom from OEM limits or reliable screen-off operation.

The phone receives tokenized context and must be trusted; it is not a public node. Revocation prevents new authenticated results. Host cancellation invalidates the lease, but the phone may finish its current small block: a separate immediate remote-cancellation channel is not implemented.

## iPhone / iPad

`scripts/build-ios.sh` requires Xcode/XcodeGen and produces an unsigned device build. The published IPA and app ZIP require valid Apple signing and provisioning before installation; they cannot be installed directly from Safari. No App Store/TestFlight package has been produced.

After signing and installation, use **Scan QR** to scan the desktop invitation and confirm its address/fingerprint. Camera scanning on physical Android/iOS devices remains to be qualified; compilation and desktop QR decoding are separate evidence.

Import the same host-selected draft GGUF through Files, up to 1 GiB. It is copied into private storage, verified and excluded from backups. Choose Metal/CPU and limits, enable the engine and resume the session. Keep the app in the foreground; backgrounding pauses it. Compilation does not qualify Metal or the memory budget on a physical iPhone.

## Limits

- Text and pure greedy decoding only: no tools, images, structured output, penalties or stochastic sampling.
- One active run, at most 512 generated tokens; no multi-user batching.
- Target and draft must use identical meanings for token IDs.
- Recurrent/hybrid models are rejected pending checkpoint restoration and qualification. The large GGUFs already available in the laboratory are Qwen35/Qwen35MoE.
- Remote drafting does not pool phone RAM to host a larger target. Capacity sharding/offload remains open.
- HarmonyOS NEXT requires a separate native companion; the Android APK does not qualify it.

## Connected-phone benchmark

The runner rejects offline nodes and nodes without a ready engine. It uses public prompts, compares host/local/remote in randomized order, and retains failures, fallback, actual tokens and before/after telemetry. Credentials stay local.

```sh
python3 scripts/benchmark-connected.py --topology "Xiaomi hotspot → Mac, Wi-Fi" --tokens 128 --repetitions 3
```

The default output directory is `artifacts/connected-benchmark` and must be new. The offline gate was tested; the complete runner remains to be exercised on the updated phone. Context must fit the prompt, output and proposal block. Comparing cable/adapters or a dedicated access point requires new physical tests of that topology, not an estimate from the Wi-Fi version.
