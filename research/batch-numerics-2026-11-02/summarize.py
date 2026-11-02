"""Summarize fixed-window numerical checks, not request performance."""
import hashlib,json,sys
from collections import Counter,defaultdict
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def summarize(path):
 d=json.loads(Path(path).read_text());counts=Counter();groups=defaultdict(Counter);flips=[];worst={'gap':0,'case':None};ctrlworst={'gap':0,'case':None}
 for window in d['windows']:
  width=window['width'];counts['windows']+=1;groups[str(width)]['windows']+=1
  for pos in window['positions']:
   counts['positions']+=1;groups[str(width)]['positions']+=1
   if pos['top1_flipped']:
    counts['serial_batch_top1_flips']+=1;groups[str(width)]['serial_batch_top1_flips']+=1
    flips.append({'case':window['case'],'offset':window['offset'],'width':width,'window_position':pos['index'],'serial_margin':pos['serial_margin'],'batch_margin':pos['batch_margin'],'max_abs_serial_batch':pos['max_abs_serial_batch']})
   if pos['control_top1_flipped']:counts['serial_repeat_top1_flips']+=1;groups[str(width)]['serial_repeat_top1_flips']+=1
   if pos['max_abs_serial_batch']>worst['gap']:worst={'gap':pos['max_abs_serial_batch'],'case':window['case'],'offset':window['offset'],'width':width,'window_position':pos['index']}
   if pos['max_abs_serial_control']>ctrlworst['gap']:ctrlworst={'gap':pos['max_abs_serial_control'],'case':window['case'],'offset':window['offset'],'width':width,'window_position':pos['index']}
 return {'raw_file':Path(path).name,'raw_sha256':sha(path),'gpu_layers_requested':d['gpu_layers_requested'],'flash_attention_requested':d['flash_attention_requested'],'threads':d['threads'],'counts':dict(counts),'by_width':{k:dict(v) for k,v in groups.items()},'max_abs_serial_batch':worst,'max_abs_serial_repeat':ctrlworst,'flips':flips}
if __name__=='__main__':
 results=[summarize(p) for p in sys.argv[2:]]
 Path(sys.argv[1]).write_text(json.dumps({'scope':'targeted single-session windows, not population rates','runs':results},indent=2)+'\n')
 for r in results:print(r['raw_file'],r['counts'],'max_gap',r['max_abs_serial_batch']['gap'],'control_max',r['max_abs_serial_repeat']['gap'])
