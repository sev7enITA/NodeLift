# Standalone host physical validation

2 November 2026. [Package manifest](../../releases/standalone-host.json) records exact source, native-library and archive identities.

A self-contained Apple silicon host was built from clean tracked source plus the frozen-resource path change. It bundles Python 3.14.6, the native library and dashboard assets. The macOS operating system still supplies system frameworks and `/usr/bin/openssl`; a local GGUF is supplied by the user. No automatic package download occurs.

On one physical M3 Max running macOS 27.2, the packaged executable passed its startup check. With an isolated temporary state directory and loopback-only ports, the dashboard, branded SVG, authenticated inventory route and bundled native library were exercised. A Qwen2.5-0.5B Q4_K_M model was imported by path, configured for CPU and generated eight tokens. Temporary state was removed after the test; the existing running host was not modified.

The first candidate failed generation because the frozen bundle looked for `native/llama.lock` outside its resource directory. The corrected build resolves the bundle root explicitly and contains the lock file; the subsequent generation completed. The uncorrected result is not promoted to a successful test. The ZIP was re-extracted with the macOS archive utility and its self-check passed. A separate launcher test verified startup and shutdown on isolated ports without automatically opening a browser.

Clean selected source passed 156 host tests. This is not a physical peer-pairing, Wi-Fi, sustained performance, output-equivalence, energy or speedup qualification. The build uses ad-hoc signing and is not Apple-notarized; another Mac may refuse to run it. Other macOS versions and architectures remain unqualified.

Reproduce with an explicitly selected GGUF:

```sh
python3 scripts/validate-standalone-host.py --host /path/to/NodeLift-host --model /path/to/model.gguf
```

The validation helper requires Python for the developer running the test. The packaged host itself does not require system Python.
