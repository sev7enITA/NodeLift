"""Recalculate the first physical NodeLift qualification from retained raw samples."""
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FOLDER = Path(__file__).resolve().parent
ROOT = FOLDER.parents[2]


def read(name):
    return json.loads((FOLDER / name).read_text())


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * fraction) - 1]


results = []
for record in read("jobs.json"):
    filename = record.get("record_file", record["kind"] + ".json")
    snapshot = read(filename)
    job = next(j for j in snapshot["jobs"] if j["id"] == record["job_id"])
    assert job["state"] == "completed", "Do not silently exclude failed jobs"
    samples = job["result"]["samples"]
    result = {
        "job_id": job["id"], "kind": job["kind"], "raw_file": filename,
        "started_rome": datetime.fromtimestamp(job["started"], ZoneInfo("Europe/Rome")).isoformat(),
        "elapsed_host_seconds": job["finished"] - job["started"],
        "sample_count": len(samples), "rtt": [], "transfers": [],
    }
    for pace in sorted({s.get("pace_ms", 0) for s in samples if s["kind"] == "rtt"}):
        rows = [s for s in samples if s["kind"] == "rtt" and s.get("pace_ms", 0) == pace]
        values = [s["ms"] for s in rows]
        result["rtt"].append({
            "requested_pause_ms": pace, "n": len(values),
            "p50_ms": percentile(values, .5), "p95_ms": percentile(values, .95),
            "max_ms": max(values), "over_20_ms": sum(v > 20 for v in values),
            "connections": len({s["connection_id"] for s in rows}),
        })
    for kind in ("download", "upload"):
        for size in (16384, 1048576):
            rows = [s for s in samples if s["kind"] == kind and s["bytes"] == size]
            if rows:
                result["transfers"].append({
                    "direction": "Mac → Xiaomi" if kind == "download" else "Xiaomi → Mac",
                    "bytes_per_request": size, "n": len(rows),
                    "aggregate_MB_per_second": sum(s["bytes"] for s in rows) / sum(s["ms"] for s in rows) / 1000,
                })
    if job["kind"] == "cpu":
        result["cpu"] = samples
    results.append(result)

(FOLDER / "summary.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
caps = read("before.json")["nodes"][0]["capabilities"]
lines = [
    "# NodeLift — prima prova fisica Xiaomi/hotspot",
    "", "31 ottobre 2026. Diagnostica esplorativa del protocollo: nessuna inferenza LLM eseguita.", "",
    "## Configurazione osservata", "",
    "L'utente conferma che lo Xiaomi 17 Ultra fornisce l'hotspot al Mac M3 Max. "
    "La companion si è associata, ha inviato heartbeat e ha eseguito i job richiesti dal Mac.", "",
    f"Telemetria dichiarata dall'app: **{caps['model']}**, **{caps['os']}**, "
    f"{caps['physical_memory_bytes']/2**30:.2f} GiB di RAM fisica e "
    f"{caps['available_memory_bytes']/2**30:.2f} GiB disponibili al sistema nella lettura iniziale. "
    "Non è un budget di memoria allocabile verificato per un LLM. Stato termico nominale nelle letture conservate; "
    "nessuna prova termica prolungata. Identità commerciale e hash dell'APK installato non attestati indipendentemente.", "",
    "Il campo trasporto dell'app riporta «altro / non rilevato»: legge la rete predefinita del telefono, "
    "che non identifica necessariamente l'interfaccia hotspot usata verso il Mac. "
    "La topologia deriva quindi dalla conferma dell'utente, non da quel campo.", "",
    "## Latenza HTTPS applicativa", "",
    "RTT misurato sul telefono con orologio monotono, risposta da 64 byte, warmup escluso. "
    "Le pause richieste sono esterne al tempo RTT. Percentili empirici nearest-rank; "
    "non sono ping, latenza unidirezionale o tempi per token.", "",
    "| Prova | Pausa richiesta | Campioni | p50 ms | p95 ms | Massimo ms | Oltre 20 ms | Connessioni |",
    "|---|---:|---:|---:|---:|---:|---:|---:|",
]
labels = {"network.json": "Rapida", "network_paced.json": "Con pause", "network_paced_repeat.json": "Replica con pause"}
for run in results:
    for row in run["rtt"]:
        lines.append(f"| {labels[run['raw_file']]} | {row['requested_pause_ms']} ms | {row['n']} | "
                     f"{row['p50_ms']:.2f} | {row['p95_ms']:.2f} | {row['max_ms']:.2f} | "
                     f"{row['over_20_ms']} | {row['connections']} |")
lines += ["", "## Trasferimenti", "",
          "Goodput = byte utili / somma dei tempi applicativi. MB decimali; 1 MiB = 1.048.576 byte. "
          "Quattro richieste per dimensione e direzione: diagnostica breve, non banda sostenuta o PHY.", "",
          "| Prova | Direzione | Payload | MB/s |", "|---|---|---:|---:|"]
for run in results:
    for row in run["transfers"]:
        lines.append(f"| {labels[run['raw_file']]} | {row['direction']} | "
                     f"{row['bytes_per_request']//1024} KiB | {row['aggregate_MB_per_second']:.2f} |")
cpu = next(r for r in results if "cpu" in r)["cpu"][0]
lines += ["", "## CPU e limiti", "",
          f"La prova CPU ha completato **{cpu['iterations']} iterazioni in {cpu['ms']:.2f} ms**. "
          "È un matvec FP32 256×256 Kotlin/JVM a singolo thread, principalmente in cache. "
          "Non misura GPU/NPU, banda DRAM o token/s e non viene confrontato con un kernel host differente.", "",
          "Le prove hanno un ordine fisso 0/30/60 ms. La replica è stata aggiunta dopo aver osservato "
          "la coda della latenza nella prima prova: è esplorativa, nella stessa sessione, "
          "e non costituisce una conferma indipendente preregistrata. Non attribuire causalmente "
          "le differenze alle pause o al risparmio energetico senza controllare ordine, interferenze "
          "e carico concorrente. Il riuso della connessione è osservabile dagli ID del server; "
          "non esclude altri costi di scheduling, radio, TLS e copie.", "",
          "La mediana da sola non basta a dimensionare il protocollo. Servono altre sessioni, "
          "ordine delle pause randomizzato, trasporti alternativi, misure sostenute e soprattutto "
          "un workload LLM reale contro il Mac ottimizzato. Nessun gate di speedup è stato superato "
          "o fallito da questa diagnostica. Non derivare uno speedup dalla somma della RAM.", "",
          "Nella companion Android 0.1 il riepilogo «Ultima misura» della prova con pause usa solo "
          "i primi 32 RTT: per confrontare i gruppi usare questa analisi o la dashboard, che usa "
          "tutti i campioni separati per pausa. Correzione del riepilogo mobile ancora da distribuire.", "",
          "## Riproducibilità", "",
          "Eseguire `python3 analyze.py` in questa directory. I JSON originali contengono i campioni; "
          "`conditions.json` registra condizioni e aspetti ignoti; `jobs.json` identifica le prove. "
          "`summary.json` è derivato. `evidence-manifest.json` conserva hash dei file e dei sorgenti "
          "del protocollo. Non contiene credenziali o inviti di associazione.", ""]
(FOLDER / "REPORT.md").write_text("\n".join(lines))
manifest = read("evidence-manifest.json")
manifest["records"] = [{"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                       for p in sorted(FOLDER.iterdir()) if p.is_file() and p.name != "evidence-manifest.json"]
(FOLDER / "evidence-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(results, indent=2, ensure_ascii=False))
