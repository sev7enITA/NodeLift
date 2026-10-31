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
