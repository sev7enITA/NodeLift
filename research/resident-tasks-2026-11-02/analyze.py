"""Reproduce pilot summaries and an explicitly post-hoc format diagnostic."""
import json
import re
import statistics
from pathlib import Path
from probe import FIXTURES, score

HERE = Path(__file__).resolve().parent
report = json.loads((HERE / 'local-pilot/results.json').read_text())
assert len(report['rows']) == len(report['plan']) == 48
cells = {}
for model in ('small', 'target'):
    for scope in ('full', 'segment'):
        rows = [r for r in report['rows'] if r['model'] == model and r['scope'] == scope]
        diagnostic = []
        for row in rows:
            # Diagnostic only: never overwrite the predeclared strict score.
            match = re.fullmatch(r'```json\s*([\s\S]*?)\s*```\s*', row.get('output', ''))
            text = match.group(1) if match else row.get('output', '')
            expected = next(f['expected'] for f in FIXTURES if f['id'] == row['record_id'])
            diagnostic.append({'record_id': row['record_id'], 'repetition': row['repetition'],
                               'removed_one_markdown_fence': bool(match), **score(text, expected)})
        cells[f'{model}_{scope}'] = {
            **report['summary']['cells'][f'{model}_{scope}'],
            'median_output_tokens': statistics.median(r['output_tokens'] for r in rows),
            'posthoc_correct_after_fence_removal': sum(x['correct'] for x in diagnostic),
            'posthoc_diagnostic': diagnostic,
        }
ratios = {}
for model in ('small', 'target'):
    pairs = [x for x in report['summary']['pairs'] if x['model'] == model]
    ratios[model] = {
        'planned_pairs': 12, 'complete_pairs': sum(x['both_complete'] for x in pairs),
        'strictly_correct_pairs': sum(x['both_correct'] for x in pairs),
        'median_raw_time_ratio_full_over_segment': statistics.median(x['task_time_ratio_full_over_segment'] for x in pairs),
        'median_request_payload_reduction': statistics.median(x['payload_reduction_fraction'] for x in pairs),
        'valid_workflow_speedup': None,
    }
summary = {'cells': cells, 'pairs': ratios,
           'posthoc_warning': 'Fence removal was added after seeing outputs. Primary strict scores stay unchanged. '
                              'Six unique fixtures repeated twice, no held-out quality estimate. '
                              'Times include invalid outputs and different output lengths; no usable workflow speedup.'}
(HERE / 'analysis.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({'pairs': ratios, 'primary_valid_outputs': sum(x['correct'] for x in report['rows'])}))
