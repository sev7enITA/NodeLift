# Local Qwen source review

**Completed: 17 actual local model responses through NodeLift. One Qwen-originated cancellation issue was independently reproduced and corrected. Two other boundary fixes were found independently by Codex.** This was a scoped static review, not a full application audit or a phone performance test.

The requested [HauhauCS Qwen3.8 27B GGUF](https://huggingface.co/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF) ran on the Mac through NodeLift's authenticated `local_api` engine route. The full downloaded file passed its pinned SHA-256 check. No replacement model or cloud inference was used.

## Verified changes

| Change | Provenance | Independent evidence | Delivery scope |
|---|---|---|---|
| Check cancellation after connection setup and before a generation POST | Qwen identified the unavailable-socket window; Codex reproduced the delayed POST and refined the fix | Real loopback regression fails before and passes after; 16 provider tests pass | Host source updated and running |
| Convert Java UTF-16 to standard UTF-8 at the JSON boundary | Codex, before any Qwen response; Qwen later reviewed the disclosed fix | 15 real JVM/JNI cases; Android ARM64 object compilation | Android JNI source only; published build 16 unchanged |
| Reject a null required worker total as missing telemetry | Codex during adjudication; not raised by Qwen | Mailbox regression fails before and passes after; valid tokens remain accepted | Host source updated and running |

Read [provider cancellation](PROVIDER_CANCELLATION.md), [JNI Unicode](JNI_UNICODE.md) and [null telemetry](TELEMETRY_NULL.md). The final host suite passes **167 tests**. Eight additional real-weight native correctness checks reject the model's context-overflow and accepted-count hypotheses. These checks are not performance measurements. See [validation](validation.json), [host results](host-tests-final.txt) and [native counterchecks](native-findings-check.json).

## Reviewer results and limitations

Ten initial packets asked for a blind review of bounded source excerpts. An eleventh packet disclosed the already reproduced JNI issue and candidate patch. Four initial answers reached the 512-token limit: `native-state`, `transport`, `impact-estimator` and `impact-attribution`. Their original truncated responses are retained. Six shorter informed follow-ups completed without truncation: four supplied missing context or metric contracts, and two reviewed known telemetry/provider fixes. Follow-ups are not independent discoveries.

| Area | Adjudicated result |
|---|---|
| Native context and accepted tokens | Context arithmetic and eight real-weight checks reject the claims. Qwen retracts overflow, but still incorrectly treats a target bonus as an accepted draft token. |
| JNI lifetime and native handles | Original string release is unconditional; retained shared ownership protects in-flight calls. Proposed leaks/use-after-free are rejected. |
| Controller and leases | Cancellation is cooperatively checked; finish intentionally carries the committed prefix. A generic active-entry cap would matter if caller concurrency expands, but the proposed 513-node case bypasses the current single-run contract. |
| TLS and model transfer | Qwen withdraws the slot-leak suspicion and, after context, the path-traversal suspicion. The node route cannot select an arbitrary filesystem path. |
| Android lifecycle | No persistent resource leak was demonstrated. Rapid pause/restart status and cleanup latency remain a targeted instrumentation/physical-device follow-up. |
| Android download and cancellation | Failed partial downloads are intentionally removed. Opaque native handle IDs make cancel after close a no-op; the alleged pointer race is rejected. |
| Impact estimation | Ordered energy samples, whole-session bootstrap, positive duration validation and the candidate-minus-host TTFT convention match their contracts. Qwen retracts the relevant suspicions in follow-ups. |
| Provider | Generator cleanup is already guarded. The pre-connect cancellation window yields the reproduced, corrected delayed-POST defect. |
| Known fixes | Qwen reports no supported regression in the supplied JNI, telemetry and provider patches. This is static feedback, not execution evidence. |

Every visible claim has an entry in [adjudication.json](adjudication.json). Raw opinions, including incorrect claims and explanatory imprecision, are preserved. The collector's `human_adjudication: pending` fields describe capture-time state; the subsequent adjudication is by **Codex**, not a human auditor. The model has no execution tools in this experiment. Statements about test results in its follow-up answers merely refer to evidence supplied in the prompt.

This pass does **not** establish superiority over GLM/Gemini or a causal effect of the publisher's “uncensored” label. Input coverage, model size, quantization and non-thinking output limits differ from the [earlier review](../async-pipeline-2026-11-03/REVIEW.md). The earlier core packets did not include JNI. A fair model comparison needs the same complete dependency context, settings and independently labelled defects. The practical lesson is to require a concrete reproduction and preserve rejected findings before accepting model-authored patches.

## Frozen model and runtime

- Hub revision: `993a5971fda8f30dd1b7eb2654792ba4415c7460`.
- File: `Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q4_K_P.gguf`.
- Size: 17,923,393,664 bytes.
- SHA-256: `ba36dc3c2b2ff5e0aa5d71092a8894546996a6a119ae391803dda07cdc08516d`.
- Actual GGUF architecture: `qwen35`, 65 blocks including the embedded prediction head; native context metadata 262,144.
- Review context: 16,384 tokens, one slot, Metal offload, temperature zero, non-thinking mode, maximum 512 output tokens per call.
- llama.cpp source: `ddf48f85c933c1f438212a02eb21e7b001d2d37d`; 1,819 source files compared with the pinned tree. This source-identity check is not a review of all those files.
- The initial ten source packets cover 14 NodeLift files or excerpts. Native core files shared with the community fork are recorded in [fork-scope.json](fork-scope.json).
- Embedded MTP and the associated FastMTP patch are disabled. [FastMTP inspection](fastmtp-inspection.json) is a Codex static assessment only, with no imported patch or benchmark.
- The native NodeLift verifier still rejects hybrid/recurrent models pending checkpoint/rollback qualification. This model ran through the separate local provider route; importing a GGUF does not change native compatibility.

The model remains in the local cache and library. The temporary review server has stopped and the prior provider endpoint was restored. Future use requires starting a compatible local server and selecting it in NodeLift. Target/draft configuration and phone pairing were preserved.

## Evidence and reproduction

Read [the verified download identity](download-verified.json), [runtime libraries](backend-libraries.json), [first-pass run identity](run-manifest.json), [first-pass packets](packets.json), [first-pass completion](completion.json), [follow-up inputs](followup/packets.json) and [follow-up completion](followup/completion.json). Each `*.prompt.txt` has a manifest hash; its matching `*.response.json` retains actual NodeLift run ID, answer, finish reason, usage and timings. These timings characterize this review execution, not an isolated inference benchmark.

The exact collector used for both passes is preserved in `collector-executed.py`. The maintained runner adds an output-directory guard to avoid replacing retained evidence. With the pinned model available through `.models/`, a compatible server binary and an idle NodeLift host:

```sh
python3 research/qwen-review-2026-11-03/run_review.py \
  --server /absolute/path/to/qualified/llama-server \
  --output-directory artifacts/qwen-review-rerun
```

Use the retained frozen prompts for reproduction. `prepare_packets.py` creates a different source snapshot from the current checkout; it must not overwrite the historical review inputs. The runner registers the model, refreshes NodeLift's provider catalog, invokes its real engine API, then restores the prior endpoint and stops its own server. It does not execute model suggestions or publish anything. Do not overlap model review with performance measurements.

## Acknowledgements

Thanks to [HauhauCS](https://huggingface.co/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF) for the published quantization and optimization material, and to the [llama.cpp contributors](https://github.com/ggml-org/llama.cpp) for the inference runtime. The Hub identifies the model license as Apache 2.0; weights are not included in NodeLift's MIT-licensed repository. Earlier work, including DistAI, remains linked in [Acknowledgements](../../docs/ACKNOWLEDGEMENTS.md). No endorsement, certification, pooled RAM or distributed acceleration is implied.
