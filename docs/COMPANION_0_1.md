# NodeLift 0.1 — companion di qualificazione

31 ottobre 2026. Il nome **NodeLift** è stato scelto dall'utente. La directory storica del progetto rimane ExpandMyHW per preservare percorsi e ricerca. Questa è la prima implementazione del sistema di associazione e misura, **non un motore di inferenza distribuita**.

## Cosa è implementato

- Host Python senza dipendenze PyPI: server HTTPS per i nodi, dashboard web su loopback, inviti monouso di cinque minuti, registrazione e revoca, job limitati a test noti, risultati esportabili.
- Android Kotlin: UI nativa, servizio `connectedDevice`, rilevamento del modello, RAM fisica e memoria disponibile al sistema, termica, trasporto, battery indicator; sessione cifrata con Android Keystore.
- iOS SwiftUI: UI nativa, TLS con certificato host esplicitamente verificato, credenziali Keychain, termica e margine memoria del processo; pausa in background. Nessuna pretesa di daemon permanente.
- HarmonyOS ArkTS: **sorgente candidato**, UI, associazione, pinning SPKI e test rete in primo piano. Token solo in memoria; CPU, lettura RAM e inferenza non abilitati. Richiede SDK API 23+ per disabilitare redirect. Non è stato compilato né installato: DevEco/SDK e firma Huawei non sono disponibili nell'ambiente esaminato.
- Test rapidi di rete: 32 RTT applicativi con risposta da 64 byte, quattro download e upload per ciascuna dimensione 16 KiB/1 MiB. Un warmup escluso. Sono diagnostici: il p95 di 32 campioni è esplorativo, non una stima stabile della coda di latenza.
- Android/iOS: test rete con 600 RTT, divisi in tre gruppi da 200 con pause richieste 0/30/60 ms. La dashboard presenta i gruppi separatamente. L'ID di connessione assegnato dal server permette di osservare il riuso TCP/TLS. I ritardi effettivi del sistema operativo possono eccedere le pause richieste.
- Android/iOS: test CPU sintetico FP32 matvec 256×256, circa 1,5 secondi, un thread. Misura quel kernel e quel runtime, principalmente in cache; **non predice banda DRAM, GPU, NPU o token/s**.

Non sono implementati: caricamento GGUF sui telefoni, KV cache distribuita, draft/verify remoto, sharding dei layer, backend Harmony GPU/NPU, generator LM Studio o integrazione Ollama. Non è ancora dimostrato un vantaggio rispetto al Mac.

## Avvio sul computer

Prerequisiti host: Python 3.11+ con SQLite 3.35+ e OpenSSL disponibile nel PATH. Non installare certificati nell'archivio globale del computer o del telefono: la companion usa l'identità ricevuta nell'invito solo per NodeLift.

```sh
cd host
python3 -m nodelift.host --address IP_LOCALE_DEL_MAC
```

Sostituire `IP_LOCALE_DEL_MAC` con l'IPv4 privato del Mac sulla stessa rete/hotspot dei dispositivi. Il valore predefinito 127.0.0.1 è utilizzabile solo per prove sul computer. Il processo stampa il link privato della dashboard su `s`; aprire quel link sul Mac. Il token nel frammento è un segreto locale: non pubblicarlo.

1. Nella dashboard scegliere **Aggiungi dispositivo**.
2. Trasferire e incollare l'invito nella companion del telefono; vale cinque minuti e si usa una volta. Non inoltrarlo a soggetti estranei. Il pairing è manuale in questa build; non c'è ancora scansione QR o discovery mobile.
3. Scegliere **Associa e attiva nodo**. La companion fa solo connessioni in uscita al computer; non espone un server sul telefono.
4. Avviare dalla dashboard **Rete rapida**, **Rete con pause** oppure **Test CPU**, quando supportati dal client.
5. Esportare il JSON, che contiene i campioni e non le credenziali. **Pausa** sul telefono interrompe la disponibilità; **Revoca** sul computer invalida il token. **Dimentica computer** sul telefono elimina solo le credenziali locali: per invalidare anche il token sul server usare Revoca.

