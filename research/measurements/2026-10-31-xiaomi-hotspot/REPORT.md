# NodeLift — prima prova fisica Xiaomi/hotspot

31 ottobre 2026. Diagnostica esplorativa del protocollo: nessuna inferenza LLM eseguita.

## Configurazione osservata

L'utente conferma che lo Xiaomi 17 Ultra fornisce l'hotspot al Mac M3 Max. La companion si è associata, ha inviato heartbeat e ha eseguito i job richiesti dal Mac.

Telemetria dichiarata dall'app: **Xiaomi 25128PNA1C**, **Android 17 / API 37**, 14.76 GiB di RAM fisica e 4.87 GiB disponibili al sistema nella lettura iniziale. Non è un budget di memoria allocabile verificato per un LLM. Stato termico nominale nelle letture conservate; nessuna prova termica prolungata. Identità commerciale e hash dell'APK installato non attestati indipendentemente.

Il campo trasporto dell'app riporta «altro / non rilevato»: legge la rete predefinita del telefono, che non identifica necessariamente l'interfaccia hotspot usata verso il Mac. La topologia deriva quindi dalla conferma dell'utente, non da quel campo.

## Latenza HTTPS applicativa

RTT misurato sul telefono con orologio monotono, risposta da 64 byte, warmup escluso. Le pause richieste sono esterne al tempo RTT. Percentili empirici nearest-rank; non sono ping, latenza unidirezionale o tempi per token.

| Prova | Pausa richiesta | Campioni | p50 ms | p95 ms | Massimo ms | Oltre 20 ms | Connessioni |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rapida | 0 ms | 32 | 6.28 | 8.25 | 8.79 | 0 | 1 |
| Con pause | 0 ms | 200 | 7.68 | 11.30 | 90.55 | 1 | 1 |
| Con pause | 30 ms | 200 | 8.30 | 14.24 | 95.03 | 8 | 1 |
| Con pause | 60 ms | 200 | 8.91 | 79.88 | 89.19 | 15 | 1 |
| Replica con pause | 0 ms | 200 | 6.21 | 8.27 | 94.70 | 2 | 1 |
| Replica con pause | 30 ms | 200 | 7.80 | 11.77 | 98.56 | 8 | 1 |
| Replica con pause | 60 ms | 200 | 8.80 | 68.37 | 97.96 | 14 | 1 |

## Trasferimenti

Goodput = byte utili / somma dei tempi applicativi. MB decimali; 1 MiB = 1.048.576 byte. Quattro richieste per dimensione e direzione: diagnostica breve, non banda sostenuta o PHY.

| Prova | Direzione | Payload | MB/s |
|---|---|---:|---:|
| Rapida | Mac → Xiaomi | 16 KiB | 2.33 |
| Rapida | Mac → Xiaomi | 1024 KiB | 36.11 |
| Rapida | Xiaomi → Mac | 16 KiB | 1.19 |
| Rapida | Xiaomi → Mac | 1024 KiB | 19.89 |
| Con pause | Mac → Xiaomi | 16 KiB | 2.37 |
| Con pause | Mac → Xiaomi | 1024 KiB | 42.97 |
| Con pause | Xiaomi → Mac | 16 KiB | 1.14 |
| Con pause | Xiaomi → Mac | 1024 KiB | 37.12 |
| Replica con pause | Mac → Xiaomi | 16 KiB | 2.34 |
| Replica con pause | Mac → Xiaomi | 1024 KiB | 42.15 |
| Replica con pause | Xiaomi → Mac | 16 KiB | 1.08 |
| Replica con pause | Xiaomi → Mac | 1024 KiB | 36.74 |

## CPU e limiti

La prova CPU ha completato **14115 iterazioni in 1500.05 ms**. È un matvec FP32 256×256 Kotlin/JVM a singolo thread, principalmente in cache. Non misura GPU/NPU, banda DRAM o token/s e non viene confrontato con un kernel host differente.

Le prove hanno un ordine fisso 0/30/60 ms. La replica è stata aggiunta dopo aver osservato la coda della latenza nella prima prova: è esplorativa, nella stessa sessione, e non costituisce una conferma indipendente preregistrata. Non attribuire causalmente le differenze alle pause o al risparmio energetico senza controllare ordine, interferenze e carico concorrente. Il riuso della connessione è osservabile dagli ID del server; non esclude altri costi di scheduling, radio, TLS e copie.

La mediana da sola non basta a dimensionare il protocollo. Servono altre sessioni, ordine delle pause randomizzato, trasporti alternativi, misure sostenute e soprattutto un workload LLM reale contro il Mac ottimizzato. Nessun gate di speedup è stato superato o fallito da questa diagnostica. Non derivare uno speedup dalla somma della RAM.

Nella companion Android 0.1 il riepilogo «Ultima misura» della prova con pause usa solo i primi 32 RTT: per confrontare i gruppi usare questa analisi o la dashboard, che usa tutti i campioni separati per pausa. Correzione del riepilogo mobile ancora da distribuire.

## Riproducibilità

Eseguire `python3 analyze.py` in questa directory. I JSON originali contengono i campioni; `conditions.json` registra condizioni e aspetti ignoti; `jobs.json` identifica le prove. `summary.json` è derivato. `evidence-manifest.json` conserva hash dei file e dei sorgenti del protocollo. Non contiene credenziali o inviti di associazione.
