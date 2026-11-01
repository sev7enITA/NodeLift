"""Basic device classification from one bounded diagnostic assessment.

Synthetic CPU and HTTPS probes never qualify LLM speedup or shared RAM.
"""
import json
import math
import statistics


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def summarize(record, jobs, caps, current_address=None):
    report = dict(state='pending', classification='needs_assessment', updated_at=None,
                  network=None, cpu=None, llm_qualified=False, reason='needs_assessment', steps=[])
    if not record:
        return report
    report['updated_at'] = max([record['created']] + [j['finished'] for j in jobs if j.get('finished')])
    report['steps'] = [{'kind':j['kind'], 'state':j['state']} for j in jobs]
    for job in jobs:
        if job['state'] != 'completed' or not job.get('result'): continue
        result = json.loads(job['result']) if isinstance(job['result'], str) else job['result']
        samples = result.get('samples', [])
        if job['kind'] == 'network':
            rtts = sorted(s['ms'] for s in samples if s.get('kind')=='rtt' and s.get('pace_ms',0)==0 and positive(s.get('ms')))
            directions = {}
            for direction in ('download','upload'):
                valid = [s for s in samples if s.get('kind')==direction and positive(s.get('bytes')) and positive(s.get('ms'))]
                largest = max((s['bytes'] for s in valid), default=0)
                directions[direction+'_mib_s'] = statistics.median(s['bytes']/1048576/(s['ms']/1000) for s in valid if s['bytes']==largest) if largest else None
            if rtts and all(v is not None for v in directions.values()):
                report['network'] = dict(rtt_p50_ms=statistics.median(rtts),rtt_p95_ms=rtts[math.ceil(.95*len(rtts))-1],samples=len(rtts),**directions)
        elif job['kind'] == 'cpu':
            sample = next((s for s in samples if s.get('kind')=='cpu' and positive(s.get('ms')) and positive(s.get('iterations'))),None)
            if sample:report['cpu'] = dict(iterations_per_second=sample['iterations']/(sample['ms']/1000),ms=sample['ms'])
    states = [j['state'] for j in jobs]
    if 'running' in states:
        report.update(state='running',reason='assessment_running')
    elif 'queued' in states:
        report.update(reason='waiting_for_device')
    elif report['network'] and report['cpu']:
        report.update(state='completed',classification='draft_candidate' if caps.get('engine_ready') else 'diagnostics_only',reason='basic_complete' if caps.get('engine_ready') else 'engine_not_ready')
    elif not jobs:
        report.update(state='unsupported',classification='diagnostics_only',reason='unsupported_diagnostics')
    elif len(jobs)<2 and (report['network'] or report['cpu']):
        report.update(state='partial',classification='diagnostics_only',reason='unsupported_diagnostics')
    else:
        report.update(state='partial' if report['network'] or report['cpu'] else 'failed',classification='needs_attention',reason='network_failed' if not report['network'] else 'cpu_failed')
    if record.get('peer_address') and current_address and record['peer_address'] != current_address:
        report.update(state='partial',classification='needs_assessment',reason='connection_changed')
    return report
