# NodeLift — metodo del confronto / comparison methodology

Data di congelamento delle fonti: **31 ottobre 2026**. Versione del dataset: **1**. Curatore: Fabrizio Degni / progetto NodeLift.

## Ambito
55 schede selezionate: 16 sistemi distribuiti, 17 runtime, 6 piattaforme di serving, 5 applicazioni mobili, 2 riferimenti locali e 9 lavori di ricerca. La matrice usa criteri assoluti e uniformi, non un punteggio competitivo arbitrario. È un censimento ampio, non la promessa di includere ogni progetto esistente o di certificare un vincitore universale.

La ricerca parte da DistAI e dalla bibliografia già verificata di NodeLift, estende i collegamenti ai progetti correlati e ricerca implementazioni mobili/distribuite, runtime nativi e ricerca recente. Sono inclusi progetti occidentali, asiatici e internazionali. Sono esclusi frontend di sola chat duplicativi, cataloghi generici di modelli, reti di solo training e semplici fork senza differenze rilevanti per il problema. Una fonte accessibile e un legame tecnico pertinente sono requisiti minimi.

**Non tutte le righe sono alternative dirette.** Un kernel, una app, un paper e una piattaforma server non sono intercambiabili. La categoria resta visibile nei filtri. Gli abstract o README sono dichiarazioni degli autori: non dimostrano, da soli, che un percorso sia riproducibile sui nostri telefoni.

## Geografia senza supposizioni
Il campo ecosystem indica la provenienza documentata dell'organizzazione o collaborazione: western, asia, international, unverified. Non deduciamo nazionalità o etnia da nomi, alfabeti o pseudonimi. Un progetto multinazionale non è forzato in una classificazione binaria. La provenienza non assegna alcun vantaggio tecnico.

## Dimensioni del confronto
Ogni scheda riporta nome, categoria, provenienza, stato, licenza, architettura, host, Android, iOS, effettivo ruolo di calcolo mobile, capacità oltre la memoria di un singolo dispositivo, effetto sulla singola chat, trasporto, API/integrazioni, sicurezza, livello di evidenza, limiti, lezione per NodeLift, revisione, data di verifica e fonti.

- **Mobile compute:** inferenza sul dispositivo, diversa da un telefono che visualizza risposte remote. Un SDK disponibile non equivale a una companion qualificata.
- **Capacity:** pesi divisi tra dispositivi, diversa dall'uso di disco/RAM locale, dal routing di intere richieste e dall'esecuzione di un piccolo draft remoto.
- **Single chat:** latenza totale e inter-token di una sola generazione. Non si ricava dal throughput aggregato, dal prefill, da un kernel isolato o dalla dimensione del modello che entra in memoria.
- **Android/iOS:** distingue codice, build, applicazione distribuita, dimostrazione fisica e qualificazione svolta da NodeLift. Un tag di filtro indica pertinenza documentata, non una certificazione.
- **Transport:** percorso effettivo documentato. Wi-Fi, cavo USB, USB networking, Ethernet e RDMA non sono sinonimi; un connettore non garantisce una velocità IP.
- **API:** compatibilità osservata o documentata, distinta da un plugin interno ufficiale. NodeLift 0.2.1 non è un backend interno di Ollama; il suo handler SDK LM Studio è stato provato, il runtime completo del plugin no.
- **Security:** meccanismi dichiarati o limiti espliciti. Non abbiamo eseguito un penetration test dei concorrenti. “Locale” non significa automaticamente cifrato o sicuro contro un peer.
- **License:** identificazione informativa della licenza alla revisione esaminata; dipendenze, pesi e distribuzioni possono avere termini diversi. Nessuna valutazione legale di compatibilità. NOASSERTION di GitHub non è prova di assenza di licenza.

## Evidenza e numeri
Le prestazioni esterne sono attribuite agli autori; non sono state riprodotte sul testbed NodeLift. È esplicita la differenza tra hardware fisico, emulazione, simulazione, analisi teorica, build e ispezione documentale.

Non confrontiamo direttamente token/s ottenuti con modelli, prompt, quantizzazioni, hardware o metriche diversi. Non convertiamo “fino a” in prestazione tipica. Non consideriamo stelle GitHub, download o marketing come prova di correttezza o maturità.

Per NodeLift il riferimento pubblico è la release sperimentale 0.2.1. I 60 run congelati sono locali su M3 Max, Qwen2.5 1.5B target/0.5B draft, massimo 64 token, sei prompt e due ripetizioni per braccio. I 48 confronti appaiati concordano nei token, ma le mediane di speedup restano 0.425–0.719×: **nessuna accelerazione dimostrata**. Il test TLS con un nodo emulato e il pilot rete sullo Xiaomi sono evidenze separate. Nessuna velocità di inferenza distribuita su telefono fisico è ancora qualificata.

## Revisioni e alias
45 repository sono registrati in source-inventory.json con commit Git immutabile; 44 sono schede autonome. Pooled è il progetto già denominato SwarmLLM: il fork Pendia/SwarmLLM-P2P-AI è una fonte storica della stessa famiglia, non un concorrente aggiuntivo. Nakshatra ha genealogia Git Petals ma documenta una propria architettura attuale e viene descritto separatamente. L'Ollama Cluster fork è distinto dall'upstream. PowerInfer-2 è una ricerca diversa dal codice desktop PowerInfer. LiteRT-LM/Gallery e MLC/WebLLM condividono famiglie ma coprono livelli differenti.

Le revisioni documentali dei paper sono esplicite; pagine web senza versione restano soggette a cambiamenti. Licenze custom o incongruenze documentali sono segnalate, non risolte per supposizione. Dati mancanti significano **non documentato nelle fonti esaminate**, non impossibile o certamente assente.

## Riproducibilità e correzioni
JSON è la fonte canonica delle 55 schede; CSV e Markdown sono esportazioni degli stessi campi. Le descrizioni tecniche restano in inglese in entrambe le modalità della pagina per evitare due inventari divergenti. La narrazione, le etichette e i filtri sono bilingui. Fonti e commit sono in ogni scheda. Il repository contiene l'inventario e il generatore degli export.

Segnalare correzioni con fonte primaria, revisione, dispositivo e percorso esatto tramite [GitHub Issues](https://github.com/sev7enITA/NodeLift/issues). Una correzione documentale non sostituisce un benchmark.

## English summary
This is a dated, broad, non-exhaustive comparison of 55 selected entries, including adjacent runtimes and research, not 55 interchangeable competitors. Uniform descriptive criteria replace a fabricated winner score. Organization/collaboration provenance is not inferred from personal names. “Not established” means missing evidence in reviewed sources, not impossible support. Upstream claims, physical hardware, simulations, builds and NodeLift-replicated measurements are kept separate. Different models/hardware/timing paths cannot form a fair tokens-per-second league table. NodeLift's current controls show slower local drafting and no demonstrated physical-phone speedup. Canonical English entries are exported identically to JSON, CSV and Markdown; page narrative and controls are bilingual.
