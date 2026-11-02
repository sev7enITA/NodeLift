#!/usr/bin/env python3
"""Local resident-model segmentation pilot. No network or companion execution."""
import argparse
import hashlib
import json
import random
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'host'))
from nodelift.native import Native, library_path

SEED = 20261102
KEYS = ('record_id', 'owner', 'due_date', 'status')
FIXTURES = [
    {'id': 'R101', 'source': 'Maintenance record R101. Owner: Mira. Due date: 2026-12-03. Current status: open. Replace the north entrance sensor. The south entrance is not part of this job.',
     'expected': dict(zip(KEYS, ('R101', 'Mira', '2026-12-03', 'open')))},
    {'id': 'R102', 'source': 'Maintenance record R102. Owner: Tomas. Due date: 2026-12-05. The current status is closed. The pump was inspected and the receipt was filed. R101 is another job and is still open.',
     'expected': dict(zip(KEYS, ('R102', 'Tomas', '2026-12-05', 'closed')))},
    {'id': 'R103', 'source': 'Maintenance record R103. Owner: Hana. Due date: not assigned. Current status: blocked. A replacement part is pending. There is no due date for this record.',
     'expected': dict(zip(KEYS, ('R103', 'Hana', None, 'blocked')))},
    {'id': 'R104', 'source': 'Maintenance record R104. Original due date: 2026-12-01. Update: the due date is now 2026-12-09, replacing the original date. Owner: Luca. Current status: open. Use the updated due date.',
     'expected': dict(zip(KEYS, ('R104', 'Luca', '2026-12-09', 'open')))},
    {'id': 'R105', 'source': 'Maintenance record R105. Owner: not assigned. Due date: 2026-12-11. Current status: open. Mira is the requester, not the owner. Nobody has been assigned to carry out this job.',
     'expected': dict(zip(KEYS, ('R105', None, '2026-12-11', 'open')))},
    {'id': 'R106', 'source': 'Maintenance record R106. Owner: Noor. Due date: 2026-12-12. Previous status: blocked. Current status: closed. The dependency was resolved and the work completed. Use the current status.',
     'expected': dict(zip(KEYS, ('R106', 'Noor', '2026-12-12', 'closed')))},
]


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest_file(path):
    with Path(path).open('rb') as stream:
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
        return h.hexdigest()


def payload(fixture, scope):
    records = FIXTURES if scope == 'full' else [fixture]
    instruction = (
        f'Extract only maintenance record {fixture["id"]}. '
        'Return one JSON object with exactly these four keys: record_id, owner, due_date, status. '
        'Use the current or updated values, not superseded values. '
        'All values must be strings, except an unassigned owner or due date must be JSON null. '
        'Use YYYY-MM-DD for dates. Do not use markdown or add explanations.\n\n'
    )
    return {
        'task_id': fixture['id'],
        'instruction': instruction,
        'sources': [x['source'] for x in records],
        'output_contract': 'maintenance-record-v1',
        'max_output_tokens': 96,
    }


def score(text, expected):
    # Reject duplicate keys, non-JSON output, wrong types and omitted fields.
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    try:
        value = json.loads(text, object_pairs_hook=unique)
    except (ValueError, TypeError):
        return {'schema_valid': False, 'correct': False}
    schema = (isinstance(value, dict) and set(value) == set(KEYS)
              and all(isinstance(v, str) or v is None for v in value.values()))
    return {'schema_valid': schema, 'correct': schema and value == expected}


def task(engine, fixture, scope):
    message = payload(fixture, scope)
    body = encoded(message)
    row = {'record_id': fixture['id'], 'scope': scope, 'payload_bytes': len(body),
           'payload_sha256': hashlib.sha256(body).hexdigest(), 'status': 'failed',
           'schema_valid': False, 'correct': False}
    start = time.perf_counter()
    try:
        # Parse the same message a future task worker would receive; no transport
        # or security protocol is implemented by this local probe.
        request = json.loads(body)
        prompt = request['instruction'] + '\n\n'.join(request['sources'])
        engine.call('reset')
        prefix = engine.call('tokenize', text=prompt, chat=True)['tokens']
        if len(prefix) + request['max_output_tokens'] >= 2048:
            raise ValueError('context budget exceeded')
        prefill_start = time.perf_counter()
        prefill = engine.call('prefill', prefix=prefix)
        row.update(prompt_tokens=len(prefix), prefill_native_ms=prefill['ms'],
                   prefill_wall_ms=(time.perf_counter() - prefill_start) * 1000)
        first = engine.call('draft', prefix=prefix, count=1)
        tokens = first['tokens']
        if not tokens:
            raise ValueError('no first token')
        row['first_token_ready_ms'] = (time.perf_counter() - start) * 1000
        result = first
        if not first['eos']:
            result = engine.call('draft', prefix=prefix + tokens,
                                 count=request['max_output_tokens'] - len(tokens))
            tokens += result['tokens']
        text = bytes.fromhex(engine.call('text', tokens=tokens)['bytes_hex']).decode('utf-8')
        row.update(status='completed', output=text, output_tokens=len(tokens),
                   output_tokens_sha256=hashlib.sha256(encoded(tokens)).hexdigest(),
                   finish_reason='stop' if result['eos'] else 'length')
        row.update(score(text, fixture['expected']))
        row['response_payload_bytes'] = len(encoded({'task_id': fixture['id'], 'output': text}))
    except Exception as error:
        row['error_type'] = type(error).__name__
    row['task_wall_ms'] = (time.perf_counter() - start) * 1000
    return row


