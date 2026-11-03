# Timing contract and correctness gates

This experiment uses token IDs, not text matching, to authorize cache reuse. The target remains authoritative. It does not shard a model or combine device RAM.

## Resource time and critical-path time

Native operations report schema 1. `native_total_ms` partitions into `native_sync_ms` and `native_after_sync_ms`. Synchronization includes prefix reuse, KV rollback/refill and the decode calls needed to establish the committed prefix. `native_decode_ms` is an overlapping diagnostic, not a third additive phase. Counts identify decode calls, evaluated tokens and synchronization tokens. These are CPU wall durations around API calls, not GPU hardware event timings, wire latency, FLOPs or energy.

Worker schema 1 reports local validation, native-call and total wall durations using one monotonic clock. Prior lookahead native work is reported separately with its parent lease. Its prefix-consumed tokens, reusable tokens and discarded tokens form a count partition. Reusable tokens are only candidates: a later target rejection is recorded separately and must not be called accepted work.

The host records enqueue, dispatch, receipt and completion on its own monotonic clock. Queue duration and dispatch-to-result duration are distinct. Subtracting self-reported worker duration leaves an unattributed remainder that includes transport, scheduling and serialization. It is not an RTT measurement. Worker and host timestamps are not synchronized.

Critical-path remote waiting is measured around the future/mailbox wait. The initial draft may overlap target prefill; later phone lookahead may overlap target verification. Resource durations therefore must not be stacked into request latency or interpreted as device contribution percentages. Native timing does not measure battery energy. Thermal and battery snapshots are contextual only.

Expired valid-identity replies are retained in a bounded host ledger, rejected by the protocol and credited with zero committed tokens. History retains at most 512 completed records for up to ten minutes, never prompt token arrays. Export the trace while available. An offline worker or failed finish exchange leaves cleanup incomplete. Failed native operations and predictions lost before a report can have unknown work: unknown is not zero.

## Bounded pipeline

The experimental Android worker computes at most one next block after the previous result is acknowledged. On prefix `P` and proposed block `D`, it predicts up to `k+1` tokens on `P+D`. The extra token predicts a possible target bonus. A new authoritative prefix must match that base plus exactly the consumed predicted tokens, and epoch/sequence/model/tokenizer must match. Otherwise the cache is discarded and the explicit new prefix is synchronized. Completed predictions expire after two seconds. This expiry is not a two-second compute deadline. The next poll waits behind native work on the worker's single inference thread, so a wrong prediction can delay a corrective request. The terminal finish request accounts for remaining predictions when reachable.

The local experiment uses one background worker and an exact-prefix check. It has no network lease expiry; it is a matched overlap candidate, not identical mobile scheduling. Both local models remain resident for all local pilot arms. Cleanup waiting is included in `request_total_ms`.

## Correctness defaults

Serial target verification is the default. Experimental batched verification requires explicit `verification_mode=experimental_batch` or API `nodelift_verification_mode`. Bounded lookahead additionally requires `pipeline=bounded_v1` or `nodelift_pipeline`, a fixed draft policy and a capable companion. Existing companions cannot silently opt in.

The native wrapper rejects embedded NUL and recognized special-token spellings inside chat message content, including system and assistant content. This preserves trusted template controls but currently rejects legitimate literal discussion of those spellings. Raw tokenization offers explicit `parse_special` and `add_special` flags. This is a tokenizer boundary, not protection against semantic prompt injection.

Allocation/serialization failures cannot escape the C ABI; null is a response-allocation failure. Cooperative load cancellation clears partially loaded state. Tests exercise recovery, default serial equivalence, actual context boundaries and stale-prefix rejection. Passing these tests is not proof that every model, GPU, quantization or batch shape is exact. Batched output divergence remains a release gate, including when the affected mode is faster.
