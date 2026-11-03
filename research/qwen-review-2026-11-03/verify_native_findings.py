#!/usr/bin/env python3
"""Check Qwen's two native-state hypotheses against the existing real library.

Correctness checks only. This is not a timing or physical-device benchmark.
"""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'host'))
from nodelift.native import Native,library_path
model=ROOT/'.models/qwen2.5-0.5b-instruct-q4_k_m.gguf'
rows=[]
with Native() as n:
    n.call('load',path=str(model),n_ctx=256,threads=2,gpu_layers=0)
    prefix=n.call('tokenize',text='The capital of France is',chat=False)['tokens']
    edge=(prefix*256)[:255]
    for strict in (True,False):
        n.call('reset')
        proposal=n.call('draft',prefix=edge,count=1)['tokens']
        n.call('reset')
        result=n.call('verify',strict=strict,prefix=edge,proposal=proposal,remaining=4)
        assert len(result['tokens'])==1
        rows.append({'case':'255-token prefix plus one proposal in context 256','strict':strict,'result':{k:result[k] for k in ('tokens','accepted','proposed','verification_mode')},'passed':True})
    n.call('reset')
    proposal=n.call('draft',prefix=prefix,count=4)['tokens']
    for remaining in (1,2,3,4,5):
        n.call('reset')
        result=n.call('verify',strict=True,prefix=prefix,proposal=proposal,remaining=remaining)
        assert result['accepted']==min(len(proposal),remaining)
        assert result['tokens'][:result['accepted']]==proposal[:result['accepted']]
        assert len(result['tokens'])<=remaining
        rows.append({'case':'serial accepted count with remaining budget','remaining':remaining,'accepted':result['accepted'],'output_tokens':len(result['tokens']),'passed':True})
    n.call('reset')
    wrong=proposal[:];wrong[1]=(wrong[1]+1)%100
    result=n.call('verify',strict=True,prefix=prefix,proposal=wrong,remaining=4)
    assert result['accepted']==1 and len(result['tokens'])==2
    rows.append({'case':'one accepted proposal followed by replacement','accepted':result['accepted'],'output_tokens':len(result['tokens']),'passed':True})
record={'scope':'CPU real-weight native correctness checks, not performance or phone tests','model':model.name,'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'library_sha256':hashlib.sha256(library_path().read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checks':rows}
Path(__file__).with_name('native-findings-check.json').write_text(json.dumps(record,indent=2)+'\n')
print(f'{len(rows)} native finding checks passed')
