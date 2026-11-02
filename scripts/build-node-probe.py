#!/usr/bin/env python3
"""Package the standard-library probe as a portable Python zip application."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import zipapp

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error('output already exists')
with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder)
    (folder/'nodelift_probe.py').write_bytes((ROOT/'host/nodelift/probe.py').read_bytes())
    (folder/'LICENSE').write_bytes((ROOT/'LICENSE').read_bytes())
    (folder/'__main__.py').write_text('from nodelift_probe import main\nraise SystemExit(main())\n')
    zipapp.create_archive(folder, args.output, interpreter='/usr/bin/env python3')
print(json.dumps({'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
                  'python_required':'3.10+', 'native_runtimes_included':False}))
