"""Read-only analysis of published DistAI data; never imports/runs upstream code.

Run: python3 research/distai/verify_evidence.py
This checks arithmetic and provenance, not inference performance on our hardware.
"""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def rows(name):
    return [json.loads(line) for line in (ROOT / 'source/tools' / name).read_text().splitlines() if line.strip()]


def main():
    provenance = json.loads((ROOT / 'provenance.json').read_text())
    files = []
    for entry in provenance['tree_entries']:
        path = ROOT / 'source' / entry['path']
        if not path.is_file():
            continue
        data = path.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        files.append({'path': entry['path'], 'matches_upstream': blob == entry['git_blob_sha']})
    quality = rows('results-codeeval.jsonl')
    optim = rows('results-ottimizzazione.jsonl')
    prefill = rows('results-prefill.jsonl')
    seq, batched, cluster = quality[-3:]
    # Parse literal task definitions only; no exec, eval, or import of upstream code.
    tree = ast.parse((ROOT / 'source/tools/codeeval.py').read_text())
    tasks = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
            if any(isinstance(t, ast.Name) and t.id in ('TASKS', 'HARD') for t in node.targets):
                tasks.extend(ast.literal_eval(node.value))
    group_task = next(t for t in tasks if t[0] == 'group_anagrams')
    statement = ast.parse(group_task[3]).body[-1]
    expected = ast.literal_eval(statement.test.comparators[0])
    reference = sorted(sorted(group) for group in [['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']])
    projections = []
    for run in prefill:
        if '7B Q4_K_M, PC 14 layer' in run['label']:
            measurements = run['rows']
            last = measurements[-1]
            mean_tps = sum(r['gen_tps'] for r in measurements) / len(measurements)
            projections.append({
                'label': run['label'],
                'observed_generation_lengths': [r['gen_n'] for r in measurements],
                'projected_300_token_turn_using_script_formula_s': last['n'] / last['prompt_tps'] + 300 / mean_tps,
                'projected_300_token_turn_using_long_context_rate_s': last['prompt_ms'] / 1000 + 300 / last['gen_tps'],
                'note': 'Both are extrapolations from shorter runs, not measured 300-token end-to-end turns.'
            })
    result = {
        'kind': 'published-data arithmetic and static inspection; NOT a new hardware benchmark',
        'commit': provenance['commit'],
        'source_files': len(files),
        'all_source_blobs_match': all(f['matches_upstream'] for f in files),
        'published_rows': {'quality': len(quality), 'optimization': len(optim), 'prefill': len(prefill)},
        'optimization_rows_with_error_field': sum(bool(r.get('error')) for r in optim),
        'queue_comparison': {
            'sequential_host_s': seq['wall_s'], 'batched_host_s': batched['wall_s'], 'cluster_s': cluster['wall_s'],
            'speedup_vs_sequential': seq['wall_s'] / cluster['wall_s'],
            'speedup_vs_batched': batched['wall_s'] / cluster['wall_s'],
            'wall_time_reduction_vs_batched_pct': 100 * (1 - cluster['wall_s'] / batched['wall_s']),
            'passed': [r['passed'] for r in (seq, batched, cluster)],
            'total': [r['total'] for r in (seq, batched, cluster)],
            'note': 'One published batch per setup; no confidence interval or independent replication.'
        },
        'group_anagrams_suspected_oracle_error': {
            'confirmed': False, 'expected': expected, 'reference': reference,
            'oracle_matches_correct_reference': expected == reference,
            'note': 'Initial suspicion withdrawn; do not report this as a defect.'
        },
        'prefill_turn_projections': projections,
        'diffusion_results_file_in_published_tree': any(e['path'] == 'tools/results-dllm.jsonl' for e in provenance['tree_entries']),
    }
    output = ROOT / 'evidence-checks.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
