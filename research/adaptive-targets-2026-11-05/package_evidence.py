"""Copy bounded, non-secret experiment evidence and hash pinned model files after timing."""
from pathlib import Path
import hashlib, json, shutil

P=Path(__file__).resolve().parent
A=P.parents[1]/'artifacts/adaptive-targets-2026-11-05'
out=P/'results/raw'
out.mkdir(parents=True,exist_ok=True)
stages=['14B-screen','14B-fp32-screen','14B-fp32-validation-0','14B-fp32-validation-1','32B-screen','smoke-template-retry']
for stage in stages:
    destination=out/stage
    destination.mkdir(exist_ok=True)
    for name in ['admission.json','manifest.json','calibration.json','warmups.json','runs.jsonl','smoke.json']:
        source=A/stage/name
        if source.exists():shutil.copyfile(source,destination/name)
    status=A/(stage+'-status.json')
    if status.exists():shutil.copyfile(status,destination/'status.json')
shutil.copyfile(A/'runner-initial.py',out/'runner-before-template-amendment.py')
shutil.copyfile(A/'smoke-status.json',out/'initial-template-smoke-status.json')
models=json.loads((A/'models.json').read_text())
hashes=[]
for model in models:
    root=Path(model['path'])
    files=[]
    for path in sorted(root.rglob('*')):
        if not path.is_file():continue
        h=hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda:f.read(8*1024**2),b''):h.update(chunk)
        files.append({'file':str(path.relative_to(root)),'bytes':path.stat().st_size,'sha256':h.hexdigest()})
    hashes.append({'repo':model['repo'],'revision':model['revision'],'files':files})
    print('hashed',model['repo'],flush=True)
(P/'model-file-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
