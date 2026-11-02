#!/usr/bin/env python3
"""Reject unoptimized Android inference kernels using actual compile commands."""
import argparse
import json
from pathlib import Path
import shlex

REQUIRED = {'core.cpp', 'ggml-cpu.c', 'ggml-cpu.cpp', 'quants.c'}
def audit(commands):
    rows = []
    for entry in commands:
        unit = Path(entry['file']).name
        if unit not in REQUIRED:
            continue
        args = entry.get('arguments') or shlex.split(entry['command'])
        optimizations = [v for v in args if v.startswith('-O')]
        effective = optimizations[-1] if optimizations else '-O0 (compiler default)'
        rows.append({'unit': unit, 'effective_optimization': effective,
                     'optimized': effective in ('-O2', '-O3'),
                     'fast_math': '-ffast-math' in args or '-Ofast' in args,
                     'isa': next((v for v in args if v.startswith('-march=')), None)})
    missing = sorted(REQUIRED - {r['unit'] for r in rows})
    return {'units': rows, 'missing': missing,
            'passed': bool(rows) and not missing and all(r['optimized'] and not r['fast_math'] for r in rows)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('compile_commands', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.compile_commands.read_text()))
    rendered = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end='')
    raise SystemExit(0 if result['passed'] else 1)
