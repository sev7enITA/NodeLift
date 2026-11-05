"""Pinned official Qwen snapshots with free-space admission and retained manifests."""
from pathlib import Path
import json,shutil,time,hashlib
from huggingface_hub import snapshot_download
P=Path(__file__).resolve().parent;A=P.parents[1]/'artifacts/adaptive-targets-2026-11-05';A.mkdir(exist_ok=True)
rows=json.loads((P/'catalog.json').read_text());selected=[r for r in rows if r['repo'].endswith('4bit')]
assert shutil.disk_usage(Path.home()).free>sum(r['bytes'] for r in selected)+12*1024**3
results=[]
for r in selected:
 if shutil.disk_usage(Path.home()).free<r['bytes']+12*1024**3:raise RuntimeError('Disk reserve')
 t=time.monotonic();print('START',r['repo'],flush=True)
 path=snapshot_download(r['repo'],revision=r['revision'],allow_patterns=[x['name'] for x in r['files']],max_workers=3)
 v={'repo':r['repo'],'revision':r['revision'],'path':path,'seconds':time.monotonic()-t};results.append(v)
 (A/'models.json').write_text(json.dumps(results,indent=2)+'\n');print('DONE',r['repo'],round(v['seconds'],1),flush=True)
print('ALL DOWNLOADED',flush=True)
