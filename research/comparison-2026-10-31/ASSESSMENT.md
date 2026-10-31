# NodeLift — confronto globale e conseguenze progettuali
**Fonti congelate al 31 ottobre 2026 · 55 schede · release NodeLift 0.2.1 sperimentale**

La possibilità di riutilizzare telefoni per inferenza distribuita è già dimostrata da altri progetti. Il lavoro utile per NodeLift consiste nel rendere misurabile e affidabile la scelta di quando coinvolgerli, con integrazioni e recupero dagli errori verificabili. Non abbiamo evidenza per dichiarare NodeLift il primo, il più veloce o superiore a tutte le alternative.

La [matrice dettagliata](../../site/NodeLift/data/comparison.md) e i relativi [JSON](../../site/NodeLift/data/comparison.json), [CSV](../../site/NodeLift/data/comparison.csv) e [metodo](../../site/NodeLift/data/methodology.md) condividono la stessa fonte. Il sito pubblico previsto è [fabriziodegni.com/NodeLift](https://www.fabriziodegni.com/NodeLift/).

## Risultato del censimento
Il perimetro include 16 sistemi distribuiti, 17 runtime, 6 piattaforme server, 5 app mobili, 2 riferimenti e 9 ricerche. Non sono 55 concorrenti intercambiabili: i runtime possono diventare dipendenze, i paper precedenti scientifici, le app termini di confronto per l'esperienza mobile. Un inventario universalmente completo non è verificabile; questo è un insieme ampio, datato e correggibile con criteri comuni.

Le collaborazioni asiatiche comprendono Alibaba MNN, Tencent ncnn, l'ecosistema Huawei/MindSpore, PaddlePaddle/FastDeploy, KTransformers, PowerInfer e studi come EdgeShard e DiP-SD. Le fonti occidentali e internazionali includono, tra gli altri, llama.cpp, MLX, Qualcomm GenieX, Google LiteRT-LM, ExecuTorch, Petals, LinguaLinked e WISP. Per maintainer indipendenti senza provenienza documentata abbiamo indicato “unverified”, senza inferirla dal nome.

## I riferimenti più vicini
| Famiglia | Cosa dimostra la fonte | Conseguenza per NodeLift |
|---|---|---|
| [PhoneBorg](https://github.com/dzaczek/phoneborg) | Android via ADB/USB, routing e modalità BigBrain con shard; prove fisiche e test emulati distinti. | USB e gestione termica sono confronti necessari; più telefoni non garantiscono più token/s. |
| [InferRing](https://github.com/N1k1tung/infer-ring) | App Apple che combina Mac e iPhone; prefill e decode possono cambiare in direzioni opposte. | iOS compute e cluster misti Apple sono precedenti concreti, non novità NodeLift. |
| [Pooled](https://github.com/Nehanth/pooled) | Browser WebGPU/WebRTC, shard mobili e streaming di esperti; già denominato SwarmLLM. | Il browser riduce l'installazione ma introduce limiti di memoria, compatibilità e lifecycle. |
| [DistAI](https://github.com/alex8819/DistAi) / [prima.cpp](https://github.com/OpenCPIL/prima.cpp) | Offload a nodi eterogenei e pianificazione; capacità e velocità richiedono prove separate. | Il planner deve poter escludere un nodo e considerare disco, compute e comunicazione. |
| [Cake](https://github.com/evilsocket/cake) | Worker su più sistemi, shard e distribuzione automatica dei pesi documentati. | Provisioning e piattaforme miste hanno già precedenti; verificare anche i termini di riuso. |
| [LinguaLinked](https://aclanthology.org/2024.acl-demos.16/) | Partizionamento e load balancing dimostrati su Android fisici. | Confrontare con un vero sistema mobile, non soltanto con un server remoto. |

## Quattro problemi diversi
1. **Capacità:** far entrare pesi e KV cache che non entrano su un dispositivo. Layer sharding, esperti e storage offload sono strategie differenti. NodeLift 0.2.1 non implementa lo sharding del target.
2. **Latenza di una chat:** ridurre tempo al primo token, intervallo fra token e tempo totale. Il draft remoto di NodeLift mira a questo obiettivo, ma il vantaggio non è ancora dimostrato.
3. **Throughput:** completare più richieste con una flotta. Routing, repliche e batching possono aiutare anche quando la singola richiesta rallenta.
4. **Accesso:** usare dal telefono un modello residente altrove. [LM Link](https://lmstudio.ai/docs/lmlink) copre questo caso; non equivale a prestare la RAM del telefono al modello desktop.

Nessun punteggio complessivo sostituisce questi quattro esiti. Un'applicazione può essere ottima in uno e irrilevante in un altro.

## Cosa cambia per il motore
[WISP](https://arxiv.org/html/2601.11652v2), [FlexSpec](https://arxiv.org/html/2601.00644v1), [PipeInfer](https://arxiv.org/abs/2407.11798v2) e [PipeSpec](https://aclanthology.org/2025.findings-acl.669/) rendono insufficienti pretese di novità basate solo su draft adattivo, pipeline, cancellazione o rollback. Sono tecniche da studiare e qualificare. [DiP-SD](https://arxiv.org/html/2604.20919v1) aiuta a formulare l'obiettivo multiutente, ma la sua simulazione non è una prova sullo Xiaomi.

[Speculation at a Distance](https://arxiv.org/html/2606.25091v2) impone il confronto con la speculazione locale quando possibile. Le sue condizioni non vanno trasformate in una soglia universale di RTT o in un'impossibilità assoluta su LAN eterogenee.

Il percorso proposto è:
- Un selettore di utilità confronta host-only, migliore accelerazione locale e draft remoto usando il **tempo completo per token effettivamente confermato**. Deve contare attese, draft rifiutati, verifica, sincronizzazione e recupero.
- La decisione viene prima valutata in osservazione, poi attivata con margine conservativo e isteresi. Il dispositivo non entra nella catena critica solo perché è connesso.
- Un percorso separato di capacità rende esplicito che un modello più grande può diventare eseguibile a prezzo di maggiore latenza. Non va presentato come accelerazione.
- Backend Android CPU, GPU e NPU sono candidati da confrontare con modelli compatibili; compilazione, caricamento e qualità fanno parte del costo.
- Il lifecycle mobile richiede sospensione, revoca, cambio rete, background, temperatura e batteria. Il trasporto autenticato già implementato in NodeLift non sostituisce queste prove.

Questi punti sono **sviluppo e sperimentazione futuri**, non funzioni tutte disponibili nella release.

Per Huawei esiste un riferimento ufficiale utile: la [pagina MindSpore Lite](https://www.mindspore.cn/lite/en) documenta Android/iOS e un Lite Kit integrato in HarmonyOS NEXT. Questo offre una pista nativa da indagare; non dimostra compatibilità con un particolare LLM, con il telefono dell'utente o con NodeLift. Non va confuso con il percorso Termux descritto da altri progetti.

## Benchmark riproducibili da completare
La prima porta di uscita è una companion nativa realmente online e un target grande supportato dal verificatore. Poi:

| Esperimento | Condizioni comuni | Misure e criterio |
|---|---|---|
| Host-only / migliore locale / telefono | Stessi pesi, tokenizer, quantizzazione, prompt, contesto e output budget; ordine randomizzato e warmup dichiarato. | Token effettivi, TTFT, inter-token p50/p95, completamento, correttezza, RAM/KV, swap. |
| Wi-Fi hotspot / access point / USB networking / Ethernet | Percorso IP verificato su ciascun OS; payload realistici; test con inferenza attiva. | RTT distribuito, jitter, throughput bidirezionale, p95 e riconnessioni; non solo velocità nominale. |
| Sessione sostenuta | Stati schermo/alimentazione dichiarati, ripetizioni e raffreddamento controllati. | Deriva prestazioni, stato termico, energia/batteria, fallimenti. |
| Più nodi / più richieste | Stesso carico; baseline locale con batching e code equivalenti. | Goodput entro obiettivo di latenza, equità e lavoro scartato. |
| Fault injection | Caduta nodo, lease scaduta, risposta tardiva, prefix errato, annullamento. | Correttezza, tempo di recupero e assenza di output duplicato. |

Il test candidato dovrebbe dichiarare in anticipo una soglia pratica, per esempio almeno il 10% di miglioramento mediano con intervallo di confidenza favorevole e nessuna regressione p95 inaccettabile. Questo è un **criterio proposto**, non un risultato o una promessa. L'effetto di una modifica si valuta nello stesso esperimento, non confrontando sessioni con carichi diversi.

## Evidenza NodeLift oggi
I [risultati pubblici](../measurements/ENGINE_RESULTS.md) includono 156 run comparativi complessivi, ma solo 60 costituiscono la ripetizione NodeLift congelata 0.2.1. Quel gruppo usa Qwen2.5 1.5B/0.5B su M3 Max: tutte le 48 coppie di output coincidono, mentre lo speedup mediano è inferiore a uno in ogni braccio. Le 36 prove upstream hanno percorsi di timing diversi e non creano una classifica diretta NodeLift/llama.cpp.

Il pilot sullo Xiaomi misura rete e protocollo. Il nodo TLS emulato verifica integrazione e recupero. La build iOS è unsigned. Il kernel benchmark 27B non prova supporto NodeLift per quell'architettura ibrida. Tenere separate queste evidenze rende il progetto valutabile e impedisce di vendere un miglioramento non ancora ottenuto.

## Posizionamento difendibile
La proposta è una flotta locale che spiega **quando un dispositivo aiuta, quanto aiuta e come ripiega quando non aiuta**, con benchmark pubblici e supporto dichiarato per versione. Il valore potenziale è nell'integrazione verificabile e nella qualità delle decisioni, non nella semplice somma nominale della RAM. Riutilizzo dell'hardware è la missione; risparmio energetico, allungamento della vita utile e popolarità GitHub restano risultati da misurare, non claim già dimostrati.
