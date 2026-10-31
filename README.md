# NodeLift

Progetto per usare smartphone e tablet come nodi locali di inferenza LLM, con future integrazioni per LM Studio e client compatibili con Ollama/OpenAI. Nome scelto dall'utente: **NodeLift**; la directory di lavoro conserva il nome storico ExpandMyHW.

**Stato al 31 ottobre 2026: prima companion di qualificazione 0.1.** Host locale e companion Android/iOS implementati e compilati; client HarmonyOS nativo in forma di sorgente candidato non compilato. **Il motore LLM distribuito e gli adapter Ollama/LM Studio non sono implementati.** Nessuno speedup su telefoni fisici ancora misurato.

- [Avvio, installazione e limiti della companion 0.1](docs/COMPANION_0_1.md)
- [Stato delle build e delle verifiche](artifacts/README.md)
- [Dispositivi dichiarati e rete hotspot](profiles/devices.json)
- [Prima prova fisica: Xiaomi 17 Ultra come hotspot, quattro job completati](research/measurements/2026-10-31-xiaomi-hotspot/REPORT.md). Misure applicative di rete e CPU sintetica; nessun benchmark LLM.

- [Assessment e compatibilità](ASSESSMENT.md)
- [DistAI: analisi del codice, risultati e lessons learned](research/distai/LESSONS_LEARNED.md)
- [Protocollo benchmark e criteri go/no-go proposti](BENCHMARK_PROTOCOL.md)
- [Revisioni GLM/Gemini: stato e correzioni](research/reviews/REVIEW_STATUS.md)
- [Ricalcoli dei dati DistAI](research/distai/evidence-checks.json)

La directory `research/distai/source` conserva 37 file testuali dello snapshot upstream fissato, per rendere verificabile l'analisi. Non include un'installazione né binari eseguiti. La licenza e le attribuzioni upstream sono conservate nei file `LICENSE` e `THIRD_PARTY_NOTICES.md` all'interno della directory source.

Ricalcolo locale dei soli dati pubblicati:

```sh
python3 research/distai/verify_evidence.py
```

Dispositivi dichiarati: Xiaomi 17 Ultra, Oppo indicato come Find X6 Ultra, Oppo Find N5, iPhone 15 Pro Max, Huawei Pura 70 Ultra con HarmonyOS NEXT 7. Rete attuale hotspot. Identità hardware, memoria utilizzabile e prestazioni vanno rilevate sui dispositivi. Gemini 4 High ha completato il riesame del disegno; GLM 5.3 Max resta indisponibile per capacità. Nessuna scelta finale del motore di inferenza prima delle prove discriminanti.