Il server ascolta soltanto sull'indirizzo scelto, non su tutte le interfacce. Il sistema operativo deve consentire le connessioni locali in entrata al processo Python. Non sono stati cambiati firewall, hotspot, autorizzazioni di sistema o impostazioni del router. `--bonjour` annuncia facoltativamente il servizio con `dns-sd`, dove disponibile; non sostituisce l'associazione e non abilita discovery nelle companion 0.1.

### Se «Aggiungi dispositivo» non risponde

Aprire il solo `http://127.0.0.1:9868` in una nuova scheda non trasferisce la sessione privata della scheda originale. La dashboard ora mostra un avviso in italiano e disabilita le azioni finché l'accesso non è valido. Riaprire il collegamento completo stampato dal server; se si usa la sessione avviata dall'assistente, con log privato in `~/.local/share/nodelift/host-session.log`, fare doppio clic su `scripts/open-dashboard.command`. Il comando verifica che la sessione sia ancora attiva e apre il browser senza stampare il segreto. Non serve reinstallare la companion.

Correzione verificata nel browser il 31 ottobre 2026: scheda senza sessione con avviso e pulsanti disabilitati; ripristino della sessione; clic su «Aggiungi dispositivo» con invito effettivamente generato. Un collegamento con sessione aperto nella stessa scheda viene ricaricato anche se cambia soltanto il frammento dell'URL. Nessuna modifica al protocollo mobile o alle autorizzazioni.

Certificato iniziale valido 30 giorni. Cambio di IP richiede un nuovo `--state` e nuova associazione, perché l'identità contiene il SAN IP. Rotazione guidata, DNS stabile e UX QR sono lavoro successivo. Lo stato predefinito è `~/.local/share/nodelift` con directory privata e token salvati solo come hash; i certificati e la chiave privata sono locali al computer.

## Compilazione e installazione

### Android

JDK 21, SDK Android 36 e Gradle wrapper 8.13. Build verificata con Android Gradle Plugin 8.12.0 e Kotlin 2.1.20.

```sh
./scripts/build-android.sh
```

APK: `apps/android/app/build/outputs/apk/debug/app-debug.apk`; copia consegnabile in `artifacts/NodeLift-0.1.0-android-debug.apk`. È una **build debug**, non una release Play Store. L'installazione su telefono e i test OEM HyperOS/ColorOS restano da fare. Non installare questo APK sul Huawei dichiarato HarmonyOS NEXT come se fosse la companion nativa.

### iOS

```sh
./scripts/build-ios.sh
```

Il progetto Xcode è `apps/ios/NodeLift.xcodeproj`, rigenerabile da `project.yml` con XcodeGen. Sono riuscite compilazioni Release per simulatore e device, con firma disabilitata. **Un'app non firmata non è installabile sull'iPhone**: aprire il progetto in Xcode, scegliere il team di sviluppo e il dispositivo, quindi eseguire la firma/installazione prevista dall'account. Nessun certificato/account Apple è stato creato o alterato e nessun invio a TestFlight/App Store è stato effettuato.

La companion iOS non disabilita automaticamente il blocco schermo. Per una misura mantenere l'app attiva; il blocco/background la mette in pausa. Misurare separatamente eventuali prove con schermo tenuto acceso, perché influiscono sulla termica.

### HarmonyOS NEXT

Aprire `apps/harmony` in DevEco Studio con SDK compatibile API 23+; configurare la firma per il dispositivo e risolvere eventuali differenze del toolchain rispetto al candidato. Questa è una **fase ancora da eseguire**, non una procedura verificata. Il nome/versione OS “HarmonyOS NEXT 7” proviene dall'utente; API level e build effettivi vanno letti sul telefono. Non attribuire a un HAP non prodotto compatibilità verificata.

