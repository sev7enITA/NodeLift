# Repository publication verification: 1 November 2026

Source update: [`07e31d34e7b8aee1d0c1836932404281e110da46`](https://github.com/sev7enITA/NodeLift/commit/07e31d34e7b8aee1d0c1836932404281e110da46). This record and the README visual preview are documentation-only follow-ups.

- The [Wiki](https://github.com/sev7enITA/NodeLift/wiki) has 10 content pages plus sidebar/footer. All 12 remote Git files exactly match `docs/wiki`; all 10 content URLs returned HTTP 200. Home rendering and navigation were checked in Chrome.
- [Source checks](https://github.com/sev7enITA/NodeLift/actions/runs/41268529285), [documentation checks](https://github.com/sev7enITA/NodeLift/actions/runs/41268529287), [release verification](https://github.com/sev7enITA/NodeLift/actions/runs/41268561791) and [native build](https://github.com/sev7enITA/NodeLift/actions/runs/41268563738) all completed successfully at the source update commit.
- The release verifier downloaded the published 0.2.3 manifest and packages, checked every size/SHA-256 against GitHub digests and the manifest, and checked tag/source identity. It does not execute packages or verify signing identity.
- Native CI compiled the locked core on a GitHub-hosted macOS runner. It did not load model weights, exercise phone inference or measure a speedup.
- Local checks validated documentation/image targets, current download links, Wiki inventory, diagnostic boundaries and release-verifier rejection of foreign/corrupt/oversized assets.
- Repository homepage now links the public showcase. Topics identify local AI, GGUF, llama.cpp, speculative decoding, Android/iOS, Apple Silicon and benchmarking.
- Gallery images are existing original brand artwork and dated real public-showcase captures. They are not new mobile-app screenshots. The captured desktop showcase was inspected before embedding it in the README.

The [REA assessment](../../../research/rea-2026-11-01/ASSESSMENT.md) records a pinned source review and reuse decisions. No REA code was vendored. Physical companion operation, mobile screenshots and measured phone speedup remain separate open qualification work.
