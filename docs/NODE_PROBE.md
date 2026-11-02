# Generic node probing and model benchmarks

Source preview 0.1.0, 2 November 2026. This is an implemented reusable Python module and command-line package, not a Windows/Linux inference worker installer. It needs Python 3.10 or later. No GPU runtime, model, privilege escalation, enrollment or automatic upload is bundled.

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

## Portable package

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
