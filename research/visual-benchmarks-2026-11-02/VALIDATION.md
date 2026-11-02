# Figure validation

- Reconciled all 9 plotted source cells directly against raw host/candidate attempts, independently of the renderer and summary helper. Checked all 42 completed output-equivalent pairs, duration ratios, duration differences, TTFT differences, accepted/proposed counts and fallback counts.
- Retained the interrupted iPhone cell with no eligible pair: one observed invalid candidate and two missing candidates out of three planned, plus three missing host attempts in the original evidence.
- Verified SHA-256 for all 9 source files and all 12 localized PNGs.
- Inspected timing, latency, adaptive and contribution figures for axes, labels and clipping. Verified the Italian desktop gallery, Chinese language switching and a 390-pixel browser layout. Narrow screens use horizontal figure scrolling and full-size links. This is browser layout validation, not a native phone test.
- JavaScript syntax, generated release-history consistency and documentation checks passed: 100 Markdown pages and 423 local link targets, no errors.

No new inference runs, energy samples or confidence intervals were generated. Reproducing the figures validates presentation of the retained observations, not independent performance replication.
