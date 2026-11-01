#!/usr/bin/env python3
"""Read-only setup inventory. Does not load libraries, read credentials or run models."""
import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect(root=ROOT):
    checks = []

    def add(name, state, required, detail, remediation=''):
        checks.append(dict(name=name, state=state, required=required,
                           detail=detail, remediation=remediation))

    add('python', 'present' if sys.version_info >= (3, 12) else 'missing', True,
        platform.python_version(), 'Use Python 3.12 or newer.')
    host = platform.system(), platform.machine()
    add('host', 'reference_platform' if host[0] == 'Darwin' and host[1] in ('arm64', 'aarch64') else 'unqualified',
        False, ' / '.join(host), 'Only Apple Silicon macOS has recorded native host evidence; qualify other hosts separately.')
    for name, commands, required, instruction in (
        ('git', ('git',), True, 'Install Git.'),
        ('cmake', ('cmake',), True, 'Install CMake 3.22+ or set NODELIFT_CMAKE.'),
        ('cxx', ('clang++', 'g++', 'c++'), True, 'Install a C++17 compiler / Xcode command-line tools.'),
        ('openssl', ('openssl',), True, 'Install OpenSSL for the local TLS identity.'),
        ('node', ('node',), False, 'Install Node.js to develop the LM Studio adapter.'),
        ('adb', ('adb',), False, 'ADB is optional for Android development; pairing uses the local network.'),
        ('xcodegen', ('xcodegen',), False, 'xcodegen and Xcode are needed only for iOS builds.'),
    ):
        if name == 'cmake':
            commands = (os.environ.get('NODELIFT_CMAKE') or 'cmake',)
        found = any(shutil.which(command) for command in commands)
        if name == 'cmake' and not found:
            fallback = Path.home() / 'Library/Android/sdk/cmake/3.22.1/bin/cmake'
            found = fallback.is_file() and os.access(fallback, os.X_OK)
        add(name, 'present' if found else 'missing', required,
            'Executable found; version and runtime behavior not validated.' if found else 'Not found on the configured search path.', instruction)
    extension = 'dylib' if host[0] == 'Darwin' else 'so'
    native = Path(os.environ.get('NODELIFT_LIBRARY') or root / 'native/build/host/lib' / ('libnodelift.' + extension))
    add('native_library', 'present_unverified' if native.is_file() else 'missing', False,
        'File present; not loaded by this command.' if native.is_file() else 'Native host library has not been located.',
        'Run ./scripts/build-native.sh, then the documented real-weight checks.')
    missing = [row['name'] for row in checks if row['required'] and row['state'] == 'missing']
    return {'schema_version': 1, 'scope': 'read-only setup inventory',
            'build_prerequisites_found': not missing, 'missing_required': missing,
            'inference_qualified': False, 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Print a portable report without local paths or credentials.')
    parser.add_argument('--strict', action='store_true', help='Exit 1 if a required build prerequisite is missing.')
    args = parser.parse_args()
    report = inspect()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print('NodeLift setup inventory: no model or native library was executed.\n')
        for check in report['checks']:
            print(f"{check['name']}: {check['state']}: {check['detail']}")
            if check['state'] in ('missing', 'unqualified'):
                print('  ' + check['remediation'])
        print('\nPresence is not a version check, successful inference or phone qualification.')
    return 1 if args.strict and report['missing_required'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
