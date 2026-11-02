#!/usr/bin/env python3
"""Explain retained fixed-delegation costs. No simulated result is a speedup."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path


def explain(path):
    raw = json.loads(path.read_text())
    if raw.get('scope', {}).get('candidate') != 'remote_draft' or any(
        s.get('configuration', {}).get('draft_policy') != 'fixed' for s in raw['sessions']
    ):
        raise ValueError('Cost diagnosis requires fixed remote-draft sessions')
    candidates, hosts, eligible = [], [], []
    planned = sum(len(s['plan']) for s in raw['sessions'])
    for session in raw['sessions']:
        for pair in session['plan']:
            arms = {a['arm']: a for a in session['attempts'] if a['pair_id'] == pair['id']}
            candidates += [arms['candidate']] if 'candidate' in arms else []
            hosts += [arms['host']] if 'host' in arms else []
            if len(arms) != 2 or any(a['status'] != 'completed' for a in arms.values()):
                continue
            h, c = arms['host'], arms['candidate']
            if all(h[f] == c[f] for f in ('tokens_sha256', 'token_count', 'finish_reason')) and not c['fallback']:
                eligible.append((h, c))
    result = {'source': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'planned_pairs': planned, 'observed_candidate': len(candidates),
              'fallbacks': sum(bool(a.get('fallback')) for a in candidates),
              'eligible_clean_pairs': len(eligible),
              'scope': 'Clean matched-output fixed cells only. Failures, missing attempts and fallback remain in the denominator; no confidence qualification.'}
    if not eligible:
        result['block_cost'] = None
        return result
    cb = [b for _, c in eligible for b in c['blocks']]
    hb = [b for h, _ in eligible for b in h['blocks']]
    if any(b.get('round_ms') is None or b.get('draft_ms') is None for b in cb + hb):
        result['block_cost'] = None
        return result
    committed = sum(b['generated'] for b in cb)
    baseline = sum(b['round_ms'] for b in hb) / sum(b['generated'] for b in hb)
    round_total = sum(b['round_ms'] for b in cb)
    wait = sum(b['draft_ms'] for b in cb)
    residual = round_total - wait
    result['block_cost'] = {
        'blocks': len(cb), 'committed_tokens': committed,
        'candidate_ms_per_committed_token': round_total / committed,
        'host_ms_per_committed_token': baseline,
        'remote_wait_fraction': wait / round_total,
        'remote_wait_ms_per_block': wait / len(cb),
        'non_remote_ms_per_committed_token': residual / committed,
        'remote_budget_ms_per_block_at_current_acceptance': (baseline * committed - residual) / len(cb),
        'budget_definition': 'Descriptive break-even headroom with current committed counts and non-remote costs held fixed; not a prediction, confidence bound or routing authorization.',
        'remote_components': 'Unresolved: phone computation, dispatch, transfer and result handling. Not network RTT.',
    }
    result['end_to_end_median_paired_ratio'] = statistics.median(c['duration_ms']/h['duration_ms'] for h, c in eligible)
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = {'cells': [explain(p) for p in args.inputs], 'new_inference_runs': 0,
              'qualified_recommendation': False, 'energy': 'unmeasured'}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
