# NodeLift 0.2.1: build and validation

31 October 2026. Experimental native inference release. **No physical-phone LLM speedup, pooled RAM or production readiness is established.**

| Component | Observed result | Boundary |
|---|---|---|
| Host / protocol / HTTP | 26 automated tests passed, including fresh startup, authorization separation, lease failures and split Unicode streaming | Contract tests use stub inference where explicitly labelled |
| Native core | 29 real-weight correctness checks passed on M3 Max / Metal | Four prompts, bounded outputs; not universal numerical equivalence |
| Remote work | Four real-weight TLS fault cases passed: valid/wrong/error/dropped proposals | Emulated local node, not a physical phone |
| Client gateway | Live real-weight normal/stream equality, Unicode, disconnect cancellation passed | One configured small target, greedy only |
| LM Studio adapter | TypeScript build, three stream tests, real SDK handler → live engine passed | CLI installation stalled and was stopped; GUI/plugin runtime remains unverified |
| Android | 0.2.1 build 3 ARM64 APK built; APK signature verified; native library and license notices packaged | Debug-signed lab build; updated native APK not physically exercised yet |
| iOS | Complete Release device build including native Metal/CPU framework and notices succeeded | Unsigned; physical installation/rendering/inference open |
| HarmonyOS NEXT | Separate source candidate retained | No native engine, SDK build or HAP |
| External reviews | Actual Gemini 4 High and GLM 5.3 Max design and source responses received and adjudicated | Static model advice, not device/runtime certification |
| UI | Desktop functional checks and first Gemini visual review; iOS build/parse passed | Post-fix visual recheck limited, no physical iOS UI test |

Local artifacts: `NodeLift-0.2.1-android-debug.apk`; release packaging adds a source ZIP, an explicitly unsigned iOS app ZIP and a SHA-256 build manifest. Artifacts/logs are ignored by Git; downloadable assets belong on the GitHub prerelease. Weights, private state, signing keys and user prompts are excluded.

The observed Xiaomi test still refers to the 0.1 qualification companion. The new connected benchmark runner refuses offline/legacy nodes; its full physical sequence remains pending. See [engine guide](../docs/ENGINE_0_2.md), [measured results](../research/measurements/ENGINE_RESULTS.md) and [review adjudication](../research/reviews/ENGINE_REVIEW.md).

## Historical 0.1 checkpoint

The section below records earlier evidence only; current status is above.

# NodeLift 0.1.0 — build e verifiche

31 ottobre 2026. **Companion di qualificazione: motore LLM distribuito non implementato.**

Aggiornamento dashboard dello stesso giorno: ripristino accesso verificato nella scheda dell'utente, avviso esplicito per sessione mancante, azioni disabilitate senza autenticazione e comando locale `scripts/open-dashboard.command`. Archivio sorgenti e manifest aggiornati; APK Android invariato.

Aggiornamento fisico successivo: companion Android installata dall'utente sullo Xiaomi 17 Ultra; pairing/heartbeat e quattro job reali completati (rete rapida, rete con pause, CPU e replica rete con pause). [Report e dati](../research/measurements/2026-10-31-xiaomi-hotspot/REPORT.md). Nessun benchmark LLM o controllo termico sostenuto. La tabella sotto conserva i controlli iniziali della build, prima di questa prova.

| Componente | Risultato osservato | Limite |
|---|---|---|
| Host HTTPS + dashboard | 14 test automatici passati; flusso invito verificato nel browser | Nessun telefono fisico associato durante la verifica |
| Android | `NodeLift-0.1.0-android-debug.apk` compilato; anche APK strumentale compilato | Test strumentale non eseguito: emulatore ADB offline e errore mprotect; HyperOS/ColorOS da provare |
| iOS | Build Release device e simulator riuscite | Firma disabilitata; non installato su iPhone |
| Client Swift | Pairing, trasferimenti, heartbeat e rifiuto certificato errato verificati su HTTPS locale | Esecuzione su macOS, non iOS |
| HarmonyOS | Progetto ArkTS candidato presente nei sorgenti | DevEco/SDK/firma assenti; nessun HAP prodotto |
| Revisione Gemini 4 High | Riesame del disegno completato e rilievi esaminati | Non audit del codice, non misura hardware |
| Revisione GLM 5.3 Max | Tentativo effettuato con effort Max | Servizio a capacità; nessuna revisione completata |

Distribuibili locali:

- `NodeLift-0.1.0-android-debug.apk`: build debug per test Android; non è la companion Huawei NEXT.
- `NodeLift-0.1.0-source.zip`: host, app, script, test, documentazione e ricerca con attribuzioni. Non contiene credenziali di pairing, database del laboratorio o chiavi di firma.
- `build-manifest.json`: hash SHA-256 e inventario dei sorgenti. I binari e i log sono esclusi dal tracking Git tramite `.gitignore`; questo README resta tracciabile.

Log: `host-tests.log`, `swift-protocol-check.log`, `android-build.log`, `android-test-build.log`, `ios-build.log`, `ios-device-build.log`, `android-emulator.log`.

Nessun risultato di questi controlli dimostra speedup LLM o prestazioni della rete hotspot. Per l'uso vedere [guida companion](../docs/COMPANION_0_1.md).
