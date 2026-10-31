# ExpandMyHW — protocollo sperimentale proposto

Versione preliminare, 31 ottobre 2026. Nessun risultato hardware ancora raccolto. Il protocollo va congelato dopo l'inventario dei dispositivi e prima di osservare i risultati decisivi. Le soglie seguenti sono proposte ingegneristiche per rendere misurabile «superare nettamente», non prestazioni previste né già approvate dall'utente.

Aggiornamento successivo dello stesso giorno: raccolta la [prima diagnostica fisica Xiaomi/hotspot](research/measurements/2026-10-31-xiaomi-hotspot/REPORT.md). È un pilot di trasporto e CPU sintetica, con replica esplorativa, non il benchmark end-to-end o la verifica dei gate descritti sotto.

## Domanda primaria e controlli

**Una singola conversazione con lo stesso target diventa sensibilmente più veloce aggiungendo uno o più telefoni, rispetto alla migliore configurazione locale praticabile?**

Baseline da misurare e pubblicare:

| ID | Configurazione | Perché serve |
|---|---|---|
| B0 | Host target solo, backend accelerato e parametri ottimizzati | Guadagno rispetto all'esecuzione usuale ottimizzata |
| B1 | Host target + migliore draft locale compatibile | Evita di attribuire alla rete il guadagno della sola speculation |
| B2 | B1 con overlap/asincronia locale, se supportata | Controlla che il guadagno non venga da una migliore pipeline disponibile anche localmente |
| D1 | Target host + draft autonomo telefono, blocchi sincronizzati | Isola costo rete e vantaggio di delega |
| D2 | D1 con overlap e cancellazione/rollback | Misura il vantaggio asincrono, non lo presume |
| P1 | Stesso target distribuito per layer, come riferimento DistAI | Controllo negativo/positivo a seconda della capacità dell'host |
| C0/C1 | Target fuori capacità host: out-of-core locale / shard residenti remoti | Esperimento capacità separato |

Se un'opzione locale non è supportata dal backend, documentare il limite e restringere il claim. Non dichiarare «batte ogni soluzione locale» dopo aver provato solo B0. Usare budget di tuning comparabile e dati di tuning separati da quelli di test.

## Identità e condizioni da registrare

- Computer e telefoni/tablet: modello/SoC, RAM fisica e utilizzabile dal processo, OS/build, backend, driver, alimentazione, temperatura/stato termico, batteria, app concorrenti.
- Modello target e draft: repository, revisione immutabile, SHA-256, quantizzazione, tokenizer completo, chat template, contesto, KV dtype, cache, sampler, seed, numero esperti e routing invariati.
- Runtime: commit completo, build flags, patch hash, backend effettivamente usato, offload layer, thread, batch/ubatch, flash attention, cache prompt. Verificare che nessuna fase sia caduta su CPU involontariamente.
- Rete: AP/router, banda/canale e modalità negoziata, distanza/ostacoli, numero peer e carico concorrente; porte USB, cavo/hub, adattatore e switch. Identificatori privati sostituiti da ID anonimi nei log da pubblicare.
- Policy: nessuna inferenza cloud o download durante la prova; modelli già locali per run warm. Il caricamento cold viene cronometrato separatamente.

## Fase 0: trasporto e capacità, prima di un runtime completo

Stesso telefono sui trasporti disponibili: Wi-Fi, USB networking, ADB di laboratorio Android, Ethernet compatibile. Misurare entrambe le direzioni e full duplex, con peer singolo e più peer simultanei.

Dimensioni indicative dei messaggi: 64 B, 4 KiB, 16 KiB, 64 KiB, 1 MiB, 16 MiB, più trasferimento pesi sostenuto. Poi sostituirle/affiancarle con le dimensioni effettive dei tensori e dei blocchi del modello scelto. Registrare latenza applicativa p50/p95/p99, goodput, perdita/errori e queueing; distinguere RTT da tempo unidirezionale. Senza clock sincronizzati, non sottrarre timestamp di host differenti come se lo fossero.

Ripetere radio idle, traffico continuo e rete contesa; misurare keepalive attivo/spento con relativo consumo. Non usare il migliore ping o la copia più veloce come costo per ogni token. Misurare anche caricamento, picco RAM e pressione dopo 30 minuti; non forzare OOM deliberati sul computer di lavoro.

## Fase 1: microesperimenti discriminanti

### E1 — draft autonomo, una sola chat

Un telefono ospita tutto il draft e propone blocchi k=1/2/4/8/16 (solo valori supportati e sicuri). Host verifica e committa; contesto e sequenza delle proposte hanno ID/versione. Iniziare greedy. Misurare per blocco: tempo draft, trasferimento, attesa, verifica, token accettati, rollback, bytes reali e lavoro scartato.

Confrontare D1/D2 contro migliore B0/B1/B2 sul medesimo workload. Accettazione non costante: varia per task, contesto e posizione. Non ottimizzare solo su un prompt numerico ripetitivo. Il rapporto tra velocità draft e target è necessario ma non sufficiente.

**Stop anticipato di fattibilità:** se già il limite ottimistico, dichiarando quali costi trascura, non può battere la baseline, non costruire il plugin per quella combinazione. Se lo supera, serve comunque la prova end-to-end. Per il sampling non greedy, misurare il costo del protocollo esatto e verificarne l'algoritmo di acceptance/rejection e residual sampling; nessuna equivalenza presunta per l'invio dei soli ID.

