# Missing total duration must not be labelled valid

Codex found and reproduced this issue while checking the Qwen lease findings. Qwen did not identify it in its `leases` response.

`worker_timing` required the `worker_total_ms` key, but skipped all duration values equal to `None`. Consequently, `{"schema_version":1,"worker_total_ms":null}` produced a nonempty validated record without any duration. `Mailbox.submit` then labelled that record `valid_self_report`.

The correction requires a numeric total before validating finiteness, range and nested durations. A missing/null total is now `missing_or_invalid`. This does not reject otherwise valid draft tokens, authorize any token, manufacture a zero duration or change model output. It corrects the measurement evidence label.

The added mailbox regression fails on the original implementation and passes after the change. All eight timing/lookahead tests pass. See [before](telemetry-before.txt), [after](telemetry-after.txt) and [the exact original observation](telemetry-observation.json). These are host unit tests, not measurements from a physical phone. No new mobile package is required for this host correction.
