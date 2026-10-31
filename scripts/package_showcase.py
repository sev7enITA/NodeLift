#!/usr/bin/env python3
"""Package only the public NodeLift showcase; never include host/runtime state."""
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site/NodeLift"
OUT = ROOT / "artifacts/showcase"
OUT.mkdir(parents=True, exist_ok=True)
files = sorted(p for p in SITE.rglob("*") if p.is_file())
assert files and (SITE / "index.html") in files
assert all(not p.is_symlink() and p.suffix in {".html", ".css", ".js", ".json", ".csv", ".md", ".png", ".svg", ".woff2", ".txt"} for p in files)
manifest = {"created_utc": datetime.now(timezone.utc).isoformat(),
            "base_url": "https://www.fabriziodegni.com/NodeLift/", "files": {}}
for path in files:
    manifest["files"][str(path.relative_to(SITE))] = {
        "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
identity = hashlib.sha256(json.dumps(manifest["files"], sort_keys=True).encode()).hexdigest()[:12]
archive = OUT / f"NodeLift-showcase-{identity}.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
    for path in files:
        output.write(path, Path("NodeLift") / path.relative_to(SITE))
manifest["archive"] = {"name": archive.name, "bytes": archive.stat().st_size,
                       "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}
(OUT / "deployment-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({"archive": str(archive), "files": len(files), "bytes": archive.stat().st_size,
                  "sha256": manifest["archive"]["sha256"]}, indent=2))
