# Device graph verification — 1 November 2026

Scope: desktop control room, authenticated host inventory, telemetry timestamps and output-attribution presentation. The native inference algorithm, phone runtime, model weights and release binaries are unchanged.

## Automated checks

- `PYTHONPATH=host python3 -m unittest discover -s host/tests`: 80 tests passed, including legacy database migration, pairing preservation, independent contact/telemetry timestamps, missing host metrics and admin-only inventory.
- `node scripts/check-device-graph.cjs`: synthetic accounting cases cover remote drafts, host fallback, local drafts, lookup, EOS/output-budget tails, missing/inconsistent records and external providers. Memory scopes and dated diagnostic grouping are checked separately.
- Connection-state tests preserve unknown contact through language/engine redraws until a successful host status fetch. Geometry tests check six variable-height companion cards across one, two and three columns; relationship segments avoid every card interior.
- `node scripts/check-localization.cjs` and `python3 scripts/generate-localization.py --check`: English default, persistence, all three catalogs, parameter isolation and generated-file freshness passed.
- `python3 scripts/check-docs.py` and JavaScript syntax checks passed.

On this iCloud-backed checkout, Python's existing bytecode cache stalled imports. Repeating the host suite with `PYTHONPYCACHEPREFIX=/tmp/nodelift-graph-pycache` completed normally. This changes cache storage, not application code or test semantics.

## Live control-room checks

- Restarted the idle host after privately saving the previous session snapshot. Pairing and model configuration were preserved. The Mac inventory reported Apple M3 Max, 16 CPU cores and 64 GiB. Live free memory/process utilization remains unknown.
- The paired Android companion was offline and not native-ready. Its historical network/CPU records were shown with dates; its legacy telemetry receipt timestamp remained unknown. No phone job or native-phone benchmark was run for this UI update.
- A real host-only generation using the existing target completed with 14 committed token IDs. The graph showed 0 accepted mobile tokens / 14 committed IDs. This checks integration and attribution, not a speedup or representative performance benchmark.
- English, Italian and Simplified Chinese switching retained device selection and observed output. Online-only filtering showed the correct empty companion state. Inspector disclosures and keyboard focus survived repeated polling. The full control room had no horizontal overflow at the observed 1685 CSS-pixel width.
- A separate, clearly marked synthetic fixture exercised missing evidence, external runs, disconnection, access loss and six companions. Access loss cleared device buttons, run options, inspector content and share. Six companions produced seven entity cards and six relationship paths without horizontal overflow at the observed desktop width.

Synthetic data is UI/test evidence only. It does not establish six-phone operation, native mobile performance, pooled RAM, acceleration or energy savings. Run history in the selector is bounded to the current host process; native experiment files remain separate private records.

## Review boundaries

The requested Gemini high-capability model was unavailable due to the browser account's usage limit. No Gemini review is claimed for this change. Responsive captures used the synthetic fixture; fixed-header compositor artifacts in the emulated-viewport captures prevent treating those images as polished release/gallery screenshots. DOM geometry and functional checks are recorded separately from visual critique.

GLM 5.3 with Max effort returned PASS on the initial sanitized-source/synthetic-image review, with four recommendations: announce device selection without announcing polling updates; route multirow links outside cards and observe layout changes; remove unexplained percentage-dependent edge thickness; distinguish an unselected phone from a selected phone whose proposals were not accepted. These are UI findings, not model-performance validation. The initial review also reported that its CSS attachment was truncated before graph rules; focused styles are required for any follow-up review.

All four recommendations were implemented. A second GLM 5.3 Max review of the focused final JavaScript, graph CSS and markup returned PASS with no mandatory fixes. This follow-up was source-only, without a fresh visual or screen-reader execution. The local browser separately confirmed that changing to Italian during a simulated disconnection retained unknown-contact badges, the disabled filter and its correctly translated last-snapshot label. The production caller restores connectivity only after a successful `/admin/status` fetch; its pure transition tests and live host access were checked independently.
