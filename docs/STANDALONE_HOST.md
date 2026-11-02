# Standalone NodeLift host for macOS Apple silicon

This is an experimental self-contained host preview, separate from the standalone [node probe](NODE_PROBE.md). [Download the ZIP](https://github.com/sev7enITA/NodeLift/releases/download/host-standalone-v0.3.0-preview.1/NodeLift-host-0.3.0-preview-macos-arm64.zip) and verify the [package manifest](../releases/standalone-host.json).

The package includes Python, the native inference library, dashboard and launcher. On startup it checks the native library, required dashboard assets and engine provenance. macOS supplies its system frameworks and `/usr/bin/openssl`, which is checked for local TLS identity creation. Models are not bundled. No Python installation, runtime download or system-wide library installation is required. A missing or broken component produces a startup error; repair is not an automatic network download.

Extract the archive and open **Start NodeLift.command**. The launcher checks whether the default dashboard port 9868 is in use, starts one host, opens its private local dashboard URL and keeps the Terminal window open for its lifetime. It uses the usual local NodeLift state folder. It does not stop or replace another running host. The launcher stores its session link in a private temporary file and deletes that file on exit.

Alternatively, in Terminal from the extracted folder:

```sh
./NodeLift-host --self-check
./NodeLift-host --address auto
```

Then use the private local URL printed by the host. Add a compatible GGUF through the dashboard before running inference. A system model, phone or external GPU driver is not downloaded by this package.

## Scope and limitations

The package has ad-hoc code signing, no Apple notarization and may be blocked by macOS. It has been tested on one M3 Max with macOS 27.2, not across other Macs or operating-system versions. The desktop host is still an experimental text/greedy engine. An individual localhost generation, UI and inventory check do not prove phone pairing, distributed speedup, capacity sharding, long-term stability or correctness on every model. Existing NodeLift state and models remain subject to their own lifecycle.

The [physical validation record](../research/standalone-host-2026-11-02/README.md) includes the initially failed candidate and the corrected model smoke test. The package contains notices for NodeLift, llama.cpp, CPython and PyInstaller. Windows and Linux downloads currently provide the separate CPU-only node probe, not this host.
