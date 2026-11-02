"""Versioned, fail-closed analysis of paired NodeLift benchmark sessions.

Original NodeLift decision policy built from standard paired statistics. Reports
are evidence summaries, never scheduling authority or hardware attestation.
"""
import hashlib
import json
import math
import random
import re
import statistics
from collections import defaultdict

VERSION = 'nodelift-impact-v1'
MIN_CLUSTERS = 10
BOOTSTRAPS = 2000
SEED = 731921
SCOPE_KEYS = ('target_sha256', 'draft_sha256', 'native_sha256', 'config_sha256',
              'host_id', 'node_id', 'connection', 'candidate', 'warmup_policy')
LIMITATIONS = [
    'Imported records are not independent hardware attestation.',
    'Time and TTFT estimates are conditional on complete, identical-output, fallback-free pairs.',
    'Sessions must be independently collected; changing a session ID does not create independence.',
    'Confidence intervals describe sampling variability, not systematic or meter uncertainty.',
    'No effective GPU-offload or memory-residency attestation: no qualified routing recommendation.',
    'No automatic scheduler promotion; results apply only to the recorded scope.',
]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def number(value, label, minimum=0, maximum=1e12):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError('invalid ' + label)
    return float(value)


def label(value, name, maximum=256):
    if not isinstance(value, str) or not value or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise ValueError('invalid ' + name)
    return value


def sha256(value, name):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
        raise ValueError('invalid '+name)
    return value


def quantile(values, q):
    values = sorted(values)
    i = (len(values)-1)*q
    lo = int(i)
    return values[lo] + (values[min(lo+1, len(values)-1)]-values[lo])*(i-lo)


def estimate(rows, reducer=statistics.median):
    """Equal weight per pair; whole-session bootstrap, no within-session resampling."""
    groups = defaultdict(list)
    for session, value in rows:
        groups[session].append(value)
    result = {'estimate': reducer([v for _, v in rows]) if rows else None,
              'ci95': None, 'n': len(rows), 'clusters': len(groups)}
    if len(groups) >= MIN_CLUSTERS:
        rng = random.Random(SEED)
        clusters = list(groups.values())
        samples = [reducer([v for group in rng.choices(clusters, k=len(clusters)) for v in group])
                   for _ in range(BOOTSTRAPS)]
        bounds = [quantile(samples, .025), quantile(samples, .975)]
        result['degenerate_interval'] = bounds[0] == bounds[1]
        result['ci95'] = None if result['degenerate_interval'] else bounds
    return result


def wilson(successes, total):
    if not total:
        return None
    p, z = successes/total, 1.959963984540054
    den = 1+z*z/total
    center = (p+z*z/(2*total))/den
    half = z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
    return [max(0, center-half), min(1, center+half)]


