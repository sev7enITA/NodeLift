#!/usr/bin/env python3
"""Build a native, self-contained probe on the target operating system."""
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
parser.add_argument('--llama-bench', required=True, type=Path)
parser.add_argument('--llama-license', required=True, type=Path)
parser.add_argument('--output-dir', required=True, type=Path)
args = parser.parse_args()
for path in (args.llama_bench, args.llama_license):
    if not path.is_file():
        parser.error('benchmark executable and upstream license must exist')
if importlib.metadata.version('pyinstaller') != '6.22.3':
    parser.error('build requires PyInstaller 6.22.3')
args.output_dir.mkdir(parents=True, exist_ok=True)
name = 'NodeLift-node' + ('.exe' if os.name == 'nt' else '')
output = args.output_dir / name
if output.exists():
    parser.error('output exists; use a fresh output directory')
binary_name = 'llama-bench.exe' if os.name == 'nt' else 'llama-bench'
if args.llama_bench.name != binary_name:
    parser.error('benchmark must use its standard platform filename')
python_license = next((p for p in (Path(sysconfig.get_path('stdlib'))/'LICENSE.txt',
                                    Path(sys.base_prefix)/'LICENSE.txt') if p.is_file()), None)
dist = importlib.metadata.distribution('pyinstaller')
pyinstaller_license = next((Path(dist.locate_file(p)) for p in (dist.files or [])
                             if str(p).endswith('licenses/COPYING.txt')), None)
if not python_license or not pyinstaller_license or not pyinstaller_license.is_file():
    parser.error('Python and PyInstaller license files must be available for redistribution')
with tempfile.TemporaryDirectory(prefix='nodelift-node-build-') as tmp:
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile',
           '--name', 'NodeLift-node', '--paths', str(ROOT/'host'),
           '--distpath', str(args.output_dir.resolve()), '--workpath', str(Path(tmp)/'work'),
           '--specpath', tmp, '--add-binary', str(args.llama_bench.resolve())+os.pathsep+'native',
           '--add-data', str((ROOT/'LICENSE').resolve())+os.pathsep+'licenses/nodelift',
           '--add-data', str(args.llama_license.resolve())+os.pathsep+'licenses/llama-cpp',
           '--add-data', str(python_license.resolve())+os.pathsep+'licenses/python',
           '--add-data', str(pyinstaller_license.resolve())+os.pathsep+'licenses/pyinstaller',
           str(ROOT/'scripts/standalone-node.py')]
    subprocess.run(cmd, check=True)
    subprocess.run([str(output.resolve()), '--self-check'], check=True)
print(json.dumps({'output': str(output), 'bytes': output.stat().st_size,
                  'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                  'pyinstaller': importlib.metadata.version('pyinstaller')}))
