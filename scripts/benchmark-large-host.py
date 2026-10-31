"""Upstream large-model kernel baseline. No NodeLift/mobile acceleration claim."""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--model',required=True)
args=parser.parse_args();model=Path(args.model).resolve()
folder=ROOT/'research/measurements/large-host-baseline';folder.mkdir(parents=True,exist_ok=True)
binary=ROOT/'.deps/llama.cpp/build/bin/llama-bench'
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
command=[str(binary),'-m',str(model),'-ngl','999','-t','8','-fa','on','-p','128','-n','64','-r','3','-o','json']
manifest={'model':model.name,'bytes':model.stat().st_size,'sha256':sha(model),
          'llama_commit':(ROOT/'native/llama.lock').read_text().strip(),'binary_sha256':sha(binary),
          'options':command[3:],'started':time.time(),
          'memory_pressure_before':subprocess.check_output(['memory_pressure','-Q'],text=True),
          'swap_before':subprocess.check_output(['sysctl','vm.swapusage'],text=True),
          'scope':'upstream llama-bench pp128/tg64 kernel microbenchmark; synthetic token stream, not chat latency, not NodeLift hybrid support, no phone involved'}
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (ROOT/'artifacts/large-host-raw.json').open('w') as out,(ROOT/'artifacts/large-host.log').open('w') as log:
    subprocess.run(command,stdout=out,stderr=log,check=True,timeout=240)
rows=json.loads((ROOT/'artifacts/large-host-raw.json').read_text())
for row in rows:
    if 'model_filename' in row:row['model_filename']=Path(row['model_filename']).name
(folder/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
manifest.update(finished=time.time(),memory_pressure_after=subprocess.check_output(['memory_pressure','-Q'],text=True),
                swap_after=subprocess.check_output(['sysctl','vm.swapusage'],text=True))
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(folder/'hashes.json').write_text(json.dumps({p.name:sha(p) for p in folder.iterdir() if p.is_file() and p.name!='hashes.json'},indent=2)+'\n')
print(json.dumps([{'n_prompt':r.get('n_prompt'),'n_gen':r.get('n_gen'),'avg_ts':r.get('avg_ts'),'stddev_ts':r.get('stddev_ts')} for r in rows]))