def energy(record, duration_ms):
    """Integrate meter watts in its run-relative clock; require exact full coverage.

    No extrapolation. Samples may bracket the window and are linearly clipped.
    Calibration uncertainty is recorded separately, never folded into a bootstrap.
    """
    if record is None:
        return None, 'energy absent'
    if not isinstance(record, dict):
        return None, 'invalid energy object'
    try:
        source = label(record.get('source'), 'energy source')
        scope = label(record.get('scope'), 'energy scope')
        clock = label(record.get('clock'), 'energy clock')
        components = record.get('components')
        if not isinstance(components, list) or not 1 <= len(components) <= 16 or len(set(components)) != len(components):
            raise ValueError('invalid meter components')
        components = sorted(label(c, 'component') for c in components)
        if record.get('unit') != 'W' or clock != 'run_relative_monotonic_ms':
            raise ValueError('unsupported energy unit or clock')
        uncertainty = record.get('calibration_relative_uncertainty')
        if uncertainty is not None:
            number(uncertainty, 'calibration uncertainty', 0, 1)
        gap = number(record.get('max_gap_ms'), 'meter max gap', 1, 60000)
        samples = record.get('samples')
        if not isinstance(samples, list) or not 2 <= len(samples) <= 10000:
            raise ValueError('invalid energy samples')
        points = [(number(p[0], 'meter timestamp', -60000), number(p[1], 'power', 0, 1e6))
                  for p in samples if isinstance(p, list) and len(p) == 2]
        if len(points) != len(samples) or points[0][0] > 0 or points[-1][0] < duration_ms:
            raise ValueError('energy window not covered')
        total = 0.
        for (t0, p0), (t1, p1) in zip(points, points[1:]):
            if t1 <= t0:
                raise ValueError('unordered energy samples')
            a, b = max(0, t0), min(duration_ms, t1)
            if b <= a:
                continue
            if t1-t0 > gap:
                raise ValueError('energy sample gap')
            pa, pb = p0+(p1-p0)*(a-t0)/(t1-t0), p0+(p1-p0)*(b-t0)/(t1-t0)
            total += (pa+pb)*.5*(b-a)/1000
        return {'joules': total, 'identity': [source, scope, components, clock],
                'calibration_relative_uncertainty': uncertainty}, None
    except (ValueError, TypeError, IndexError):
        return None, 'invalid or incomplete energy coverage'


