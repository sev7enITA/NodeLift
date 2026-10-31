# Revisioni esterne: stato ed esame critico

**Aggiornamento successivo del 31 ottobre:** Gemini 4 High ha completato un nuovo riesame del disegno NodeLift; GLM 5.3 Max ha nuovamente risposto che il servizio è a capacità. La tabella sotto conserva lo stato della prima sessione; gli esiti aggiornati sono descritti in fondo. Nessuna revisione esterna del codice o convalida hardware è stata ottenuta.

31 ottobre 2026. L'utente ha richiesto GLM 5.3 Max e Gemini 4 High via browser. Sono stati usati i servizi indicati con i selettori verificati nell'interfaccia; nessuna sostituzione con altri modelli è stata accettata. Sono stati trasmessi quesiti tecnici e fonti pubbliche, non codice privato AudioEnhancer né credenziali.

## Stato effettivo

| Revisore richiesto | Osservazione | Esito |
|---|---|---|
| GLM 5.3, effort Max | Prima richiesta generale ha prodotto appunti di ricerca senza conclusione; interrotta per concentrare il lavoro su DistAI. Secondo prompt specifico ha ricevuto «Model is currently at capacity»/«Currently in peak hours» | **Revisione finale non disponibile**; non accettato il suggerimento di passare a Flash |
| Gemini 4, ragionamento Alta (selettore 4 Argon / Alta) | Prima richiesta interrotta, seconda risposta parziale; poi limite d'uso con reset indicato alle 17:45 e interfaccia passata a Flash-Lite | **Revisione parziale**, non copre l'intero dossier DistAI e non è un'approvazione |

Trascrizioni: [Gemini parziale](gemini-4-high-partial.txt), [GLM indisponibile e prompt](glm-5.3-max-unavailable.txt). Il testo Gemini è conservato come evidenza di quanto affermato dal revisore, **non come fonte verificata dei fatti**. La cattura screenshot del browser GLM ha restituito timeout; lo stato di capacità è stato letto nell'albero accessibile. Nessuna attestazione visiva completa allegata.

## Come sono stati trattati i suggerimenti Gemini

| Affermazione | Decisione | Motivo |
|---|---|---|
| Pipeline di layer su nodi più lenti peggiora la singola sequenza quando il target risiede sull'host | Accolta con ipotesi esplicite | Somma dei tempi sul percorso critico, coerente con risultati DistAI |
| Confrontare draft remoto con draft locale | Accolta e rafforzata | Serve anche baseline locale asincrona dove supportata |
| NO-GO universale per ogni distribuzione se il modello entra sul Mac | **Non accolta come teorema generale** | Le ipotesi della pipeline seriale non coprono ogni parallelismo/speculation/contesa hardware |
| Draft remoto perde sempre, salvo RAM locale satura | **Non accolta come conclusione dimostrata** | Assume velocità relative, stesso costo verifica e nessun beneficio di overlap o minore contesa; va misurato |
| Wi-Fi ha sempre specifici range di banda/latenza e cavo sempre un ordine di grandezza migliore | Non usata per dimensionamento | Mancano misure sui nostri telefoni/router; valori generici non sono evidenza |
| exo supporta attivamente macOS e Linux | Corretta | PLATFORMS.md consultato riporta Apple Silicon macOS Tier 1 e Linux Planned |
| distributed-llama passa il 90% in busy-wait con questi nodi | Scartata | Nessun benchmark della configurazione fornito a supporto |
| iOS offre sempre circa 4–6 GB per app | Scartata come regola | Dipende da modello, OS, entitlement e pressione memoria; non è un budget universale |
| BGContinuedProcessingTask non è un daemon permanente | Accolta con documentazione Apple | Disponibilità risorse e lifecycle vanno gestiti, senza negare a priori GPU background supportata |

La revisione generale GLM aveva riconosciuto correttamente alcuni limiti di piattaforma e RPC, ma non ha restituito una valutazione completa: non attribuiamo al modello le conclusioni del dossier. I rilievi DistAI provengono dalla nostra ispezione del codice e dai ricalcoli riproducibili.

## Chiusura ancora necessaria prima del progetto definitivo

Riproponibile a entrambi i modelli il prompt mirato conservato nel file GLM e i tre documenti di assessment, chiedendo: verificare causalità e baseline; contestare gli esperimenti E1/E2/E3; controllare sampling esatto e lifecycle iOS; identificare precedenti che riducono la novità. La risposta dovrà essere esaminata criticamente e le eventuali correzioni registrate. Nessun consenso fra modelli può sostituire prove sui dispositivi.

## Riesame NodeLift dopo l'inventario dei dispositivi

Selettori verificati: Gemini **4 Argon / Alta** e GLM **5.3 / Effort Max**. Il quesito descriveva i risultati DistAI, i dispositivi dichiarati, la rete hotspot e il disegno delle companion di qualificazione. Non conteneva credenziali, indirizzi privati o codice AudioEnhancer.

- [Gemini: prompt e risposta completa](gemini-4-high-nodelift-followup.txt).
- [GLM: prompt e nuova indisponibilità](glm-5.3-max-nodelift-retry.txt). Non sostituito con Flash.

Gemini ha rivisto la conclusione assoluta precedente: riconosce ora il draft autonomo asincrono come ipotesi da confrontare con il migliore draft locale. Corregge anche exo/Linux e riconosce il generator plugin LM Studio. Questo è un riesame del disegno descritto, non un audit dei file implementati.

| Rilievo nuovo | Trattamento |
|---|---|
| Misure tutte ravvicinate nascondono il risveglio radio | Accolto: aggiunto job `network_paced` su Android/iOS, 200 RTT per ciascuna pausa richiesta 0/30/60 ms; risultati separati per gruppo |
| N=32 rende debole il p95 | Accolto il limite statistico; non l'affermazione letterale «non permette di calcolarlo». Il percentile empirico si può calcolare ma ha alta incertezza. Test rapido etichettato diagnostico |
| Connessioni/TLS/stack diversi falsano confronti | Accolto: ID di connessione server registrato nei campioni RTT; rimosso disconnect esplicito Android dopo risposta completa. Non presunto identico riuso degli stack |
| Matvec 256×256 non misura banda DRAM o performance LLM | Accolto e dichiarato in UI/documentazione; nessun predittore token/s basato su quel test |
| Host asyncio, Android OkHttp | Corretto: implementazione effettiva usa ThreadingHTTPServer e HttpsURLConnection; il revisore non aveva il codice e non ha verificato questi dettagli |
| connectedDevice richiede necessariamente USB/Bluetooth | Non accolto: la documentazione Android comprende connessioni di rete con prerequisiti di permission. Resta da verificare il comportamento OEM in esecuzione |
| Hotspot escluso universalmente sopra 4 ms / jitter 3× | Non adottato come gate universale: il break-even dipende dal job, dal target e dalla baseline. Nessuna misura dei dispositivi supporta quella soglia assoluta |
| Soglie rigide 48/54 GiB sul Mac e tempi di wake radio precisi | Non usate come dati osservati; memoria allocabile e tempi devono essere misurati |
| Harmony non qualificabile senza SDK/device | Accolto: sorgente candidato, nessun HAP o compatibilità dichiarata come verificata |

Restano mancanti la revisione finale GLM Max, un controllo indipendente del codice, l'installazione/firma fisica iOS/Harmony e le misure sui cinque telefoni. La compilazione e i test di protocollo non chiudono questi punti.