### E2 — capacità senza ricaricare pesi per token

Selezionare un target/contesto che effettivamente supera la memoria disponibile all'host. Confrontare C0/C1 a identità modello invariata, registrando paging, SSD I/O, caricamento, TTFT e decode. Non scegliere una quantizzazione peggiore o meno esperti solo per il cluster.

**Stop:** memoria mobile o KV insufficiente, riavvii frequenti, costo remoto maggiore del percorso out-of-core misurato. Se C0 non è avviabile, dichiarare nuova capacità e tempi assoluti di C1, senza un rapporto di speedup inventato.

### E3 — controllo dei trasporti e della policy

Ripetere la migliore D/P sullo stesso set di nodi cambiando soltanto trasporto. Confrontare tutti i nodi contro sottoinsieme scelto dal planner e host solo. Introdurre contesa di rete, throttling osservato e uscita di un nodo. Contare il tempo speso a rilevare, riplanificare e ricostruire il contesto.

**Stop:** il guadagno esiste solo nel primo minuto, sparisce a regime o richiede esclusioni manuali che il planner non sa riprodurre. Un routing sbagliato non va nascosto eliminando quel run.

## Fase 2: benchmark end-to-end

- Prompt corti/medi/lunghi, inizialmente circa 512/2048/8192 token se supportati; misurare i token reali dopo il template. Output fisso 128/512 token per il benchmark di velocità e output naturale separato per qualità/EOS.
- Task almeno di coding, ragionamento, testo italiano/inglese e riassunto lungo; dati fissati con hash. Il set prestazionale non sostituisce una suite qualità ampia con casi limite e risultati analizzabili.
- Due tracce: conversazione singola, senza concorrenza; carico multiutente/coda separato. Il secondo non può far passare il criterio primario.
- Cache fredda e calda dichiarate; prompt-cache hit/miss separati. Niente riutilizzo involontario del prompt per favorire una configurazione.
- Ordine delle configurazioni randomizzato e confronti appaiati per prompt; sessioni in blocchi temporali con condizioni iniziali comparabili. Run di almeno 30 minuti per stato termico sostenuto.
- Piano iniziale: almeno 30 prompt di test e 5 ripetizioni appaiate per la configurazione finalista, distribuite su più sessioni; pilot per stimare varianza e adeguare numerosità **prima** della prova finale. Non trattare migliaia di token correlati come migliaia di osservazioni indipendenti.
- Mediana, p95 e intervalli bootstrap al 95% raggruppando per prompt/sessione; pubblicare anche singoli casi, timeout, fallimenti ed eventuali esclusioni motivate. Un risultato inconcludente richiede più dati, non un claim favorevole.

## Metriche e gate proposti

| Dimensione | Definizione | Criterio proposto |
|---|---|---|
| Velocità primaria | Token generati/tempo decode a output controllato; confronto appaiato con migliore baseline locale | Mediana dello speedup almeno 1,30× e limite inferiore CI95% oltre 1,10× |
| Esperienza complessiva | Tempo dal submit all'ultimo token utile, cold/warm separati | Riduzione mediana almeno 20% nella traccia principale preregistrata |
| Coda della latenza | p95 inter-token/tempo risposta, incluse attese tra burst | Nessun peggioramento >5% rispetto alla baseline; incertezza dichiarata |
| Avvio | TTFT visto dal client, inclusi rete e scheduling | Nessuna regressione >10% warm nella traccia principale; cold pubblicato separatamente |
| Sostenibilità | Stesse metriche nell'ultimo terzo del run ≥30 minuti | I gate di velocità continuano a passare |
| Qualità | Greedy e tolleranze numeriche predefinite; sampling esatto e suite task | Nessuna modifica nascosta a target/esperti/contesto; regressioni spiegate e criterio preregistrato |
| Energia | Energia totale host+nodi+rete misurabile per risposta/token utile | Pubblicare anche se peggiora; soglia energetica di prodotto da concordare |
| Affidabilità | Completamenti corretti, timeout, replay, cancellazione, disconnessioni | Nessuna risposta corrotta o token non verificato committato; costi di recupero espliciti |

1,30× in velocità corrisponde a circa 23,1% di riduzione del tempo di quella fase, non al 30%. Le diverse metriche possono divergere: risposte in burst possono aumentare token/s ma peggiorare la fluidità. Il sistema non passa se vince solo una media nascondendo il resto.

Per il claim «supera DistAI», riprodurre una configurazione comparabile sullo stesso hardware con build accelerata e tuning equo; distinguere guadagni dovuti al backend aggiornato da quelli del runtime. Se DistAI non supporta un dispositivo, riportare copertura aggiunta, non uno speedup contro una baseline inesistente. Non usare direttamente 3,9 token/s su vecchio PC come avversario del M3 Max.

## Evidenze minime da conservare

Manifest immutabile del run; JSONL per richiesta e per blocco; timestamp monotoni; numero token e bytes; output e hash (solo prompt non sensibili); metriche host/mobile; condizioni rete; errori; intervalli di confidenza e script di analisi. Per coding, eseguire risposte in una sandbox vera: `python -I` da solo non basta.

Pubblicare insieme risultati favorevoli e negativi. Non chiamare benchmark una simulazione, una stima da banda teorica o la revisione di un modello esterno.