def analyze(data):
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data.get('schema_version') != 1 or data.get('runner') != VERSION:
        raise ValueError('version 1 impact sessions required; legacy records cannot be promoted')
    scope = data.get('scope')
    if not isinstance(scope, dict) or set(scope) != set(SCOPE_KEYS):
        raise ValueError('exact impact scope required')
    for key in SCOPE_KEYS:
        label(scope[key], key)
    for key in ('target_sha256', 'native_sha256', 'config_sha256', 'host_id', 'connection'):
        sha256(scope[key], key)
    if scope['draft_sha256'] != 'none':
        sha256(scope['draft_sha256'], 'draft hash')
    if scope['candidate'] not in ('host', 'local_draft', 'remote_draft'):
        raise ValueError('invalid candidate')
    kind = data.get('evidence_kind')
    if kind not in ('physical', 'local', 'synthetic', 'control'):
        raise ValueError('evidence kind required')
    if scope['candidate'] == 'host' and kind != 'control':
        raise ValueError('host versus host must be control evidence')
    scope_hash = digest(scope)
    sessions = data.get('sessions')
    if not isinstance(sessions, list) or not 1 <= len(sessions) <= 100:
        raise ValueError('1 to 100 sessions required')
    seen_sessions, seen_runs = set(), set()
    time_rows, percent_rows, ttft_rows, energy_rows, reliability_rows, completion_rows = [], [], [], [], [], []
    exclusions, points, energy_reasons = [], [], set()
    service_time_rows, service_ttft_rows = [], []
    counts = dict(planned_pairs=0, eligible_pairs=0, clusters=0, mismatched_pairs=0, missing_runs=0, invalid_pairs=0)
    reliability = {arm: dict(planned=0, observed=0, completed=0, correct=0, missing=0, fallback=0,
                            strict_success=0, failed=0, cancelled=0) for arm in ('host', 'candidate')}
    for session in sessions:
        if not isinstance(session, dict):
            raise ValueError('invalid session')
        sid = label(session.get('id'), 'session id', 100)
        if sid in seen_sessions:
            raise ValueError('duplicate session')
        seen_sessions.add(sid)
        plan = session.get('plan')
        attempts = session.get('attempts')
        if not isinstance(plan, list) or not 1 <= len(plan) <= 100 or not isinstance(attempts, list):
            raise ValueError('bounded plan and attempts required')
        if session.get('plan_sha256') != digest(plan) or session.get('scope_sha256') != scope_hash:
            raise ValueError('plan or scope digest mismatch')
        if len(attempts) > 2*len(plan):
            raise ValueError('retries cannot replace primary attempts')
        slots, pair_ids = {}, set()
        for p in plan:
            if not isinstance(p, dict) or set(p) != {'id', 'prompt_sha256', 'order', 'max_tokens'}:
                raise ValueError('invalid pair plan')
            pid = label(p['id'], 'pair id', 100)
            sha256(p['prompt_sha256'], 'prompt digest')
            if pid in pair_ids or p['order'] not in ('AB', 'BA') or type(p['max_tokens']) is not int or not 1 <= p['max_tokens'] <= 512:
                raise ValueError('invalid pair plan')
            pair_ids.add(pid)
        for a in attempts:
            if not isinstance(a, dict) or a.get('pair_id') not in pair_ids or a.get('arm') not in reliability:
                raise ValueError('unplanned attempt')
            slot = (a['pair_id'], a['arm'])
            if slot in slots:
                raise ValueError('duplicate primary attempt')
            if a.get('run_id'):
                rid = label(a['run_id'], 'run id', 128)
                if rid in seen_runs:
                    raise ValueError('reused run across pairs or sessions')
                seen_runs.add(rid)
            if a.get('status') not in ('completed', 'failed', 'cancelled', 'invalid'):
                raise ValueError('terminal attempt status required')
            slots[slot] = a
        for p in plan:
            counts['planned_pairs'] += 1
            if counts['planned_pairs'] > 1000:
                raise ValueError('at most 1000 planned pairs')
            pair = [slots.get((p['id'], arm)) for arm in ('host', 'candidate')]
            reasons, valid = [], []
            for arm, a in zip(('host', 'candidate'), pair):
                r = reliability[arm]
                r['planned'] += 1
                if a is None:
                    r['missing'] += 1
                    counts['missing_runs'] += 1
                    reasons.append(arm + ': missing')
                    valid.append(False)
                    continue
                r['observed'] += 1
                completed = a['status'] == 'completed'
                r['completed'] += int(completed)
                r['failed'] += int(a['status'] in ('failed', 'invalid'))
                r['cancelled'] += int(a['status'] == 'cancelled')
                fallback = a.get('fallback')
                if type(fallback) is not bool:
                    raise ValueError('explicit fallback flag required')
                r['fallback'] += int(fallback)
                ok = completed and not fallback
                if not completed or fallback:
                    reasons.append(arm + ': ' + ('fallback' if fallback else a['status']))
                if a.get('scope_sha256') != scope_hash or a.get('prompt_sha256') != p['prompt_sha256'] or a.get('max_tokens') != p['max_tokens']:
                    reasons.append(arm + ': scope or prompt drift')
                    ok = False
                if completed:
                    try:
                        duration = number(a.get('duration_ms'), 'duration', .000001)
                        number(a.get('ttft_ms'), 'TTFT', 0, duration)
                        if type(a.get('token_count')) is not int or not 1 <= a['token_count'] <= p['max_tokens']:
                            raise ValueError('no generated tokens')
                        sha256(a.get('tokens_sha256'), 'tokens digest')
                        if a.get('clock_discontinuity_ms') is not None:
                            number(a['clock_discontinuity_ms'], 'clock discontinuity', 0, 1000)
                        if a.get('finish_reason') not in ('stop', 'length') or not a.get('run_id'):
                            raise ValueError('missing run provenance')
                    except ValueError:
                        reasons.append(arm + ': invalid timing or output')
                        ok = False
                valid.append(ok)
            if all(pair) and all('start_monotonic_ns' in a and 'end_monotonic_ns' in a for a in pair):
                try:
                    for a in pair:
                        start = number(a['start_monotonic_ns'], 'start clock', 0, 1e20)
                        end = number(a['end_monotonic_ns'], 'end clock', start, 1e20)
                        if abs((end-start)/1e6-a['duration_ms']) > 1:
                            raise ValueError('clock duration mismatch')
                    first, second = pair if p['order'] == 'AB' else pair[::-1]
                    if first['end_monotonic_ns'] > second['start_monotonic_ns']:
                        raise ValueError('overlap or order mismatch')
                except (ValueError, TypeError, KeyError):
                    valid = [False, False]
                    reasons.append('clock interval or realized order invalid')
            equal = bool(all(pair) and all(a['status'] == 'completed' for a in pair)
                         and pair[0].get('tokens_sha256') and pair[0].get('tokens_sha256') == pair[1].get('tokens_sha256')
                         and pair[0].get('token_count') == pair[1].get('token_count')
                         and pair[0].get('finish_reason') == pair[1].get('finish_reason'))
            if all(pair) and all(a['status'] == 'completed' for a in pair) and not equal:
                counts['mismatched_pairs'] += 1
                reasons.append('output mismatch: neither arm has an external correctness oracle')
            # Delivered service includes fallback overhead; never use it to credit device acceleration.
            if equal and all(r in ('host: fallback', 'candidate: fallback') for r in reasons):
                try:
                    durations = [number(a.get('duration_ms'), 'service duration', .000001) for a in pair]
                    firsts = [number(a.get('ttft_ms'), 'service TTFT', 0, duration) for a, duration in zip(pair, durations)]
                    if all(a.get('scope_sha256') == scope_hash and a.get('prompt_sha256') == p['prompt_sha256'] and a.get('max_tokens') == p['max_tokens'] for a in pair):
                        service_time_rows.append((sid, durations[0]-durations[1]))
                        service_ttft_rows.append((sid, firsts[1]-firsts[0]))
                except ValueError:
                    pass
            # Both arms unverified if comparator absent/mismatched. Do not invent which is correct.
            strict = [v and equal for v in valid]
            for arm, ok in zip(('host', 'candidate'), strict):
                reliability[arm]['correct'] += int(ok)
                reliability[arm]['strict_success'] += int(ok)
            reliability_rows.append((sid, int(strict[1])-int(strict[0])))
            completion_rows.append((sid, int(bool(pair[1] and pair[1]['status'] == 'completed'))-int(bool(pair[0] and pair[0]['status'] == 'completed'))))
            if not all(valid) or not equal:
                counts['invalid_pairs'] += 1
                exclusions.append({'pair_id': sid+'/'+p['id'], 'reasons': reasons or ['output equivalence unverified']})
                continue
            a, b = pair
            saved, ttft = a['duration_ms']-b['duration_ms'], b['ttft_ms']-a['ttft_ms']
            time_rows.append((sid, saved))
            percent_rows.append((sid, 100*saved/a['duration_ms']))
            ttft_rows.append((sid, ttft))
            points.append({'session': sid, 'pair_id': p['id'], 'order': p['order'], 'time_saved_ms': saved, 'ttft_change_ms': ttft})
            ea, erra = energy(a.get('energy'), a['duration_ms'])
            eb, errb = energy(b.get('energy'), b['duration_ms'])
            if ea and eb and ea['identity'] == eb['identity']:
                energy_rows.append((sid, ea['joules']-eb['joules']))
                points[-1]['energy_saved_joules'] = ea['joules']-eb['joules']
                points[-1]['meter'] = ea['identity']
                points[-1]['calibration_relative_uncertainty'] = [ea['calibration_relative_uncertainty'], eb['calibration_relative_uncertainty']]
            else:
                energy_reasons.update(x for x in (erra, errb, 'meter scope differs' if ea and eb else None) if x)
    for r in reliability.values():
        r['completion_rate'] = r['completed']/r['planned']
        r['strict_success_rate'] = r['strict_success']/r['planned']
        r['wilson95'] = wilson(r['completed'], r['planned'])
        r['wilson_scope'] = 'IID descriptive only; session correlation is not modeled'
    reliability['completion_change'] = estimate(completion_rows, statistics.mean)
    reliability['strict_success_change'] = estimate(reliability_rows, statistics.mean)
    reliability['completion_change_definition'] = 'candidate minus host completed fraction, all planned pairs; fallback may have completed'
    counts['eligible_pairs'], counts['clusters'] = len(time_rows), len(set(s for s, _ in time_rows))
    saved, percent, ttft = estimate(time_rows), estimate(percent_rows), estimate(ttft_rows)
    reasons = []
    verdict = 'inconclusive'
    if kind in ('control', 'synthetic'):
        verdict = 'control_only'
        reasons.append('Control or synthetic evidence cannot establish device acceleration.')
    elif counts['mismatched_pairs']:
        verdict = 'invalid_comparison'
        reasons.append('Output mismatch prevents a speedup claim.')
    elif counts['clusters'] < MIN_CLUSTERS or len(time_rows) < 30:
        verdict = 'insufficient_evidence'
        reasons.append('At least 10 independent sessions and 30 eligible pairs are required for the descriptive decision rule.')
    elif not saved['ci95'] or not percent['ci95'] or not ttft['ci95']:
        verdict = 'insufficient_evidence'
        reasons.append('Degenerate sampling intervals cannot establish uncertainty.')
    elif counts['invalid_pairs']:
        reasons.append('Excluded planned pairs block an improvement verdict; inspect reliability and exclusions.')
    elif saved['ci95'][0] > 0 and percent['ci95'][0] > 5 and ttft['ci95'][1] <= 0:
        verdict = 'observed_improvement'
        reasons.append('Recorded paired time exceeds the fixed 5% margin without observed TTFT deterioration.')
    elif saved['ci95'][1] < 0 or ttft['ci95'][0] > 0:
        verdict = 'observed_regression'
        reasons.append('Recorded duration or TTFT interval indicates deterioration.')
    else:
        reasons.append('Intervals do not resolve the fixed time and TTFT criteria.')
    statistical_signal = verdict
    if kind not in ('control', 'synthetic') and verdict in ('observed_improvement', 'observed_regression'):
        verdict = 'insufficient_evidence'
        reasons.append('Directional sample signal only: execution mode, residency and independent-session qualification are not attested.')
    gates = {
        'output_equivalence': 'pass' if not counts['invalid_pairs'] else 'blocked',
        'sample_size': 'pass' if counts['clusters'] >= MIN_CLUSTERS and len(time_rows) >= 30 else 'blocked',
        'execution_attestation': 'blocked', 'residency_control': 'blocked',
        'session_independence': 'unverified',
        'energy_coverage': 'pass' if len(energy_rows) == counts['planned_pairs'] else 'blocked',
        'routing_promotion': 'disabled',
    }
    return dict(schema_version=1, algorithm=VERSION, scope=scope, verdict=verdict, reasons=reasons,
                counts=counts, time_saved_ms=saved, time_saved_percent=percent, ttft_change_ms=ttft,
                energy_saved_joules=estimate(energy_rows) if energy_rows else None,
                service_time_saved_ms=estimate(service_time_rows), service_ttft_change_ms=estimate(service_ttft_rows),
                service_scope='Completed output-equivalent pairs including fallback; missing/failed attempts remain in reliability, with no imputed duration.',
                reliability=reliability, energy={'status': 'measured' if len(energy_rows) == counts['planned_pairs'] else 'partial' if energy_rows else 'unavailable',
                'valid_pairs': len(energy_rows), 'planned_pairs': counts['planned_pairs'], 'reasons': sorted(energy_reasons)},
                evidence={'kind': kind, 'clock': 'client_sse_first_nonempty_text',
                          'confidence_method': 'session_cluster_percentile_bootstrap',
                          'confidence_scope': 'Approximate sampling uncertainty only; not measurement uncertainty or a guarantee.'},
                qualified_recommendation=False, statistical_signal=statistical_signal, gates=gates, policy={'minimum_sessions': MIN_CLUSTERS, 'minimum_pairs': 30,
                'time_margin_percent': 5, 'ttft_regression_tolerance_ms': 0, 'bootstrap_replicates': BOOTSTRAPS, 'seed': SEED},
                exclusions=exclusions, paired_observations=points, limitations=LIMITATIONS)
