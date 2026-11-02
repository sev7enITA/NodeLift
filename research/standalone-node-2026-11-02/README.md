# Self-contained node probe: physical validation

2 November 2026. The [standalone package manifest](../../releases/node-probe-standalone.json) records the archive, executable, upstream benchmark, source and hash identities.

On the physical M3 Max with macOS 27.2, the frozen single-file executable reports embedded Python and successfully starts the bundled native `llama-bench`. The executable was run with `/tmp/nodelift-fake-python-bin` ahead of `/usr/bin` and `/bin` in PATH. Both `python` and `python3` there were sentinel programs that would write a marker and fail. No marker was created. This verifies that these runs did not invoke a system Python command; it does not qualify every macOS version.

- [Local inventory](mac-inventory.json) completed with the packaged executable.
- [GGUF benchmark smoke test](mac-gguf-smoke.json) completed using a local Qwen2.5-0.5B Q4_K_M artifact, CPU request, 16 prompt tokens, 8 generated tokens and one repetition. This is a functional test, not a performance study.
- The published ZIP was extracted with the macOS archive utility and its executable passed `--self-check`.
- The benchmark was rebuilt from llama.cpp revision `ddf48f85c933c1f438212a02eb21e7b001d2d37d` with static project libraries, HTTPS disabled and Metal included on the physical Mac build. OS-provided frameworks remain dependencies.
- The local build is ad-hoc signed and not notarized. Launch on another Mac and older macOS compatibility are not qualified.

The application checks its bundled native benchmark at startup. Python and its standard library are embedded and extracted by the frozen executable; no runtime download, system Python installation or telemetry is needed. A model and OS GPU drivers are not included or installed. The benchmark can use a user-supplied GGUF, while a request for GPU layers is not proof of effective accelerator allocation.

The generic probe is a standalone command-line tool. It does not replace the NodeLift host or implement enrollment of remote desktop workers. [Usage and limitations](../../docs/NODE_PROBE.md).
