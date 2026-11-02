# Physical iPhone comparison plan

2026-11-02. Preparation only until a physical iPhone is paired, online and draft-ready. No iPhone performance result is implied by this plan.

Use the same host target/draft files, native build, context 2048, requested 8 host threads, requested 999 host GPU layers and three public prompts as the [Xiaomi study](../phone-tradeoffs-2026-11-02/PLAN.md). Keep the Mac and iPhone on the user-reported Xiaomi hotspot. This is a different link arrangement: Xiaomi was the hotspot provider in its own tests, whereas iPhone and Mac are both clients. Hotspot client isolation may prevent pairing. Do not present the comparison as a pure SoC ranking.

Require an actual enrolled iPhone, fresh heartbeat and matching draft hash. Reject simulator/emulator evidence. Record companion version, reported thermal/battery/memory context and the execution mode if known. iOS source defaults to requesting Metal; that does not attest which backend an installed app actually uses. The current heartbeat does not advertise that setting. Unknown backend stays unknown.

Run serially, with no simultaneous Xiaomi inference:

1. Remote adaptive versus host, 32-token budget, 6 randomized paired trials.
2. Remote fixed versus host, 32-token budget, 6 randomized paired trials.
3. Remote adaptive versus host, 128-token budget, 6 randomized paired trials.
4. Remote fixed at 128 tokens: schedule 3 pairs only if fixed-32 median completed-service slowdown is <=5x and at least half its planned requests complete without fallback. Otherwise record the predeclared exclusion explicitly.

One unscored warmup pair per cell. Fixed draft width 4 and configured remote deadline 10 seconds; unchanged adaptive engine can tighten it. Pair outputs by full token hash, count and finish reason. Preserve missing, failed, mismatched and fallback attempts. Use completed-service timing including fallback separately from clean no-fallback timing. Cells remain correlated collection periods, not independent confidence evidence.

Keep the iPhone app foregrounded. Stop if readiness or observed connection continuity is lost, configuration/artifact metadata changes or battery/thermal limits prevent work. Do not force repeated pairing or inference on a disconnected device. No standalone network stress diagnostic is scheduled: the previous Xiaomi diagnostic timed out and its cause remains unresolved.

Energy, sustained thermal endurance, maximum main-model capacity and shared RAM remain unqualified. Do not attribute remote wait solely to Wi-Fi or to worker compute. A successful QR scan alone does not establish enrollment, network reachability or LLM readiness.
