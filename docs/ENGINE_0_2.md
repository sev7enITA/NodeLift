# NodeLift: guida del laboratorio (companion 0.2.3)

Il motore nativo è stato introdotto nella 0.2.1; la companion attuale è 0.2.3/build 5, con inglese predefinito, cinese semplificato e italiano. **Non è ancora dimostrato uno speedup su telefoni fisici.**

## Computer

1. Compila con `scripts/build-native.sh`: llama.cpp deve corrispondere a `native/llama.lock`.
2. Scarica la coppia di controllo con `python3 scripts/fetch-control-models.py`, oppure colloca GGUF compatibili in `.models`. La dashboard legge anche il catalogo LM Studio.
3. Avvia l'host sulla sua IPv4 privata. Companion HTTPS/9867; dashboard/API client sul solo loopback/9868.
4. Apri il collegamento privato stampato all'avvio. L'indirizzo senza autenticazione mostra la pagina ma non autorizza i comandi.
5. Scegli target/draft, contesto/thread/GPU e premi Applica. Modifiche non applicate bloccano l'avvio.
6. Inizia con Host only. I pesi restano residenti; il caricamento è misurato separatamente. Arresta il processo host per liberarli.

La configurazione resta nella directory privata dello stato. Il token dashboard cambia al riavvio; la chiave API client è separata e persistente.

## Android ARM64

La 0.2.3 conserva la firma della 0.2.2. Un aggiornamento sopra altre versioni richiede la stessa firma di debug locale. Non disinstallare: l'aggiornamento conserva l'associazione. È una build per il laboratorio, non Play Store.

1. Installa l'APK aggiornato, apri NodeLift e Riprendi sessione.
2. Sul Mac scegli `qwen2.5-1.5b-instruct-q4_k_m.gguf` come target e `qwen2.5-0.5b-instruct-q4_k_m.gguf` come draft; Applica.
3. Sul telefono scegli Scarica draft dal Mac e attiva: circa 491 MB sulla rete locale. SHA-256 viene verificato prima del caricamento.
4. Attendi Draft pronto e nodo online con motore nativo disponibile nella dashboard.
5. Seleziona Remote draft e il nodo; comincia con 32–64 token e blocco 4, poi confronta Host only/Local draft sugli stessi prompt. La scadenza remota è regolabile nella dashboard (0,5–60 s, default 30); superarla attiva il fallback sul Mac.

Worker CPU ARM64, non NPU/Vulkan. Limiti: file fino a 1 GiB, contesto 512–4096, 1–8 thread. La soglia batteria è configurabile; termica moderata o superiore interrompe il lavoro nativo. Thread/contesto valgono al caricamento successivo. Il foreground service non prova l'assenza di limitazioni OEM o il funzionamento a schermo spento.

Il telefono riceve il contesto tokenizzato: è un dispositivo fidato, non un nodo pubblico. La revoca impedisce nuovi risultati autenticati. La cancellazione host invalida la lease, ma il telefono può terminare il piccolo blocco già in calcolo: manca ancora un canale separato di cancellazione remota immediata.

## iPhone / iPad

`scripts/build-ios.sh` richiede Xcode/xcodegen e produce una build device senza firma. Servono firma/provisioning validi per installarla. Nessun pacchetto App Store/TestFlight è stato prodotto.

Importa tramite Files lo stesso GGUF draft scelto sull'host, fino a 1 GiB. Viene copiato nell'area privata, verificato ed escluso dal backup. Scegli Metal/CPU e i limiti, abilita il motore e riprendi la sessione. L'app deve rimanere in primo piano; passando in background si mette in pausa. La compilazione non qualifica Metal o il budget RAM sull'iPhone fisico.

## Limiti

- Testo e greedy puro: niente tools, immagini, structured output, penalità o sampling stocastico.
- Un run attivo, massimo 512 token generati; niente batching multiutente.
- Target/draft devono avere gli stessi significati per gli ID dei token.
- Modelli ricorrenti/ibridi rifiutati fino a implementazione e qualificazione del ripristino tramite checkpoint. I grandi GGUF già presenti nel laboratorio sono Qwen35/Qwen35MoE.
- Remote draft non somma RAM dei telefoni per ospitare un target più grande. Sharding/offload di capacità restano aperti.
- HarmonyOS NEXT richiede una companion nativa distinta: l'APK Android non lo qualifica.

## Benchmark del telefono connesso

Il runner rifiuta nodi offline o senza motore pronto. Usa prompt pubblici, confronta host/local/remote in ordine casuale, conserva errori, fallback, token effettivi e telemetria prima/dopo. Le credenziali restano locali.

```sh
python3 scripts/benchmark-connected.py --topology "Xiaomi hotspot → Mac, Wi-Fi" --tokens 128 --repetitions 3
```

L'uscita predefinita è `artifacts/connected-benchmark` e deve essere nuova. Il gate offline è stato verificato; l'intero runner resta da eseguire sul telefono aggiornato. Il contesto configurato deve contenere prompt, output e blocco. Confrontare anche cavo/adattatore o access point dedicato richiede nuove prove reali della relativa topologia, non una stima dalla versione Wi-Fi.
