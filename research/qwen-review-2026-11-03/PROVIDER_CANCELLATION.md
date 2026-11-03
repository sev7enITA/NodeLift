# Cancel during connection setup before sending generation

## Provenance and reproduced effect

Qwen's provider review identified a cancellation window while the connection has not exposed its socket. Codex investigated and refined it into a concrete request-boundary defect: cancellation during connection setup could still be followed by a generation POST once the connection completed.

The original implementation checked cancellation, then called `HTTPConnection.request`. That call could perform connection setup and send the request before returning. During connection setup, `Providers.cancel` might find neither `active_socket` nor `connection.sock`; it could not shut down the transport. The next cancellation check occurred after the POST had been sent.

The regression uses a real loopback HTTP server and an HTTPConnection subclass whose connect is held behind an event. It cancels while that event is held, releases setup, waits for the server handler to finish and checks requests actually received. No cloud request or real API key is used. The original implementation sent `/v1/chat/completions` after cancellation, so the regression failed. The patched implementation sends no generation request, so it passes.

## Correction and limits

Connect explicitly, publish the established socket and recheck cancellation before the generation POST. Existing cancellation of an active transport, no-retry behavior and final cleanup remain intact. All 16 provider tests pass, including streaming, Unicode, malformed provider responses, missing completion markers, endpoint restrictions and generator cleanup.

This does not promise instantaneous cancellation of operating-system DNS or connect calls. It prevents the reproduced delayed POST after cancellation during setup. Cancellation cannot retract a request already transmitted, and a later race during an in-flight send still follows the transport's cancellation semantics. No upstream provider billing or physical-phone behavior was tested.

Read the [actual model response](provider.response.json), [failing original regression](provider-connect-before.txt) and [passing provider suite](provider-connect-after.txt). This is the Qwen-originated, independently verified finding; the JNI and telemetry fixes have separate Codex provenance.
