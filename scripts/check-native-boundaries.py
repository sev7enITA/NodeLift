#!/usr/bin/env python3
"""Real-model boundary checks, including optional test-only C ABI fault injection."""
import argparse,ctypes,hashlib,json,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'host'))
from nodelift.native import Native,library_path
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--faults',action='store_true');args=p.parse_args()
checks=[];models=[]
for filename,marker in [('qwen2.5-0.5b-instruct-q4_k_m.gguf','<|im_start|>'),('Llama-3.2-1B-Instruct-Q4_K_M.gguf','<|start_header_id|>')]:
    path=ROOT/'.models'/filename
    with Native() as n:
        info=n.call('load',path=str(path),n_ctx=512,threads=4,gpu_layers=999)
        models.append(dict(file=filename,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),info=info))
        valid=n.call('tokenize',text='Hello 世界, ciao 🌍',chat=True)['tokens'];assert valid
        for content in [marker,'hello\0world']:
            for role in ['user','assistant','system']:
                try:n.call('tokenize',text='',chat=True,messages=[dict(role=role,content=content)])
                except RuntimeError:pass
                else:raise AssertionError('unsafe content accepted')
                checks.append(dict(case='chat control rejected',model=filename,role=role,kind='NUL' if '\0' in content else 'control',passed=True))
        try:n.call('tokenize',text='',chat=True,messages=[dict(role='tool',content='hello')])
        except RuntimeError:pass
        else:raise AssertionError('unsupported role accepted')
        literal=n.call('tokenize',text=marker,chat=False,add_special=False)['tokens']
        special=n.call('tokenize',text=marker,chat=False,add_special=False,parse_special=True)['tokens']
        assert literal!=special
        result=n.call('draft',prefix=valid,count=8);t=result['timing']
        assert abs(t['native_sync_ms']+t['native_after_sync_ms']-t['native_total_ms'])<.01
        assert 0<=t['native_decode_ms']<=t['native_total_ms'] and t['native_decode_tokens']>=len(valid)
        n.call('reset');verified=n.call('verify',prefix=valid,proposal=result['tokens'],remaining=len(result['tokens']))
        assert verified['tokens']==result['tokens'] and verified['verification_mode']=='serial'
        checks.append(dict(case='default serial, literal controls and timing partition',model=filename,passed=True))
        if args.faults:
            fault=n.lib.nl_test_fail_next_response;fault.argtypes=[ctypes.c_int]
            for kind in [1,2]:
                fault(kind)
                try:n.call('reset')
                except RuntimeError as e:assert 'allocation' in str(e)
                else:raise AssertionError('fault did not return null')
                assert n.call('tokenize',text='Still alive',chat=True)['tokens']
                checks.append(dict(case='response allocation recovery',kind=kind,model=filename,passed=True))
        else:assert not hasattr(n.lib,'nl_test_fail_next_response')
# Repeated cancellation covers the window after nl_call clears its cancellation bit.
with Native() as n:
    outcome={};started=threading.Event()
    def load():
        started.set()
        try:outcome['value']=n.call('load',path=str(ROOT/'.models/llama3.1-8b-ollama.gguf'),n_ctx=512,threads=4,gpu_layers=999)
        except RuntimeError as e:outcome['error']=str(e)
    thread=threading.Thread(target=load);thread.start();started.wait(1)
    while thread.is_alive():n.cancel();thread.join(.001)
    assert 'error' in outcome,outcome
    try:n.call('tokenize',text='Hello')
    except RuntimeError as e:assert 'no model' in str(e)
    else:raise AssertionError('failed load retained model')
    n.call('load',path=str(ROOT/'.models/qwen2.5-0.5b-instruct-q4_k_m.gguf'),n_ctx=512,threads=4,gpu_layers=999)
    assert n.call('tokenize',text='Recovered',chat=True)['tokens']
    checks.append(dict(case='cancel model load, clear state and reload',passed=True))
output=dict(native_library_sha256=hashlib.sha256(library_path().read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),faults=args.faults,models=models,checks=checks)
Path(args.output).write_text(json.dumps(output,indent=2)+'\n');print(f'{len(checks)} boundary checks passed')
