# Generic node probing and model benchmarks

Updated 2 November 2026. The standalone probe 0.1.1 bundles Python, its standard library and a native benchmark for the platform in each built package. The older cross-platform 0.1.0 Python zipapp remains available for users who already have Python 3.10 or later. Neither package is a Windows/Linux inference-worker installer. No model, driver installation, enrollment or automatic upload is included.

## What runs now

`host/nodelift/probe.py` collects a local, allowlisted hardware/software profile on macOS, Windows and Linux. Adapters are selected by the running OS, not a Lenovo model name. ARM64 and x86-64 are normalized separately from the native architecture reported by the OS where available. Missing observations remain null or explicitly untested.

| Platform adapter | Sources | Qualification in this revision |
| --- | --- | --- |
| macOS, including Apple silicon | sysctl and display-only system_profiler JSON | Physically executed on M3 Max; unified GPU memory is not counted twice |
| Windows, including ARM64 | CIM processor, system and video-controller fields; bounded PnP name matching for NPU candidates | Synthetic parser and unavailable-command tests; physical Windows execution pending |
| Linux, including ARM SoCs | proc CPU/memory, device-tree product name, optional lspci | Synthetic ARM/Kirin-style fixture tests; physical Linux execution pending |
| NVIDIA where available | nvidia-smi name, memory totals/free and driver version | Parser tests; no physical NVIDIA qualification in this revision |

Snapdragon or Kirin naming does not establish an NPU execution path. Windows PnP matches are candidates; Linux non-PCI accelerator enumeration can be incomplete. Driver/runtime presence, an installed Python package and successful LLM execution are distinct evidence states. Generic Windows AdapterRAM is deliberately excluded because it does not reliably establish dedicated VRAM. CPU names/product models may be present, but usernames, hostnames, serials, MAC/IP addresses, UUIDs, credentials and raw system logs are not collected into the report.

Available memory is a snapshot, not an allocation guarantee. macOS available memory, power and thermal endurance remain unknown in this version. A configuration hash fingerprints selected hardware/driver observations; it is not a stable device identity or an attestation. Model and executable hashes scope each benchmark; hashes of every dynamic dependency are not collected.

## Desktop control room

In **Devices**, choose **Probe this computer**. The authenticated local endpoint runs inventory only. Busy state, completion/error feedback, expandable results and **Export node profile** are available in English, Simplified Chinese and Italian. A mutex and 60-second cache prevent duplicate concurrent inventories; exported profiles carry their observation time and cache age.

The route accepts only an empty request. Browser requests cannot supply an executable, shell command or model path to this endpoint. The host process must load the updated source for the new endpoint to exist. Remote desktop enrollment and automatic ingestion of another computer's profile are not implemented by this change.

## Standalone package without system Python