## Protocollo e confini

`POST /v1/pair` consuma l'invito; tutte le altre API del nodo richiedono un bearer revocabile. `/v1/heartbeat` aggiorna telemetria e consegna un job una sola volta. `/v1/probe` e `/v1/upload` limitano il payload a 1 MiB. `/v1/result` accetta soltanto il proprietario del job in esecuzione, entro 120 secondi; replay, token revocati e risultati tardivi vengono rifiutati. I client interrompono il test dopo circa 90 secondi e controllano lo stato termico tra richieste/iterazioni. Il timeout di rete di una singola operazione può aggiungersi al limite tra operazioni.

Se il client viene chiuso durante una prova, il job può restare visibile in esecuzione fino al timeout: non è ripreso automaticamente e non riceve un risultato inventato. Le credenziali non autorizzano esecuzione shell, download di codice o allocazioni di memoria richieste dal server. Il protocollo di inferenza futuro richiederà un progetto separato.

Memoria Android “disponibile” e margine iOS `os_proc_available_memory()` hanno **significati diversi**: il primo è un dato del sistema, il secondo un margine per processo. Non sommarli e non usarli come budget allocabile già validato. La dashboard mostra la piattaforma e il dato osservato, non una promessa di RAM recuperata.

I test HTTPS includono stack applicativo, code, TLS e copie. Non sono iperf, banda PHY o latenza di un futuro protocollo tensoriale. Nessun p99 affidabile viene dedotto dal test rapido; i trasferimenti grandi sono ancora pochi. Servono campioni aggiuntivi, ordine randomizzato, più sessioni, carico concorrente e test fisici sostenuti secondo `BENCHMARK_PROTOCOL.md`.

## Stato delle verifiche

**Aggiornamento fisico successivo, 31 ottobre:** l'utente ha installato la companion sullo Xiaomi 17 Ultra e confermato che il telefono fornisce l'hotspot al Mac. Associazione, heartbeat, due prove con pause, una prova rapida e CPU sintetica sono stati completati sul dispositivo. [Campioni e report](../research/measurements/2026-10-31-xiaomi-hotspot/REPORT.md). Questo supera il limite di assenza di un primo test fisico Android descritto nei controlli iniziali sotto; restano aperti gli altri dispositivi, i test termici sostenuti e l'inferenza LLM. Il riepilogo Android 0.1 della prova con pause mostra soltanto i primi 32 RTT: usare la dashboard o il report per i gruppi completi; correzione mobile da distribuire.

Controlli iniziali della build, precedenti alla sessione Xiaomi:

- 14 test automatici host passati: TLS non fidato, invito scaduto/riutilizzato, autenticazione/revoca, limiti payload, proprietà/lease job, replay, timeout, origine dashboard e segreti assenti dall'export.
- Client Swift reale provato contro HTTPS locale su **macOS**: pairing, download/upload autenticati, heartbeat e rifiuto fingerprint alterato. Non equivale a test iPhone.
- Test strumentale Android scritto e APK test compilato. L'emulatore dedicato non ha completato l'avvio (`mprotect ... Permission denied`, ADB offline); nessun pass strumentale Android dichiarato.
- Dashboard verificata via browser: caricamento, stato vuoto, creazione/chiusura invito. Screenshot non ottenuto per timeout del browser; nessuna validazione visiva completa dichiarata.
- Nessun telefono fisico collegato agli strumenti durante il controllo. Nessun benchmark hotspot, termico prolungato o LLM eseguito.
- Gemini 4 High ha completato il riesame del **disegno**, con contributi e correzioni documentati; GLM 5.3 Max è ancora indisponibile per capacità. Nessun audit del codice attribuito ai due modelli.

I log si trovano in `artifacts/`. I dettagli della ricerca rimangono nel dossier DistAI e nell'assessment iniziale.
