"""One bounded application transport job, only after fresh physical-node contact."""
from pathlib import Path
import importlib.util,json,time,types,hashlib
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
source=ROOT/'scripts/benchmark-session.py';spec=importlib.util.spec_from_file_location('session_probe',source);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
args=types.SimpleNamespace(port=9868,state_dir=Path.home()/'.local/share/nodelift')
api=mod.API(args);out=ROOT/'artifacts/five-cases-2026-11-05/physical-transport';out.mkdir(exist_ok=False)
start=time.monotonic();snapshots=[];outcome='no_fresh_node';result=None
while time.monotonic()-start<120:
 state=api('/admin/status');nodes=state['nodes'];fresh=[n for n in nodes if n['online'] and n.get('capabilities_updated_at') and state['observed_at']-n['capabilities_updated_at']<20]
 snapshots.append(dict(unix=time.time(),online_count=sum(bool(n['online']) for n in nodes),fresh_count=len(fresh)))
 if len(fresh)==1:
  result=mod.network_probe(api,args,fresh[0]['id']);outcome='probe_returned';break
 time.sleep(5)
value=dict(outcome=outcome,elapsed_seconds=time.monotonic()-start,readiness=snapshots,result=result,helper_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope='Paced application transport only. No remote inference, energy, model sharding or physical acceleration claim. Current topology not independently verified.')
(out/'result.json').write_text(json.dumps(value,indent=2)+'\n');print(outcome)
