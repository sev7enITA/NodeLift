# Contributing

Include device/OS, available memory, model revision/hash/quantization, llama.cpp and NodeLift revisions, topology and build settings. Never attach credentials, private prompts or signing material.

Preserve failed trials, load/warmup boundaries, actual output counts, paired output comparisons and the strongest applicable local baseline. Label simulated nodes and latency injection. CPU microbenchmarks do not establish LLM speed; multi-user throughput does not establish single-chat latency.

Keep native correctness, transport, mobile lifecycle and claims consistent. Compilation and model reviews do not qualify a physical device. Explain the relevant tests and remaining limits. Publish negative results too.

Retain third-party licenses and notices; do not vendor weights. Focused reproducible issues and improvements are more useful than unsupported acceleration claims.

## Documentation and release notes

Maintain authored repository documentation, Wiki pages, issue/PR templates and release notes in English. Runtime localization catalogs, non-English benchmark fixtures, third-party originals and verbatim review evidence retain their original text and provenance; explain them through English guides. Do not rewrite original measurement data or transcripts as though a translation were the source.

Every published mobile build must have a version/build entry in `releases/history.json`. Generate the repository and portal changelogs with `python3 scripts/release-history.py`, then check with `--check`. Android/iOS build scripts require matching notes before compilation. Follow [the release process](docs/RELEASING.md), publish the portal, and verify the actual remote bytes. CI cannot establish that the website was deployed.
