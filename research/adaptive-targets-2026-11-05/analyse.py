"""Derive paired results without treating repeated prompts as independent workloads."""
from pathlib import Path
import json, statistics, hashlib
import numpy as np

P = Path(__file__).resolve().parent
A = P.parents[1] / 'artifacts/adaptive-targets-2026-11-05'

def read(path):
    return json.loads(path.read_text())

def paired(directory):
    manifest = read(directory / 'manifest.json')
    rows = [json.loads(line) for line in (directory / 'runs.jsonl').read_text().splitlines()]
    expected = len(manifest['plan'])
    assert len(rows) == expected, (directory, len(rows), expected)
    assert all(r['status'] == 'completed' for r in rows)
    keys = [(r['rep'], r['prompt'], r['arm']) for r in rows]
    assert len(keys) == len(set(keys))
    hosts = {(r['rep'], r['prompt']): r for r in rows if r['arm'] == 'host'}
    pairs = []
    for r in rows:
        if r['arm'] == 'host':
            continue
        h = hosts[r['rep'], r['prompt']]
        trace = r['trace']
        phase_seconds = sum(x['draft_seconds'] + x['verify_seconds'] for x in trace)
        pairs.append({
            'arm': r['arm'], 'prompt': manifest['prompts'][r['prompt']]['id'],
            'block': manifest['block'], 'rep': r['rep'],
            'exact': r['tokens'] == h['tokens'] and r['finish'] == h['finish'],
            'speed_ratio': h['seconds'] / r['seconds'],
            'host_seconds': h['seconds'], 'candidate_seconds': r['seconds'],
            'saved_seconds': h['seconds'] - r['seconds'],
            'ttft_change_seconds': r['ttft_seconds'] - h['ttft_seconds'],
            'accepted_emitted_tokens': r['accepted_emitted_tokens'],
            'candidate_token_count': r['token_count'],
            'draft_disabled': r['draft_disabled'],
            'drafted_tokens': sum(x['k'] for x in trace) if trace else None,
            'discarded_or_unemitted_tokens': sum(x['k'] - x['accepted'] for x in trace) if trace else None,
            'draft_seconds': sum(x['draft_seconds'] for x in trace) if trace else None,
            'verify_seconds': sum(x['verify_seconds'] for x in trace) if trace else None,
            'unattributed_seconds': r['seconds'] - phase_seconds if trace else None,
            'candidate_swap_growth_bytes': r['swap_growth_bytes'],
            'host_swap_growth_bytes': h['swap_growth_bytes'],
        })
    return manifest, rows, pairs

def aggregate(pairs):
    output = []
    for arm in sorted({r['arm'] for r in pairs}):
        r = [x for x in pairs if x['arm'] == arm]
        prompt_ids = sorted({x['prompt'] for x in r})
        workloads = {p: statistics.median(x['speed_ratio'] for x in r if x['prompt'] == p) for p in prompt_ids}
        # Resample prompt clusters, not individual repeated trials.
        rng = np.random.default_rng(20261105)
        values = np.array(list(workloads.values()))
        bootstrap = np.median(rng.choice(values, size=(20000, len(values)), replace=True), axis=1)
        lo, hi = np.quantile(bootstrap, [.025, .975])
        blocks = {str(b): statistics.median(x['speed_ratio'] for x in r if x['block'] == b) for b in sorted({x['block'] for x in r})}
        exact = sum(x['exact'] for x in r)
        output.append({
            'arm': arm, 'pairs': len(r), 'exact_pairs': exact,
            'median_paired_speed_ratio': statistics.median(x['speed_ratio'] for x in r),
            'median_workload_speed_ratio': statistics.median(values),
            'workload_bootstrap_95_interval': [float(lo), float(hi)],
            'block_median_ratios': blocks, 'workload_median_ratios': workloads,
            'regressing_workloads': [p for p, v in workloads.items() if v < 1],
            'median_saved_seconds': statistics.median(x['saved_seconds'] for x in r),
            'median_paired_duration_change_percent': 100 * statistics.median(1 / x['speed_ratio'] - 1 for x in r),
            'median_ttft_change_seconds': statistics.median(x['ttft_change_seconds'] for x in r),
            'disabled_requests': sum(x['draft_disabled'] is True for x in r),
            'candidate_swap_growth_bytes': sum(x['candidate_swap_growth_bytes'] for x in r),
            'qualified': exact == len(r) and len(blocks) == 2 and all(v > 1.05 for v in blocks.values()) and lo > 1,
        })
    return output

def main():
    summary = {'scope': 'Same-Mac MLX prototype, not distributed inference', 'screening': {}, 'validation': {}}
    for name in ['14B-screen', '14B-fp32-screen']:
        _, _, pairs = paired(A / name)
        summary['screening'][name] = aggregate(pairs)
    all_pairs = []
    host_rows = []
    for block in [0, 1]:
        manifest, rows, pairs = paired(A / f'14B-fp32-validation-{block}')
        all_pairs.extend(pairs)
        host_rows.extend(row for row in rows if row['arm'] == 'host')
    summary['validation']['14B-fp32'] = aggregate(all_pairs)
    summary['host_repeat_equivalence'] = {
        manifest['prompts'][p]['id']: len({(tuple(r['tokens']), r['finish']) for r in host_rows if r['prompt'] == p}) == 1
        for p in range(8)
    }
    if not all(summary['host_repeat_equivalence'].values()):
        for arm in summary['validation']['14B-fp32']:
            arm['qualified'] = False
            arm['additional_disqualification'] = 'Host repeated output differs'
    summary['32B'] = {'status': 'not_admitted', **read(A / '32B-screen/admission.json')}
    out = P / 'results'
    out.mkdir(exist_ok=True)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (out / 'validation-pairs.json').write_text(json.dumps(all_pairs, indent=2) + '\n')
    print(json.dumps(summary['validation'], indent=2))

if __name__ == '__main__':
    main()
