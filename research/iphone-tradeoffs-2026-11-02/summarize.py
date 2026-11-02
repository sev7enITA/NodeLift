"""Recompute descriptive trade-off tables from retained, scoped session records."""
import json
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CELLS=('remote-adaptive-32','remote-fixed-32','remote-adaptive-128','remote-fixed-128','build15-adaptive-32','build15-fixed-128')


# Reuse the same descriptive accounting used for Xiaomi; do not pool the sessions.
import runpy
summarize=runpy.run_path(str(ROOT.parent/'phone-tradeoffs-2026-11-02/summarize.py'))['summarize']


def main():
    out={'schema_version':1,'scope':'exploratory cells, never pooled as independent sessions','cells':{}}
    for name in CELLS:
        path=ROOT/(name+'.json')
        out['cells'][name]=summarize(json.loads(path.read_text())) if path.exists() else {'status':'not_collected'}
    (ROOT/'RESULTS.json').write_text(json.dumps(out,indent=2)+'\n')
    decisions_path=ROOT/'study-decisions.json'
    if decisions_path.exists():
        for name,decision in json.loads(decisions_path.read_text()).items():
            if name in out['cells'] and 'counts' not in out['cells'][name]:out['cells'][name]=decision
    (ROOT/'RESULTS.json').write_text(json.dumps(out,indent=2)+'\n')
    lines=['| Condition | Completed candidate / planned | Equivalent pairs | Median added total time | Median TTFT change | Median candidate/host ratio | Fallbacks | Accepted / proposed |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    def fmt(x):return 'unavailable' if x is None else f'{x:,.3f}'
    for name,v in out['cells'].items():
        if 'counts' not in v:
            status='Not scheduled by rule' if v.get('status')=='not_scheduled' else 'Not collected'
            lines.append(f'| {name} | {status} | | | | | | |');continue
        c=v['counts'];m=v['delivered_service_including_fallback']
        lines.append(f'| {name} | {c["completed_candidate"]}/{c["planned_pairs"]} | {c["equivalent_pairs"]}/{c["planned_pairs"]} | {fmt(m["added_ms"]["median"])} ms | {fmt(m["ttft_change_ms"]["median"])} ms | {fmt(m["slowdown_ratio"]["median"])}x | {c["fallbacks"]} | {c["accepted"]}/{c["proposed"]} |')
    (ROOT/'TABLE.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__=='__main__':main()
