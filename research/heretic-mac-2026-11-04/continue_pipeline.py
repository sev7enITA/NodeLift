"""Sequential, bounded local stages. Preserve artifacts and stop on failure."""
from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;A=R/'artifacts/heretic-mac-2026-11-04';base=(A/'base-model-path.txt').read_text().strip()
def run(name,args,seconds=1800):
 log=A/(name+'.log')
 if log.exists():raise RuntimeError('Refusing to overwrite '+str(log))
 print('START',name,flush=True)
 with log.open('w') as f:r=subprocess.run([sys.executable,*map(str,args)],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=seconds)
 if r.returncode:raise RuntimeError(f'{name}: exit {r.returncode}')
 print('DONE',name,flush=True)
def evaluate(label):run(label+'-evaluation',[P/'evaluate.py','--model',base,'--adapter',A/(label+'-adapter'),'--label',label,'--out',A/label])
def modify(label):
 run(label+'-stage',[P/'run_stage.py',label,'config-cwd'])
 if not (A/(label+'-adapter')/'adapter_model.safetensors').is_file():raise RuntimeError('No exported adapter: '+label)
evaluate('refusal');modify('nosyco');evaluate('nosyco');modify('draft')
for label,extra in [('draft-original',[]),('draft-modified',['--adapter',A/'draft-adapter'])]:
 run(label+'-agreement',[P/'draft_agreement.py','--out',A/(label+'-agreement.json'),*extra])
print('PIPELINE COMPLETE',flush=True)
