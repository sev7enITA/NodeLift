"""Download pinned official Qwen GGUF controls; model weights are never committed."""
import hashlib
import json
import shutil
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

root = Path(__file__).resolve().parents[1]
folder = root / '.models'
folder.mkdir(exist_ok=True)
models = json.loads((root/'profiles/control-models.json').read_text())['models']
assert shutil.disk_usage(folder).free > sum(m['bytes'] for m in models) + 3*1024**3, 'Insufficient disk headroom'

def fetch(model):
    path = folder / model['file']
    if path.exists() and hashlib.file_digest(path.open('rb'), 'sha256').hexdigest() == model['sha256']:
        print(model['role'], 'already verified', flush=True); return
    temporary = path.with_suffix('.partial')
    url = 'https://huggingface.co/'+model['repo']+'/resolve/'+model['revision']+'/'+model['file']
    digest = hashlib.sha256(); total = 0
    with urllib.request.urlopen(url, timeout=90) as response, temporary.open('wb') as out:
        while chunk := response.read(1024*1024):
            total += len(chunk)
            if total > model['bytes']: raise ValueError('Unexpected model length')
            digest.update(chunk); out.write(chunk)
    if total != model['bytes'] or digest.hexdigest() != model['sha256']: raise ValueError('Model integrity mismatch')
    temporary.replace(path)
    print(model['role'], 'downloaded and SHA-256 verified', total, flush=True)

with ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(fetch, models))