def median(rows, key):
    values = [r[key] for r in rows if r.get(key) is not None]
    return statistics.median(values) if values else None


def summarize(rows):
    cells = {}
    for model in ('small', 'target'):
        for scope in ('full', 'segment'):
            selected = [r for r in rows if r['model'] == model and r['scope'] == scope]
            completed = [r for r in selected if r['status'] == 'completed']
            cells[f'{model}_{scope}'] = {
                'attempted': len(selected), 'completed': len(completed),
                'correct': sum(r['correct'] for r in selected),
                'schema_valid': sum(r['schema_valid'] for r in selected),
                'median_completed_task_ms': median(completed, 'task_wall_ms'),
                'median_completed_first_token_ms': median(completed, 'first_token_ready_ms'),
                'median_completed_prefill_ms': median(completed, 'prefill_wall_ms'),
                'median_request_payload_bytes': median(selected, 'payload_bytes'),
            }
    pairs = []
    for model in ('small', 'target'):
        for f in FIXTURES:
            for rep in range(2):
                group = {r['scope']: r for r in rows
                         if r['model'] == model and r['record_id'] == f['id'] and r['repetition'] == rep}
                if len(group) != 2:
                    continue
                full, segment = group['full'], group['segment']
                both_complete = full['status'] == segment['status'] == 'completed'
                pairs.append({'model': model, 'record_id': f['id'], 'repetition': rep,
                              'both_complete': both_complete,
                              'both_correct': full['correct'] and segment['correct'],
                              'task_time_ratio_full_over_segment': full['task_wall_ms'] / segment['task_wall_ms'] if both_complete else None,
                              'payload_reduction_fraction': 1 - segment['payload_bytes'] / full['payload_bytes']})
    return {'cells': cells, 'pairs': pairs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--small', type=Path, default=ROOT / '.models/qwen2.5-0.5b-instruct-q4_k_m.gguf')
    parser.add_argument('--target', type=Path, default=ROOT / '.models/qwen2.5-1.5b-instruct-q4_k_m.gguf')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    paths = {'small': args.small.resolve(), 'target': args.target.resolve()}
    models = {name: {'file': path.name, 'sha256': digest_file(path)} for name, path in paths.items()}
    rng = random.Random(SEED)
    blocks = [(i, rep) for i in range(len(FIXTURES)) for rep in range(2)]
    rng.shuffle(blocks)
    plan = []
    for index, rep in blocks:
        cells = [(model, scope) for model in ('small', 'target') for scope in ('full', 'segment')]
        rng.shuffle(cells)
        plan.extend({'fixture': index, 'repetition': rep, 'model': model, 'scope': scope} for model, scope in cells)
    report = {'schema_version': 1, 'evidence_kind': 'same-Mac native feasibility probe',
              'started_utc': datetime.now(timezone.utc).isoformat(), 'seed': SEED,
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'script_sha256': digest_file(__file__), 'plan_sha256': digest_file(Path(__file__).with_name('PLAN.md')),
              'library_sha256': digest_file(library_path()), 'models': models,
              'config': {'n_ctx': 2048, 'threads_requested': 8, 'gpu_layers_requested': 999,
                         'kv_reset_each_task': True, 'both_models_resident': True, 'max_output_tokens': 96},
              'fixtures': FIXTURES, 'plan': plan, 'warmup': [], 'rows': [],
              'physical_nodes': 'not used', 'transport': 'none; serialized payload size only',
              'energy': None, 'limitations': ['six synthetic fixtures, two dependent repetitions',
                  'different model sizes are not equivalent inference', 'no network, phone or task concurrency',
                  'offline answer key is not a runtime verifier', 'no general quality guarantee']}
    def save():
        (args.output / 'results.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    engines = {}
    save()
    try:
        for name, path in paths.items():
            engine = Native()
            engines[name] = engine
            started = time.perf_counter()
            models[name]['runtime'] = engine.call('load', path=str(path), n_ctx=2048, threads=8, gpu_layers=999)
            models[name]['load_ms'] = (time.perf_counter() - started) * 1000
            save()
        warmup = {'id': 'W100', 'source': 'Maintenance record W100. Owner: Ada. Due date: 2026-12-02. Current status: open.',
                  'expected': dict(zip(KEYS, ('W100', 'Ada', '2026-12-02', 'open')))}
        # Full warmup includes a real collection record so its answer is present.
        for model in engines:
            for scope in ('full', 'segment'):
                fixture = FIXTURES[0] if scope == 'full' else warmup
                row = task(engines[model], fixture, scope)
                row['model'] = model
                report['warmup'].append(row)
                save()
        for step in plan:
            row = task(engines[step['model']], FIXTURES[step['fixture']], step['scope'])
            row.update(model=step['model'], repetition=step['repetition'])
            report['rows'].append(row)
            save()
            print(json.dumps({k: row[k] for k in ('model', 'record_id', 'scope', 'correct', 'task_wall_ms')}), flush=True)
    finally:
        for engine in engines.values():
            engine.close()
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        report['summary'] = summarize(report['rows'])
        save()
    print(json.dumps(report['summary']['cells'], indent=2))


if __name__ == '__main__':
    main()
