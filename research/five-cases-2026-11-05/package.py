"""Publish sanitized evidence; keep original local captures untouched."""
from pathlib import Path
import json,hashlib,shutil
P=Path(__file__).resolve().parent;ROOT=P.parents[1];A=ROOT/'artifacts/five-cases-2026-11-05';out=P/'results';out.mkdir(exist_ok=True)
folders=['envelope-native','envelope-fp32','accounting','localization','localization-attention','projection-probe','physical-transport']+[p.name for p in sorted(A.glob('monitor-*'))]
for name in folders:
 source=A/name
 if not source.exists():continue
 target=out/name;target.mkdir(exist_ok=True)
 for file in source.iterdir():
  if file.is_file() and file.suffix in ['.json','.jsonl','.log','.py']:
   text=file.read_text().replace(str(ROOT),'<WORKSPACE>').replace(str(Path.home()),'<USER_HOME>')
   (target/file.name).write_text(text)
r=json.loads((A/'readiness/readiness.json').read_text())
(out/'device-readiness.json').write_text(json.dumps(dict(observed_unix=r['observed_unix'],engine_available=r['engine_available'],engine_busy=r['engine_busy'],available_worker_selected=bool(r['selected_ready_node']),scope='Initial readiness snapshot before the user reopened a device. Historical identities and network details omitted from public evidence.'),indent=2)+'\n')
(P/'sample-host.swift').write_text((ROOT/'scripts/sample-host.swift').read_text())
hashes={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(P.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f.name not in ['artifact-sha256.json','publication.json']}
(P/'artifact-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
print(len(hashes),'evidence/source artifacts hashed')
