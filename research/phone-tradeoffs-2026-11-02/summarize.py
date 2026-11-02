"""Recompute descriptive trade-off tables from retained, scoped session records."""
import json
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CELLS=('local-fixed-32','remote-adaptive-32','remote-fixed-32','remote-adaptive-128','remote-fixed-128')


def stats(xs):
    return {'n':len(xs),'median':statistics.median(xs) if xs else None,'minimum':min(xs) if xs else None,'maximum':max(xs) if xs else None}


def summarize(data):
    rows=[];counts={'planned_pairs':0,'observed_host':0,'observed_candidate':0,'completed_host':0,'completed_candidate':0,'equivalent_pairs':0,'fallbacks':0,'accepted':0,'proposed':0}
    phases=[];battery=[];rss=[];load=[];disabled={};states=[]
    for session in data['sessions']:
        attempts={(a['pair_id'],a['arm']):a for a in session['attempts']}
        for p in session['plan']:
            counts['planned_pairs']+=1
            host,candidate=(attempts.get((p['id'],arm)) for arm in ('host','candidate'))
            for arm,a in [('host',host),('candidate',candidate)]:
                if a:
                    counts['observed_'+arm]+=1;counts['completed_'+arm]+=int(a['status']=='completed')
            if candidate:
                counts['fallbacks']+=int(candidate['fallback']);metrics=candidate.get('metrics',{})
                counts['accepted']+=metrics.get('accepted_tokens') or 0;counts['proposed']+=metrics.get('proposed_tokens') or 0
                reason=metrics.get('draft_disabled_reason')
                if reason:disabled[reason]=disabled.get(reason,0)+1
                for field in ('telemetry_before','telemetry_after'):
                    snap=candidate.get(field,{})
                    c=snap.get('companion',{})
                    if c.get('thermal') is not None:phases.append(c['thermal'])
                    if c.get('battery_percent') is not None:battery.append(c['battery_percent'])
                    if c.get('process_memory_bytes') is not None:rss.append(c['process_memory_bytes'])
                    if snap.get('host_load_average'):load.append(snap['host_load_average'][0])
            if not host or not candidate or any(a['status']!='completed' for a in (host,candidate)):continue
            equal=(host['tokens_sha256']==candidate['tokens_sha256'] and host['token_count']==candidate['token_count'] and host['finish_reason']==candidate['finish_reason'])
            counts['equivalent_pairs']+=int(equal)
            row={'pair_id':p['id'],'session':session['id'],'order':p['order'],'equivalent':equal,'fallback':candidate['fallback'],
                 'host_ms':host['duration_ms'],'candidate_ms':candidate['duration_ms'],
                 'added_ms':candidate['duration_ms']-host['duration_ms'],
                 'slowdown_ratio':candidate['duration_ms']/host['duration_ms'],
                 'ttft_change_ms':candidate['ttft_ms']-host['ttft_ms'],
                 'remote_wait_ms':candidate['metrics'].get('remote_wait_ms'),
                 'generated_tokens':candidate['token_count']}
            rows.append(row)
    good=[r for r in rows if r['equivalent']]
    return {'scope':data['scope'],'display':data.get('display',{}),'configuration':data['sessions'][0].get('configuration'),
            'recorded_sessions':len(data['sessions']),'independence_qualified':False,'counts':counts,
            'delivered_service_including_fallback':{k:stats([r[k] for r in good if r[k] is not None]) for k in ('host_ms','candidate_ms','added_ms','slowdown_ratio','ttft_change_ms','remote_wait_ms')},
            'accepted_fraction_of_proposals':counts['accepted']/counts['proposed'] if counts['proposed'] else None,
            'disabled_reasons':disabled,'reported_thermal_categories':sorted(set(phases)),
            'battery_percent_snapshots':stats(battery),'companion_process_bytes_snapshots':stats(rss),'host_load_one_minute_snapshots':stats(load),
            'energy':'unmeasured','pairs':rows}


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
