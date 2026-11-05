"""Negative controls for diagnostic admission and queue accounting."""
import json,math
from pathlib import Path
from qualification import assess
from simulate import pipeline
good=dict(cpu_percent=5,available_bytes=12*2**30,disk_free_bytes=20*2**30,swap_used_bytes=0)
checks=[]
def check(name,v):
 checks.append(dict(name=name,passed=bool(v)));assert v,name
check('healthy bounded diagnostic admitted',assess([good]*3,'nominal',False)['admit_bounded_diagnostic'])
for label,samples,thermal in [('missing samples',[], 'nominal'),('unknown thermal',[good]*3,'unknown'),('thermal pressure',[good]*3,'serious'),('invalid CPU',[dict(good,cpu_percent=math.nan)]*3,'nominal'),('memory floor',[dict(good,available_bytes=0)]*3,'nominal'),('disk reserve',[dict(good,disk_free_bytes=0)]*3,'nominal')]:
 check(label,not assess(samples,thermal,False)['admit_bounded_diagnostic'])
check('low-power never qualifies isolated performance',not assess([good]*3,'nominal',True)['isolated_performance_qualification'])
b=[dict(width=2,seconds=3)]*3
check('free candidates pay all verifier work',pipeline(b,0,0)['decode_seconds']==9)
check('slower producer bounded schedule',pipeline(b,2,0)['decode_seconds']==15)
check('delivery paid and overlap bounded',pipeline(b,0,2)['decode_seconds']==11)
try:pipeline(b,-1,0)
except ValueError:check('negative production cost refused',True)
else:check('negative production cost refused',False)
(Path(__file__).parent/'checks.json').write_text(json.dumps(dict(checks=checks,scope='Helper negative controls; not LLM correctness or speed validation'),indent=2)+'\n')
print(len(checks),'checks passed')
