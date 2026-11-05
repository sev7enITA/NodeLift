"""Bounded experiment process with independent OS resource/thermal sampling."""
import argparse,json,subprocess,sys,time
from pathlib import Path
import psutil
from qualification import assess
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def sample():
 m=psutil.virtual_memory();s=psutil.swap_memory()
 thermal=json.loads(subprocess.check_output(['/tmp/nodelift-five-thermal','1','1']))
 return dict(unix=time.time(),cpu_percent=psutil.cpu_percent(interval=1),available_bytes=m.available,swap_used_bytes=s.used,swap_in_bytes=s.sin,swap_out_bytes=s.sout,disk_free_bytes=psutil.disk_usage(ROOT).free,**{'thermal':thermal['thermal'],'low_power_mode':thermal.get('low_power_mode')})
def main():
 a=argparse.ArgumentParser();a.add_argument('--name',required=True);a.add_argument('command',nargs=argparse.REMAINDER);o=a.parse_args()
 folder=ROOT/'artifacts/five-cases-2026-11-05'/o.name;folder.mkdir(exist_ok=False)
 pre=[sample() for _ in range(3)];gate=assess(pre,pre[-1]['thermal'],pre[-1]['low_power_mode'])
 (folder/'preflight.json').write_text(json.dumps(dict(samples=pre,gate=gate,command=o.command),indent=2)+'\n')
 if not gate['admit_bounded_diagnostic']:raise SystemExit('Preflight refused')
 started=time.monotonic();reason=None
 with (folder/'process.log').open('w') as log,(folder/'resources.jsonl').open('w') as telemetry:
  p=subprocess.Popen(o.command,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
  try:
   while p.poll() is None:
    s=sample();telemetry.write(json.dumps(s)+'\n');telemetry.flush()
    if time.monotonic()-started>1800:reason='process_deadline'
    elif s['thermal'] in ('serious','critical'):reason='thermal_pressure'
    elif s['available_bytes']<1024**3:reason='memory_floor'
    elif s['disk_free_bytes']<12*1024**3:reason='disk_reserve'
    if reason:p.terminate();break
    time.sleep(4)
   try:code=p.wait(timeout=15)
   except subprocess.TimeoutExpired:p.kill();code=p.wait()
  finally:
   if p.poll() is None:p.terminate();p.wait(timeout=15)
  (folder/'completion.json').write_text(json.dumps(dict(exit_code=code,stop_reason=reason,elapsed_seconds=time.monotonic()-started),indent=2)+'\n')
 if code or reason:raise SystemExit(1)
if __name__=='__main__':main()