Download the experimental [macOS Apple silicon standalone ZIP](https://github.com/sev7enITA/NodeLift/releases/download/node-probe-v0.1.1/NodeLift-node-probe-0.1.1-macos-arm64.zip) and compare its SHA-256 with the [manifest](../releases/node-probe-standalone.json). The archive contains the native executable, usage instructions and dependency licenses. On launch, the executable extracts its bundled runtime and performs a bounded startup check of the native benchmark. It does not install Python globally, download packages or upload the profile.

```sh
# macOS, after extracting the archive
./NodeLift-node --self-check
./NodeLift-node inventory --output node-profile.json
./NodeLift-node benchmark --model /path/to/model.gguf --output model-benchmark.json
```

Running it without arguments checks the bundled components and writes a uniquely named local inventory to Downloads, or the home directory if Downloads is absent. The model is user-supplied. The benchmark defaults to CPU; `--gpu-layers 999` requests offload but does not attest GPU execution. OS GPU drivers and OS system frameworks are neither bundled nor silently changed. A failed startup check is reported; inventory can still run if the benchmark is unavailable.

This specific Mac package was tested on Apple M3 Max with macOS 27.2. It is ad-hoc signed and not notarized; another Mac may refuse to launch it. [Physical validation](../research/standalone-node-2026-11-02/README.md) describes the no-system-Python sentinel test and GGUF smoke test. A workflow builds separate platform binaries on their respective OSs; successful CI does not replace physical qualification or guarantee compatibility with all GPU drivers and operating-system versions.

## Windows and Linux standalone previews

[Windows x64](https://github.com/sev7enITA/NodeLift/releases/download/node-probe-v0.1.1/NodeLift-node-probe-0.1.1-windows-x64.zip), [Windows ARM64](https://github.com/sev7enITA/NodeLift/releases/download/node-probe-v0.1.1/NodeLift-node-probe-0.1.1-windows-arm64.zip), [Linux x64](https://github.com/sev7enITA/NodeLift/releases/download/node-probe-v0.1.1/NodeLift-node-probe-0.1.1-linux-x64.zip) and [Linux ARM64](https://github.com/sev7enITA/NodeLift/releases/download/node-probe-v0.1.1/NodeLift-node-probe-0.1.1-linux-arm64.zip) include their own Python and CPU benchmark. Use the [platform manifest](../releases/node-probe-platforms.json) to verify the hashes.

```powershell
# Windows PowerShell, from the extracted folder
.\NodeLift-node.exe --self-check
.\NodeLift-node.exe inventory --output node-profile.json
.\NodeLift-node.exe benchmark --model C:\path\model.gguf --output model-benchmark.json
```

Without arguments the program checks its bundled benchmark and creates an inventory in Downloads, or in the home directory if Downloads does not exist. It does not upload reports, change drivers or install packages globally. Specify a local GGUF for an explicit benchmark. These four CI builds use the CPU backend only; they cannot benchmark an NPU or GPU. Standard operating-system libraries are still required. Linux binaries built on Ubuntu 22.04 may not run on older distributions. They are unsigned and may be blocked by the OS. Startup and inventory passed on hosted runners; no physical Windows/Linux machine, P16, Snapdragon, Kirin or accelerator has been qualified. The downloadable probe is not a desktop inference worker or the NodeLift host.

## Python zipapp alternative

Download [NodeLift node probe 0.1.0](https://www.fabriziodegni.com/NodeLift/assets/NodeLift-node-probe-0.1.0.pyz). Verify its hash against the [package manifest](../releases/node-probe.json). Python runs the same package on supported desktop OSs; a native interpreter for the machine is preferred. Physical Windows/Linux qualification is still pending.

```sh
# macOS / Linux
python3 NodeLift-node-probe-0.1.0.pyz inventory --output node-profile.json
# Windows, if the Python launcher is installed
py -3 NodeLift-node-probe-0.1.0.pyz inventory --output node-profile.json
```

From the repository, substitute `python3 scripts/probe-node.py`. Existing output files are not overwritten; choose a new filename per assessment.

## Model benchmark

Use a trusted local `llama-bench` executable built for that OS and backend, and an existing local GGUF. The module does not download or execute a backend merely because a device name suggests support.

```sh
python3 scripts/probe-node.py benchmark --executable /path/to/llama-bench --model /path/to/model.gguf --threads 4 --gpu-layers 0 --output cpu.json
python3 scripts/probe-node.py benchmark --executable /path/to/llama-bench --model /path/to/model.gguf --threads 4 --gpu-layers 999 --output offload.json
python3 scripts/probe-node.py compare --baseline cpu.json --candidate offload.json --output potential.json
```

On Windows use `py -3`, a Windows executable path and quotes around paths with spaces. `--gpu-layers 999` requests offload; it does not guarantee that a GPU or NPU was used. The JSON records reported compiled backends and requested layers, with accelerator allocation explicitly unverified.

Default workloads are 128 prefill tokens and a separate 32-token decode test, three repetitions, four threads and a 120-second process timeout. Explicit bounds apply to workload, repetitions, threads, GPU-layer requests and timeout. Raw repetition timings are retained, and the adapter checks returned workloads, sample counts, finite positive timings and execution options. Artifacts are hashed before and after execution. Timeout, failure, malformed output and artifact changes remain failure outcomes, not zero-cost successes. Partial timings are not promoted to a completed comparison.

`compare` requires the same model hash, prompt/generation workload, thread count and repetition count. It compares local kernel rates; differences in executable identity and requested offload remain visible. Comparing different thread counts is a separate tuning experiment and is rejected by this command.

## Meaning of the metrics

| Metric | This module | Further evidence required |
| --- | --- | --- |
| Prefill and decode tokens/s | Measured separately on the chosen native executable/model | Do not add them or call their ratio a distributed speedup |
| Whole subprocess wall time | Separate duration including startup/loading and benchmark work | Not isolated load time or client request latency |
| TTFT | Unmeasured here | Real client streaming on the actual route |
| Connection latency and transfer | Unmeasured here | Existing paired-device network assessment on the actual connection |
| Time saved, failure/fallback reliability, uncertainty | No positive routing recommendation | Matched [Impact sessions](IMPACT_BENCHMARK.md), including the best applicable standalone baseline |
| Energy and sustained thermals | Unmeasured | Aligned power traces and longer repeated device sessions |
| Additional target capacity | Not established | Successful resident partition execution under disclosed budgets |

The module is the inventory and native-kernel stage of qualification. It deliberately does not invent an aggregate acceleration score from RAM, advertised TOPS or hardware branding. A desktop worker still needs enrollment, task execution, cancellation and connection-specific validation before entering a cluster route. The existing Impact session schema and these probe reports are different formats; importing a probe into the Impact panel is not supported.

## Provenance and checks

[linuxhw/hw-probe](https://github.com/linuxhw/hw-probe) is credited for the useful distinction between detected hardware, drivers and tested operability. Its broad diagnostics/upload workflow is not invoked or bundled, and no source code was copied. The NodeLift adapters independently select a small set of local OS fields. See the [upstream license](https://github.com/linuxhw/hw-probe/blob/master/LICENSE.md) for that project's terms.

Model measurements invoke the separately installed MIT-licensed [llama.cpp benchmark tool](https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md). Kernel performance is not output correctness, client TTFT or proof of distributed acceleration. Retain both project acknowledgements when extending this module.

```sh
PYTHONPATH=host python3 -m unittest discover -s host/tests -p test_probe.py
python3 scripts/build-node-probe.py --output /tmp/NodeLift-probe.pyz
```

The [recorded validation](../research/node-probe-2026-11-02/README.md) separates physical Mac execution, synthetic adapter tests, browser checks and unqualified platforms.
