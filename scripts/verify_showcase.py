#!/usr/bin/env python3
"""Compare anonymously fetched public files with a frozen publication manifest."""
import concurrent.futures
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/showcase"
manifest = json.loads((OUT / "deployment-manifest.json").read_text())
base = manifest["base_url"]
nonce = str(time.time_ns())

def check(item):
    name, expected = item
    request = urllib.request.Request(base + name + "?verify=" + nonce,
                                     headers={"Cache-Control": "no-cache", "User-Agent": "NodeLift-publication-verifier/1"})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read()
            sha = hashlib.sha256(body).hexdigest()
            return {"file": name, "status": response.status, "bytes": len(body), "sha256": sha,
                    "matches": sha == expected["sha256"] and len(body) == expected["bytes"]}
    except Exception as error:
        return {"file": name, "matches": False, "error": str(error)}

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(check, manifest["files"].items()))
try:
    with urllib.request.urlopen(urllib.request.Request(base.rstrip("/") + "?verify=" + nonce,
            headers={"Cache-Control": "no-cache"}), timeout=25) as response:
        canonical = {"status": response.status, "final_url": response.url,
                     "correct_path": response.url.split("?")[0] == base}
except Exception as error:
    canonical = {"error": str(error), "correct_path": False}
report = {"base_url": base, "checked_unix": time.time(), "canonical": canonical,
          "all_files_match": all(row["matches"] for row in results), "files": results}
(OUT / "live-verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
sys.exit(0 if report["all_files_match"] and canonical["correct_path"] else 1)
