# NodeLift: first physical Xiaomi/hotspot trial

31 October 2026. Exploratory protocol diagnostics; no LLM inference was performed. This report preserves the conditions and limitations of that historical session.

## Observed configuration

The owner confirmed that the Xiaomi 17 Ultra provided the hotspot to the M3 Max Mac. The companion paired, sent heartbeats and completed jobs requested by the Mac.

App-reported telemetry: **Xiaomi 25128PNA1C**, **Android 17 / API 37**, 14.76 GiB physical RAM and 4.87 GiB system-available memory at the initial reading. This is not a verified allocatable LLM memory budget. Retained readings showed nominal thermal status; no prolonged thermal test was performed. Commercial device identity and the installed APK hash were not independently attested.

The app's transport field reported “other / not detected”: it reads the phone's default network, which does not necessarily identify the hotspot interface used toward the Mac. The topology therefore comes from the owner's confirmation, not that field.

## Application HTTPS latency

RTT measured on the phone with a monotonic clock and a 64-byte response; warmup excluded. Requested pauses are outside RTT timing. Empirical nearest-rank percentiles; these are not ping, one-way latency or per-token times.

| Trial | Requested pause | Samples | p50 ms | p95 ms | Maximum ms | Over 20 ms | Connections |
|---|---:|---:|---:|---:|---:|---:|---:|
| Quick | 0 ms | 32 | 6.28 | 8.25 | 8.79 | 0 | 1 |
| Paced | 0 ms | 200 | 7.68 | 11.30 | 90.55 | 1 | 1 |
| Paced | 30 ms | 200 | 8.30 | 14.24 | 95.03 | 8 | 1 |
| Paced | 60 ms | 200 | 8.91 | 79.88 | 89.19 | 15 | 1 |
| Paced repeat | 0 ms | 200 | 6.21 | 8.27 | 94.70 | 2 | 1 |
| Paced repeat | 30 ms | 200 | 7.80 | 11.77 | 98.56 | 8 | 1 |
| Paced repeat | 60 ms | 200 | 8.80 | 68.37 | 97.96 | 14 | 1 |

## Transfers

Goodput = useful bytes / sum of application times. Decimal MB; 1 MiB = 1,048,576 bytes. Four requests per size and direction: brief diagnostics, not sustained bandwidth or PHY rate.

| Trial | Direction | Payload | MB/s |
|---|---|---:|---:|
| Quick | Mac → Xiaomi | 16 KiB | 2.33 |
| Quick | Mac → Xiaomi | 1024 KiB | 36.11 |
| Quick | Xiaomi → Mac | 16 KiB | 1.19 |
| Quick | Xiaomi → Mac | 1024 KiB | 19.89 |
| Paced | Mac → Xiaomi | 16 KiB | 2.37 |
| Paced | Mac → Xiaomi | 1024 KiB | 42.97 |
| Paced | Xiaomi → Mac | 16 KiB | 1.14 |
| Paced | Xiaomi → Mac | 1024 KiB | 37.12 |
| Paced repeat | Mac → Xiaomi | 16 KiB | 2.34 |
| Paced repeat | Mac → Xiaomi | 1024 KiB | 42.15 |
| Paced repeat | Xiaomi → Mac | 16 KiB | 1.08 |
| Paced repeat | Xiaomi → Mac | 1024 KiB | 36.74 |

## CPU and limitations

The CPU trial completed **14115 iterations in 1500.05 ms**. It is a single-threaded Kotlin/JVM FP32 256×256 matvec, mostly in cache. It does not measure GPU/NPU, DRAM bandwidth or tokens/s and is not compared with a different host kernel.

Trials used a fixed 0/30/60 ms order. The repeat was added after observing the first trial's latency tail: it is exploratory, in the same session, and not an independent preregistered confirmation. Do not causally attribute differences to pauses or power saving without controlling order, interference and concurrent load. Server connection IDs expose connection reuse; they do not rule out scheduling, radio, TLS and copy costs.

The median alone cannot size the protocol. More sessions, randomized pause order, alternative transports, sustained measurements and a real LLM workload against the optimized Mac are needed. These diagnostics neither passed nor failed an inference-speedup gate. Do not derive a speedup from total physical RAM.

In Android companion 0.1, the paced test's “Last measurement” summary uses only the first 32 RTTs. Use this analysis or the dashboard, which separates all samples by pause. At this checkpoint, the mobile summary correction had not yet been distributed.

## Reproduction

Run `python3 analyze.py` in this directory. Original JSON files contain the samples; `conditions.json` records conditions and unknowns; `jobs.json` identifies trials. `summary.json` is derived. `evidence-manifest.json` retains hashes of data and protocol sources. It contains no credentials or pairing invitations. English documentation does not change the original measurement files or their hashes.
