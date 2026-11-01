# Model library functional audit

Date: 2026-11-01. Host dashboard source fix; published mobile packages remain 0.2.8. This audit does not certify every function of NodeLift.

## Defect reproduced and repaired

A live search for `Qwen2.5-0.5B-GGUF` returned valid Hugging Face repositories from the backend, but the browser raised `Cannot read properties of undefined (reading 'message')`. The generic result button had reused the device-action factory. With no node ID or action kind, `pending?.kind === kind` compared two undefined values and selected `pending.message`.

Model buttons now have their own action handler and request groups. Device pending-state checks require an actual pending object. Error rendering accepts unknown errors safely. Search and inspection show progress, empty results and retry feedback in English, Simplified Chinese and Italian. Polling cannot re-enable an operation still in progress. Failed inspection clears the previous file selection. Download and upload controls reflect active transfers. Cancelling an upload aborts its active request and stops subsequent chunks. Small file sizes use MiB instead of rounding to 0.0 GiB.

## Function-by-function evidence

| Function | Evidence and result | Scope or limitation |
|---|---|---|
| Hugging Face search | Live API returned 12 repositories for the Qwen query; repaired production dashboard displayed clickable results | Public GGUF repositories only |
| Repository inspection | Actual browser showed Qwen files, sizes, Apache-2.0 license and immutable revision | Gated/private access is not implemented |
| File selection and download | Test dashboard downloaded a real 18,901,824-byte GGUF and showed Completed | Separate temporary state; no user model was replaced |
| Integrity and publication | Download SHA-256 matched pinned Hugging Face metadata; only verified final files were registered | Header acceptance does not qualify runtime compatibility |
| Cancel download | Real Hugging Face transfer cancelled and owned partial files removed | Cancellation can wait for the bounded in-flight network operation |
| Import existing path | Browser form imported the real GGUF; its entry appeared in the target/draft catalog. Missing paths rejected through HTTP | No copy for path imports |
| Browser upload handler | Real GGUF uploaded through HTTP in 1 MiB chunks, byte/hash checked; wrong offsets rejected. Actual JS handler exercised with synthetic files | Native file-picker UI could not be automated by the available app-control surface; not claimed as a full browser upload test |
| Cancel upload | Real partial HTTP upload cancelled and removed; JS test aborted an in-flight chunk and prevented finish/next chunks | Browser handler test is synthetic |
| Provider settings and clear key | Actual loopback HTTP configure/catalog/clear operations passed against an explicit local provider fixture; secret excluded from status | Not a test of installed LM Studio, Ollama or oMLX |
| OpenRouter catalog | Public live catalog returned 433 text-output models, without a key | No paid cloud generation performed |
| Native model loading and generation | Existing Qwen2.5-0.5B-Instruct Q4_K_M completed a 16-token native run through host HTTP | CPU configuration, public fixed prompt; functional check, not speed qualification |
| Unsupported chat model | Downloaded stories15M base GGUF imported, then runtime rejected generation with `model has no chat template` | GGUF is a container, not a guarantee of chat-template or architecture compatibility |
| Session loss, empty/error results, duplicate requests | Combined real production JS scripts passed asynchronous synthetic UI regression tests | These tests supplement the live browser checks |

The first base-model audit harness exited abnormally during native teardown after reporting the missing chat template. The harness now explicitly closes native contexts. Repeating that negative case exited normally with the expected failed-model assertion, and the positive Qwen audit exited successfully. This is not a claim that arbitrary GGUF files are safe or supported.

## Automated checks and reproduction

- `node scripts/check-model-library.cjs`: combined dashboard/library handlers, including the exact generic-button regression, search/inspect/download, import/upload/cancel, provider access and session loss. Added to Source checks CI.
- `node scripts/check-control-states.cjs`: existing device, pairing, engine and session controls remain passing.
- 19 model API/library tests and 15 provider tests passed.
- `PYTHONPATH=host python3 scripts/check-model-library-live.py --model /absolute/path/to/test.gguf --inference-model /absolute/path/to/chat-model.gguf --report /tmp/model-audit.json --public-catalog`: temporary state, real HTTP upload and native inference; fixed public prompt; optional live public OpenRouter catalog. A local provider fixture is explicitly synthetic.

Receipts: [real HTTP and Qwen inference](http-native-audit.json), [Hugging Face download](huggingface-live-receipt.json), [download cancellation](hf-cancel-check.json).

Source model: [mradermacher/llama2.c-stories15M-GGUF](https://huggingface.co/mradermacher/llama2.c-stories15M-GGUF), revision `7f13cd6df2c1e9c3ddf84d7ac09753d458a3b750`. No model weights, private credentials or user-state databases are committed. No new external-model review is claimed.
