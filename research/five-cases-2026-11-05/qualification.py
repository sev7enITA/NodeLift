"""Resource labels are explicit. Passing this gate does not qualify a speed claim."""
import math
def assess(samples,thermal,low_power):
 reasons=[]
 if len(samples)<3:reasons.append('insufficient_preflight_samples')
 if any(not math.isfinite(s['cpu_percent']) or s['cpu_percent']<0 or s['cpu_percent']>100 for s in samples):reasons.append('invalid_cpu_sample')
 if any(s['available_bytes']<9*2**30 for s in samples):reasons.append('insufficient_memory')
 if any(s['disk_free_bytes']<12*2**30 for s in samples):reasons.append('insufficient_disk_reserve')
 if thermal in ('serious','critical'):reasons.append('thermal_pressure')
 if thermal not in ('nominal','fair','serious','critical'):reasons.append('thermal_unknown')
 operational=not reasons
 if low_power:reasons.append('low_power_mode_enabled')
 if any(s['cpu_percent']>30 for s in samples):reasons.append('background_cpu_load')
 if any(s['swap_used_bytes']>0 for s in samples):reasons.append('preexisting_swap_not_attributed')
 return {'admit_bounded_diagnostic':operational,'isolated_performance_qualification':False,'reasons':reasons,'scope':'Preflight only; thermal/energy and resource behavior during inference require separate evidence'}
