#!/usr/bin/env python3
"""Experimental self-contained macOS host with explicit startup checks."""
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(ROOT/'host'))


def startup_check():
    frozen = bool(getattr(sys, 'frozen', False))
    folder = Path(sys._MEIPASS) if frozen else ROOT
    library = folder/'native'/'libnodelift.dylib'
    result = {'schema': 'nodelift.standalone-host-startup.v1', 'embedded_python': frozen,
              'native_engine': 'missing', 'system_openssl': 'missing',
              'dashboard_assets': 'missing', 'engine_provenance': 'missing',
              'automatic_runtime_download': False,
              'model': 'user_supplied'}
    if sys.platform != 'darwin':
        result['platform'] = 'unsupported'
        return result
    if library.is_file():
        try:
            engine = ctypes.CDLL(str(library))
            for name in ('nl_create', 'nl_call', 'nl_free_string', 'nl_destroy', 'nl_cancel'):
                getattr(engine, name)
            result['native_engine'] = 'available'
        except (OSError, AttributeError):
            result['native_engine'] = 'load_failed'
    openssl = Path('/usr/bin/openssl')
    if openssl.is_file():
        try:
            p = subprocess.run([str(openssl), 'version'], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=10, check=False)
            result['system_openssl'] = 'available' if p.returncode == 0 else 'failed'
        except (OSError, subprocess.TimeoutExpired):
            result['system_openssl'] = 'failed'
    assets = folder/'nodelift'
    required = ('dashboard.html', 'dashboard.css', 'dashboard.js', 'i18n.js',
                'graph.js', 'models.js', 'pairing.js', 'vendor/qrcodegen.js')
    if all((assets/name).is_file() for name in required) and (folder/'assets/brand/nodelift-mark.svg').is_file():
        result['dashboard_assets'] = 'available'
    if (folder/'native/llama.lock').is_file():
        result['engine_provenance'] = 'available'
    return result


def main():
    check = startup_check()
    if sys.argv[1:] == ['--self-check']:
        print(json.dumps(check, indent=2))
        return 0 if check.get('embedded_python') and all(check[k] == 'available' for k in ('native_engine', 'system_openssl', 'dashboard_assets', 'engine_provenance')) else 1
    print(json.dumps({'startup_check': check}), flush=True)
    if not check.get('embedded_python') or any(check[k] != 'available' for k in ('native_engine', 'system_openssl', 'dashboard_assets', 'engine_provenance')):
        print('Host startup check failed. Repair or reinstall the standalone bundle.', file=sys.stderr)
        return 1
    os.environ['NODELIFT_LIBRARY'] = str(Path(sys._MEIPASS)/'native/libnodelift.dylib')
    os.environ['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin' + os.pathsep + os.environ.get('PATH', '')
    from nodelift.host import main as host_main
    host_main()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
