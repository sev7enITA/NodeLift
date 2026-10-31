# DistAI: evidenze, limiti e lezioni per ExpandMyHW

Assessment del 31 ottobre 2026. **Nessun benchmark hardware di ExpandMyHW è stato eseguito.** Questo documento distingue codice ispezionato, risultati pubblicati dall'autore, ricalcoli nostri e ipotesi da verificare. Non è una certificazione del repository né una replica indipendente delle sue prestazioni.

## Verdetto

DistAI dimostra un prototipo concreto di inferenza distribuita Android/PC: discovery, caricamento, suddivisione dei layer, esecuzione e API compatibile OpenAI. Il suo risultato più istruttivo è negativo: **sommare memoria mediante una pipeline di layer non somma la velocità della singola conversazione**. Il progetto lo dichiara apertamente. Il nostro obiettivo prioritario, accelerare una chat rispetto al computer ottimizzato, richiede quindi un esperimento diverso e una baseline più esigente.

La lezione non è «Wi-Fi impossibile» o «telefoni inutili». È che la scelta deve dipendere dal lavoro realmente delegato, dal percorso critico, dall'hardware e dalla rete misurati. Uno scheduler deve poter lasciare tutti i telefoni inattivi quando non aiutano.

## Perimetro e riproducibilità dell'analisi

