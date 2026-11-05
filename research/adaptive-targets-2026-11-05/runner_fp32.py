"""Explicit FP32 floating-parameter lane; integer quantized weights are preserved."""
from pathlib import Path
import hashlib
import mlx.core as mx
from mlx.utils import tree_flatten
import runner
original_load=runner.load
original_save=runner.save
observed=[]
def load(path):
 model,tok=original_load(path)
 before={name:str(v.dtype) for name,v in tree_flatten(model.parameters())}
 model.set_dtype(mx.float32);mx.eval(model.parameters())
 after={name:str(v.dtype) for name,v in tree_flatten(model.parameters())}
 assert all(after[k]==v for k,v in before.items() if 'uint' in v or 'int' in v)
 observed.append({'model_directory_name':Path(path).name,'dtypes_before':sorted(set(before.values())),'dtypes_after':sorted(set(after.values())),'packed_integer_dtypes_preserved':True})
 return model,tok
def save(path,value):
 if path.name=='manifest.json':
  value['arithmetic_lane']='fp32-floating-parameters';value['parameter_dtype_observations']=observed;value['source_hashes']['runner_fp32.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 original_save(path,value)
runner.load=load;runner.save=save
if __name__=='__main__':runner.main()
