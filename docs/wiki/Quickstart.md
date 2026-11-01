# First local run

Start with the computer alone. The tested host is Apple Silicon macOS; another OS or backend needs separate qualification. Install Python 3.12+, Git, CMake 3.22+, a C++17 toolchain and OpenSSL. The build command fetches the locked llama.cpp revision and compiles it locally.

```sh
git clone https://github.com/sev7enITA/NodeLift.git
cd NodeLift
python3 scripts/doctor.py
./scripts/build-native.sh
python3 scripts/fetch-control-models.py
```

The last command downloads about 1.61 GB of public control weights. Read [the pinned model inventory](https://github.com/sev7enITA/NodeLift/blob/main/profiles/control-models.json) and the models’ licenses first. It is optional if you already have suitable complete GGUF files.

1. Find the computer’s private LAN IPv4 address on the network shared with the phone. An address such as `192.168.1.20` below is only an example; substitute your actual address.
2. Start the host:

```sh
PYTHONPATH=host python3 -m nodelift.host --address 192.168.1.20
```

3. Open the **private dashboard link printed by the host**. The plain `http://127.0.0.1:9868` address loads the page but does not grant control access.
4. In **Models**, import a complete GGUF or register an existing absolute file path. For the control pair use Qwen2.5 1.5B as target and 0.5B as draft.
5. Select the target/draft in **LLM engine**, apply configuration, choose **Computer only · baseline**, enter a public test prompt and run 32–64 output tokens.
6. Only after this succeeds, follow the [Android](https://github.com/sev7enITA/NodeLift/wiki/Android) or [iOS](https://github.com/sev7enITA/NodeLift/wiki/iOS-and-iPadOS) guide.

Choose **Language → English / 简体中文 / Italiano**. The choice is saved locally. There is no required cloud account. OpenRouter is an optional, explicitly selected cloud backend with possible charges.

Expected result: actual generated text and a completed run with timings. Compilation, a green node indicator or RAM telemetry alone is not proof of accelerated inference.