- Repository: [alex8819/DistAi](https://github.com/alex8819/DistAi).
- Snapshot: [b1c17109498e87b3db99f8f23648d84483b68bb9](https://github.com/alex8819/DistAi/tree/b1c17109498e87b3db99f8f23648d84483b68bb9), ultimo commit osservato del 16 ottobre 2026. La cronologia acquisita contiene quattro commit, tutti di quel giorno: non prova una lunga storia di manutenzione.
- Acquisiti 37 file testuali mirati, licenza MIT inclusa. Non è un clone integrale, né un audit completo di sicurezza. Nessun APK, binario o script di inferenza upstream è stato eseguito.
- Ogni file acquisito corrisponde al blob Git nello snapshot. [provenance.json](provenance.json) registra albero e commit; [source-manifest.json](source-manifest.json) contiene gli SHA-256 dei file.
- Letti tre JSONL: 17 righe di qualità, 89 di ottimizzazione, 27 di prefill. Queste **133 righe non equivalgono a 133 repliche controllate**: configurazioni differenti, errori e misure annidate. Quattordici righe di ottimizzazione riportano un campo errore non vuoto.
- [verify_evidence.py](verify_evidence.py) legge dati e definizioni letterali via AST senza eseguire codice upstream. Rigenera [evidence-checks.json](evidence-checks.json), non misura un LLM.

Ripetere dalla radice del progetto:

```sh
python3 research/distai/verify_evidence.py
```

## 1. Il risultato di capacità è reale nel prototipo, il guadagno single-user non c'è

L'architettura usa `llama-server` coordinatore e worker `ggml-rpc-server` che mantengono gruppi di layer. I pesi vengono trasferiti al caricamento; i layer remoti eseguono il calcolo e scambiano attivazioni. Non è RAM remota coerente che diventa memoria del Mac. Il README riporta un 30B a **7,0 token/s sul PC contro 3,9 distribuito**, e circa 2 token/s per un 7B PC+telefono. Sono risultati dell'autore, non misure nostre.

Per una pipeline senza sovrapposizione utile sul singolo token:

`T_token ≈ somma(T_stadio_i) + somma(T_trasferimento_i + T_sincronizzazione_i)`.

Se tutti i layer stanno sull'host e ciascuno è più veloce lì, trasferirne alcuni a nodi più lenti non migliora il decode. Questa conclusione riguarda quelle ipotesi; non dimostra l'impossibilità di ogni forma di inferenza distribuita, speculation o parallelismo intra-layer.

**Da superare:** il primo risultato di ExpandMyHW deve confrontare la stessa chat con lo stesso target e una configurazione host ottimizzata. «Modello più grande caricabile» e «più utenti serviti» sono risultati separati.

Fonte: [README fissato](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/README.md).

## 2. Il 3× è throughput di una coda, e dipende dalla baseline

Le ultime tre righe di `results-codeeval.jsonl` riportano:

| Configurazione pubblicata | Tempo di 22 task | Task superati |
|---|---:|---:|
| PC sequenziale | 202,7 s | 20/22 |
| PC con 4 slot | 106,4 s | 20/22 |
| PC 4 + Xiaomi 4 + Huawei 1 slot | 67,7 s | 20/22 |

Ricalcolo: `202,7 / 67,7 = 2,994×`, ma `106,4 / 67,7 = 1,572×`. Il cluster riduce del **36,37%** il tempo della coda rispetto al PC con batching. È un risultato interessante; **non è 3× sulla stessa baseline ottimizzata e non è 3× per una singola chat**. È pubblicato un batch per configurazione, senza intervallo di confidenza.

Il campo `tok_s` dello script è una media aritmetica delle velocità delle richieste, non il totale dei token emessi diviso il tempo della coda. Non va etichettato throughput aggregato del sistema.

**Da superare:** baseline host con batching e speculation ottimizzati; latenza individuale distinta dalla capacità aggregata; token totali/secondi di parete; distribuzioni e repliche, non un solo numero favorevole.

Fonti: [dati](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/results-codeeval.jsonl), [script](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/codeeval.py).

## 3. Prefill migliorato: misure utili, turno completo estrapolato

Per il 7B Q4_K_M con 14 layer sul PC e 14 sul Samsung, patch spenta/accesa:

- Prefill di 2048 token: **312,093 → 169,411 secondi** nei dati pubblicati.
- Decode al contesto lungo: **1,91 → 1,89 token/s**, quindi nessun miglioramento del decode in quel confronto.
- Le generazioni osservate sono da **64 token**.
- Il riepilogo **445 → 305 secondi** proietta un turno da 300 token, usando la media del decode a contesto corto e lungo. Il nostro ricalcolo replica 445,438 e 304,696 secondi.
- Usando invece il decode del contesto lungo si ottengono circa 469,161 e 328,141 secondi: **anche questi sono stime**, non nuove misure.

Il miglioramento del prefill resta consistente nel dato pubblicato. L'errore da evitare è presentare la proiezione come una conversazione interamente misurata, oppure trasferire il guadagno di prefill ai token/s di decode.

Fonti: [prefillbench.py, righe 44–50](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/prefillbench.py#L44), [JSONL](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/results-prefill.jsonl).

## 4. Wi-Fi, USB e risparmio energetico: misurare il percorso completo

Le note riportano su quelle configurazioni Wi-Fi 5 GHz circa 1,4–2 MB/s, ADB fino a 237 MB/s in una direzione e circa 35 nell'altra, tethering USB circa 29,7/40,4 MB/s con 1,2–1,6 ms di RTT. Sono dispositivi e stack specifici, non limiti universali di Wi-Fi o USB. ADB forwarding, rete USB e una copia di file non sono lo stesso test.

Un'osservazione particolarmente utile: a radio inattiva la latenza riportata sale a media 205 ms/massimo 539 ms; con traffico bidirezionale periodico scende a circa 5,6/7 ms. `Keepalive.kt` invia un byte ogni 100 ms e usa una scadenza dei peer di 30 secondi. Tenere radio e CPU svegli costa energia e può aumentare la temperatura; il miglioramento deve essere misurato a regime con quel costo incluso.

**Da superare:** confronto Wi-Fi/USB/Ethernet sul medesimo telefono, dimensioni reali dei messaggi, due direzioni, rete sotto carico e a riposo, p50/p95/p99, termica e joule per risposta. Un buon Wi-Fi può battere una porta USB 2.0 in banda; il cavo può vincere in latenza e prevedibilità. Il connettore USB-C non garantisce USB 3, Thunderbolt o networking supportato dall'OS.

Fonti: [NOTES](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/NOTES.md), [Keepalive.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/Keepalive.kt).

## 5. Lo scheduler è già selettivo, ma il modello di costo è fragile

`SplitPlan.kt` seleziona sottoinsiemi di nodi, privilegia quelli veloci e può escluderne alcuni. Non possiamo presentare questa idea come nuova. Tuttavia:

- RAM Android disponibile moltiplicata per 0,5 sui worker e 0,6 sul coordinatore; riserve fisse di 400 MiB e 200 MiB per calcolo. Sono euristiche empiriche, non contratti di memoria dei sistemi operativi.
- Se mancano le velocità, fallback proporzionale alla memoria: utile per far entrare un modello, insufficiente per promettere accelerazione.
- Costo stimato da byte medi dei layer/banda effettiva e RTT, più **10 ms fissi per nodo remoto**. Le dimensioni archiviate non descrivono da sole i byte attivi di un MoE, operatori e kernel, KV, contesto, trasferimenti e stato termico.
- `RpcBench.kt` usa matvec Q4_0 sintetici e seleziona minimi: minimo di cinque RTT e migliori tempi del grafo. È una calibrazione di picco, non un predittore della latenza sostenuta p95.
- La variabile di banda esprime banda effettiva di calcolo/memoria del benchmark; non è la banda Wi-Fi.

**Da superare:** profili per modello/backend/fase/contesto, tempi reali dei blocchi, pressione memoria, riserva adattiva e pressione termica. Validare errore di previsione fuori dal campione; margine di sicurezza e isteresi per non migrare continuamente. In modalità velocità, profilo mancante significa «calibrare o restare locale», non allocare alla cieca.

Fonti: [SplitPlan.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/SplitPlan.kt), [RpcBench.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/RpcBench.kt).

## 6. Le ottimizzazioni già fatte e quelle che cambiano il problema

DistAI mantiene embedding/output sul coordinatore, evitando il ritorno di un intero vocabolario di logits per token; documenta repacking, threadpool persistente, affinità ai core veloci e binari ARM differenziati. Sono lezioni da riusare, verificando prima ciò che il backend upstream offre già.

La build PC predefinita disabilita Metal, ma **`--gpu` abilita Metal su macOS**. Un confronto tra il nostro Metal e il suo default CPU non dimostrerebbe un vantaggio della nuova architettura. Anche il verdetto sulle vecchie GPU integrate Intel non si trasferisce alla memoria unificata Apple Silicon.

La riduzione di `expert_used_count` da 8 a 6 modifica il calcolo del modello. Il punteggio uguale 21/22 di due configurazioni non dimostra qualità invariata. Con 4 esperti i dati riportano 14/22 e con 5, 19/22: lo stesso repository mostra sensibilità a questa modifica. Dobbiamo tenere invariati routing/numero di esperti nel confronto principale; varianti approssimate meritano un esperimento qualità/prestazioni distinto.

Fonti: [NodeService.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/NodeService.kt), [build-pc.py](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/native/build-pc.py), [patch](https://github.com/alex8819/DistAi/tree/b1c17109498e87b3db99f8f23648d84483b68bb9/native/patches).

## 7. Speculation: non ripetere la delega per singolo token

Il commento in `NodeService.kt` riporta draft su Huawei via RPC a 2,24 token/s contro 4,5 senza draft: ogni token proposto paga il percorso remoto. Il codice sceglie quindi un draft locale. `Speculative.kt` calibra e può disattivarlo se non aiuta: anche l'abilitazione condizionata esiste già.

Questo esperimento negativo **non è equivalente** a un telefono che mantiene un piccolo modello completo, genera autonomamente un blocco e lo propone al target sul Mac. Questa seconda architettura è una candidata da testare, non una soluzione dimostrata e non una novità assoluta: esistono PipeInfer, PipeSpec e altra ricerca su speculation asincrona/distribuita.

Per un ciclo sequenziale, una prima condizione è:

`(T_draft_blocco + T_rete + T_verifica + T_rollback) / E[token_accettati_e_committati] < T_token_baseline`.

Con sovrapposizione, il numeratore deve venire dalla linea temporale reale del percorso critico, includendo code, calcolo scartato e riallineamenti. Non basta sostituire arbitrariamente una somma con un massimo. La baseline è **il migliore draft locale**, anche asincrono, oltre al target solo. Non assumere un tempo di verifica costante: dipende da k, contesto e GPU.

Prima prova greedy con equivalenza dei token; poi sampling esatto. Per preservare la distribuzione del target non basta inviare gli ID dei token: servono acceptance/rejection corretti e la distribuzione draft necessaria al campionamento residuo, o un protocollo equivalente dimostrato. Quel traffico può cancellare parte del vantaggio.

La selezione draft in DistAI confronta famiglia tokenizer e conteggio vocabolario con tolleranza 128, non l'identità completa token-ID/normalizzazione/special token. Non è una prova di incompatibilità osservata, ma non basta come certificazione preventiva. Il nostro manifest deve verificarla e gestire esplicitamente le incompatibilità.

Fonti: [Speculative.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/Speculative.kt), [Gguf.kt](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/app/src/main/java/com/distai/app/Gguf.kt), [PipeInfer](https://arxiv.org/abs/2407.11798), [PipeSpec](https://aclanthology.org/2025.findings-acl.669/).

## 8. Diffusione: ramo sperimentale, non scorciatoia universale

Le patch BD3LM sono separate e non applicate alla build standard. Il driver `d3_rpc.py` usa per default **Stable-DiffCoder-8B-Instruct.Q4_K_M.gguf**: non è corretto accusarlo, senza ulteriori prove, di applicare semplicemente attenzione non causale a normali pesi autoregressivi.

Restano verifiche decisive: revisione/hash del modello e obiettivo di training compatibile, semantica dei mask token e generazione completa. Lo script `bd3eval.py` prevede `results-dllm.jsonl`, ma questo file non compare nell'albero pubblicato acquisito. I numeri riassunti nelle note non sono accompagnati lì da quella traccia dettagliata. Un microbenchmark `llama-bench` di prefill a blocchi non dimostra token utili corretti al secondo di una risposta completa.

**Da superare:** benchmark separato per modelli nativamente diffusion, qualità comparabile e output conservati. Nessuna promessa di rendere parallelo un LLM causale arbitrario cambiando la maschera.

Fonti: [patch sperimentali](https://github.com/alex8819/DistAi/tree/b1c17109498e87b3db99f8f23648d84483b68bb9/native/patches-sperimentali), [d3_rpc.py](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/d3_rpc.py), [bd3eval.py](https://github.com/alex8819/DistAi/blob/b1c17109498e87b3db99f8f23648d84483b68bb9/tools/bd3eval.py).

## 9. Qualità, affidabilità e confini operativi

I 22 task di coding sono utili come smoke test, non come valutazione generale. Assert ridotti, un campione di generazione e nessun corpus esteso o intervallo statistico non giustificano «nessuna perdita di qualità». I JSONL conservano esiti, non tutte le risposte: non è possibile riesaminarne retroattivamente ogni errore. Un iniziale sospetto sul test `group_anagrams` è stato verificato e **ritirato: l'oracolo è corretto**, come registra il nostro controllo.

Il test esegue Python generato con `python3 -I` e timeout: isolamento dell'import non equivale a una sandbox di sicurezza. Un nostro benchmark di codice dovrà eseguire gli output in un ambiente realmente isolato, con limiti di rete, filesystem e risorse.

RPC senza autenticazione/cifratura e server di gestione su interfacce di rete richiedono un confine di fiducia esplicito. Per il prodotto: pairing, identità nodo, autorizzazione dei job, trasporto protetto, limiti di allocazione, modelli verificati e nessuna esposizione Internet automatica. Non è stato eseguito un penetration test.

Le istruzioni DistAI indicano riavvio del job in caso di cavo scollegato; caching dei pesi non equivale a ripresa della KV/sessione. Il nostro runtime deve definire cosa succede quando un telefono viene bloccato, risponde a una chiamata, va in pressione termica o sparisce. Il fallback può richiedere replay del contesto; costo e perdita di lavoro vanno conteggiati.

Il pin documentato di llama.cpp è `69f201a`; protocollo e patch devono combaciare. Una futura build deve bloccare commit completo e hash delle patch/modelli, non dipendere dal checkout eventualmente presente o da un URL `main` mutevole.

## 10. Matrice delle lezioni e prova richiesta

| Lezione DistAI | Scelta proposta ExpandMyHW | Prova per dire «superato» |
|---|---|---|
| Layer seriali rallentano la chat | Separare modalità velocità e capacità | Speedup stesso target contro host ottimizzato, oppure claim solo capacità |
| Draft RPC per-token troppo costoso | Draft autonomo a blocchi; overlap misurato | Battere draft locale ottimizzato, con equivalenza e costo di rete incluso |
| Vecchia rete/risparmio energetico domina | Selezione trasporto basata sul job | p95 e tempo risposta sostenuti migliori; costo energia pubblicato |
| Modello costo sintetico e fisso | Profili per fase/modello e stato reale | Predizioni validate fuori campione; nodi inutili esclusi |
| 3× dipende dal riferimento | Baseline forti e dati grezzi completi | Risultati con intervalli di confidenza e definizioni pubbliche |
| Test qualità piccolo | Equivalenza + suite ampia separata | Nessuna modifica nascosta del target; margini qualità preregistrati |
| Solo Android mobile verificato nel repo | Worker nativi Android/iOS con capacità dichiarate | Test fisici su entrambi gli OS, memoria/termica/lifecycle inclusi |
| Crash/disconnessione richiede ripartenza | Drain, cancellazione, fallback e replay espliciti | Fault injection con tempi di recupero e nessuna risposta corrotta |

**Decisione:** procedere solo con microesperimenti discriminanti e benchmark preregistrati, prima del plugin completo. Non è ancora dimostrato che telefoni non identificati possano accelerare il M3 Max 64 GiB osservato. È un'ipotesi da falsificare rapidamente, non un risultato da promettere.
