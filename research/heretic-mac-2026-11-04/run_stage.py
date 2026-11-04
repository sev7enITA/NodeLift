"""Bounded Heretic CLI stage with local artifact retention; no publication."""
from pathlib import Path
import subprocess,os,time,json,sys,shutil
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;A=R/'artifacts/heretic-mac-2026-11-04'
label=sys.argv[1];attempt=sys.argv[2] if len(sys.argv)>2 else 'native'
log=A/(label+'-'+attempt+'.log');status=A/(label+'-'+attempt+'-status.json')
if log.exists() or status.exists():raise RuntimeError('Refusing to overwrite an attempt')
env=dict(os.environ,HERETIC_CONFIG_FILE=str(P/(label+'.toml')),HF_HUB_DISABLE_TELEMETRY='1',TOKENIZERS_PARALLELISM='false',PYTHONUNBUFFERED='1')
work=A/(label+'-'+attempt+'-work');work.mkdir(exist_ok=False)
shutil.copyfile(P/(label+'.toml'),work/'config.toml')
start=time.monotonic()
try:
 with log.open('w') as f:r=subprocess.run([sys.executable.replace('python','heretic')],cwd=work,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
 v={'exit_code':r.returncode}
except subprocess.TimeoutExpired:v={'error':'stage_timeout_1800s'}
v['adapter_exported']=(A/(label+'-adapter')/'adapter_model.safetensors').is_file()
v.update({'label':label,'attempt':attempt,'elapsed_seconds':time.monotonic()-start,'scope':'bounded local model editing; not inference latency benchmark'})
status.write_text(json.dumps(v,indent=2)+'\n');print(v)
