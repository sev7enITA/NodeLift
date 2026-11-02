#!/usr/bin/env python3
"""Build the experimental macOS host on the target Mac."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--native-library', required=True, type=Path)
parser.add_argument('--llama-license', required=True, type=Path)
parser.add_argument('--output-dir', required=True, type=Path)
args = parser.parse_args()
if sys.platform != 'darwin' or args.native_library.name != 'libnodelift.dylib':
    parser.error('this host preview must be built on macOS with libnodelift.dylib')
if not args.native_library.is_file() or not args.llama_license.is_file():
    parser.error('the native library and upstream license are required')
if importlib.metadata.version('pyinstaller') != '6.22.3':
    parser.error('build requires PyInstaller 6.22.3')
python_license = next((p for p in (Path(sysconfig.get_path('stdlib'))/'LICENSE.txt',
                                    Path(sys.base_prefix)/'LICENSE.txt') if p.is_file()), None)
dist = importlib.metadata.distribution('pyinstaller')
pyi_license = next((Path(dist.locate_file(p)) for p in (dist.files or [])
                    if str(p).endswith('licenses/COPYING.txt')), None)
if not python_license or not pyi_license or not pyi_license.is_file():
    parser.error('Python and PyInstaller license files must be available')
args.output_dir.mkdir(parents=True, exist_ok=True)
output = args.output_dir/'NodeLift-host'
if output.exists():
    parser.error('output exists; use a fresh output directory')
with tempfile.TemporaryDirectory(prefix='nodelift-host-build-') as tmp:
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile',
           '--name', 'NodeLift-host', '--paths', str(ROOT/'host'),
           '--distpath', str(args.output_dir.resolve()), '--workpath', str(Path(tmp)/'work'),
           '--specpath', tmp, '--add-binary', str(args.native_library.resolve())+os.pathsep+'native']
    for name in ('dashboard.html', 'dashboard.css', 'dashboard.js', 'i18n.js',
                 'graph.js', 'models.js', 'pairing.js'):
        cmd += ['--add-data', str((ROOT/'host/nodelift'/name).resolve())+os.pathsep+'nodelift']
    for path, target in ((ROOT/'host/nodelift/vendor/qrcodegen.js', 'nodelift/vendor'),
                         (ROOT/'assets/brand', 'assets/brand'),
                         (ROOT/'native/llama.lock', 'native'),
                         (ROOT/'LICENSE', 'licenses/nodelift'),
                         (args.llama_license, 'licenses/llama-cpp'),
                         (python_license, 'licenses/python'), (pyi_license, 'licenses/pyinstaller')):
        cmd += ['--add-data', str(path.resolve())+os.pathsep+target]
    cmd.append(str(ROOT/'scripts/standalone-host.py'))
    subprocess.run(cmd, check=True)
    subprocess.run([str(output.resolve()), '--self-check'], check=True)
print(json.dumps({'output': str(output), 'bytes': output.stat().st_size,
                  'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))
