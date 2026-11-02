# Generic node probe validation

2 November 2026. [Module and usage](../../docs/NODE_PROBE.md) · [Portable package manifest](../../releases/node-probe.json).

## Implemented and physically executed

The portable Python zipapp collected an Apple M3 Max ARM64 profile with 64 GiB system memory. Shared GPU memory was not added to that total. The same packaged module invoked the existing local llama-bench executable twice with Qwen2.5-0.5B-Instruct Q4_K_M, three repetitions per profile, four threads, 128 prefill tokens and a separate 32-token decode test.

| Local profile | Median prefill tokens/s | Median decode tokens/s |
| --- | ---: | ---: |
| CPU request, GPU layers 0 | 1,217.82 | 178.92 |
| Offload request, GPU layers 999 | 8,235.86 | 322.51 |
| Descriptive rate ratio | 6.763x | 1.803x |

These are short, local kernel probes on one computer. They do not measure the benefit of another device. CPU ran first, then requested offload; this is not a randomized repeated session or an uncertainty estimate. Reported compiled backends were MTL and BLAS, build ddf48f8. Requested offload does not independently attest accelerator allocation. The tool rounds its model description to “qwen2 1B”; the model artifact, not that rounded label, identifies this test.

- Model SHA-256: `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`.
- Executable SHA-256: `f209beee3d305ddf361b9fc2acfd3d83766816645db78a84e163d237a8f6c353`.
- Package SHA-256: `e848fbfa0eddba618dd23b4bdbef6e3a309ceddfce3896592e5d752c781a7638`.

The benchmark retains all repetition timings and verifies the workload and returned execution options. Model and executable hashes were unchanged after each run. Hashes do not cover every linked runtime/driver dependency. Load time, first-token delay, connection transfer, output equivalence, fallback reliability, sustained thermals and energy are not established by these kernel timings. The comparison correctly keeps `qualified_recommendation=false` and `distributed_speedup=null`.

## Retained evidence

- [Mac inventory](mac-inventory.json).
- [CPU kernel record](mac-cpu.json).
- [Requested-offload kernel record](mac-offload.json).
- [Descriptive comparison](mac-kernel-comparison.json).
- [Validation record](validation.json).

The authenticated desktop inventory action, busy/completion state, expandable JSON and actual exported file were checked in a browser. English, Simplified Chinese and Italian controls were verified. The running host was restarted and its authenticated probe endpoint returned the new schema successfully.

The selected release source passed 151 host tests, including 12 probe tests and 20 protocol tests, in a clean main archive with only this change overlaid. Seven focused desktop JavaScript suites passed on the same isolated source. Documentation checks validated 107 pages and 464 local targets. The broader working copy also passed 152 host tests. These tests cover invalid timings, mismatched models/workloads, timeouts, changed artifacts, inventory privacy fields, shared memory, unavailable tools and endpoint authorization. The workspace contains pre-existing engine work outside this module's selected commit; full-suite success is not a new distributed-performance claim.

## Qualification still required

Windows and Linux adapters have fixture validation, including Windows ARM64/NPU candidates and Linux ARM/Kirin-style CPU information. No physical Windows, Linux, NVIDIA, Snapdragon or Kirin runtime was qualified in this revision. HarmonyOS/NEXT is not implied by Linux adapter availability. A suitable Python interpreter and OS APIs must exist.

Remote worker enrollment, scheduling and automatic profile ingestion are separate work. This module supplies inventory and model-specific local kernel evidence; a usable route still needs matched connection-specific end-to-end trials against the best standalone baseline. The existing Impact session collector is a separate format and does not import these profiles directly.

## Related work

Thanks to [linuxhw/hw-probe](https://github.com/linuxhw/hw-probe) for the hardware/driver/operability diagnostic approach, and to [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md) for the native benchmark tool. No hw-probe source was copied, bundled or executed; no inventory upload was performed.
