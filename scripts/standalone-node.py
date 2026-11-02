#!/usr/bin/env python3
"""Self-contained NodeLift inventory and explicit native model benchmarks."""
import json
import os
from pathlib import Path
import secrets
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(ROOT / 'host'))
from nodelift import probe


def bundled_benchmark():
    if not getattr(sys, 'frozen', False):
        return None
    filename = 'llama-bench.exe' if os.name == 'nt' else 'llama-bench'
    return Path(sys._MEIPASS) / 'native' / filename


def startup_check():
    """Check bundled runtime availability, not model/backend performance."""
    exe = bundled_benchmark()
    status = 'missing'
    if exe and exe.is_file():
        status = probe.run_command([str(exe), '--help'], timeout=15)['status']
    return {'schema': 'nodelift.standalone-startup.v1',
            'embedded_python': bool(getattr(sys, 'frozen', False)),
            'standard_library': 'available',
            'bundled_llama_bench': status,
            'model': 'user_supplied', 'gpu_driver': 'not_installed_or_modified',
            'runtime_download': False, 'automatic_upload': False}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    check = startup_check()
    if args == ['--self-check']:
        print(json.dumps(check, indent=2))
        return 0 if check['embedded_python'] and check['bundled_llama_bench'] == 'ok' else 1
    print(json.dumps({'startup_check': check}), file=sys.stderr, flush=True)
    if not args:
        directory = Path.home() / 'Downloads'
        if not directory.is_dir():
            directory = Path.home()
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        output = directory / ('NodeLift-node-profile-' + stamp + '-' + secrets.token_hex(3) + '.json')
        args = ['inventory', '--output', str(output)]
        print('Saving the local hardware profile to: ' + str(output), file=sys.stderr, flush=True)
    if args[0] == 'benchmark' and '--executable' not in args:
        if check['bundled_llama_bench'] != 'ok':
            print('Bundled benchmark unavailable. Run --self-check or specify a trusted --executable.', file=sys.stderr)
            return 1
        args[1:1] = ['--executable', str(bundled_benchmark())]
    return probe.main(args)


if __name__ == '__main__':
    raise SystemExit(main())
