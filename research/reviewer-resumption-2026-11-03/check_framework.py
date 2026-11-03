"""Reproduce the framework public-header issue with two minimal iOS builds."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cmake', default=str(Path.home() / 'Library/Android/sdk/cmake/3.22.1/bin/cmake'))
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
results = []
with tempfile.TemporaryDirectory(prefix='nodelift-framework-header-') as folder:
    root = Path(folder)
    for with_source in (False, True):
        src = root / ('with-source' if with_source else 'property-only')
        src.mkdir()
        (src / 'core.c').write_text('int nl_fixture(void){ return 1; }\n')
        (src / 'core.h').write_text('int nl_fixture(void);\n')
        (src / 'CMakeLists.txt').write_text(
            'cmake_minimum_required(VERSION 3.22)\nproject(header_fixture LANGUAGES C)\n'
            'add_library(header_fixture SHARED core.c' + (' core.h' if with_source else '') + ')\n'
            'set_target_properties(header_fixture PROPERTIES FRAMEWORK TRUE PUBLIC_HEADER core.h)\n')
        build = src / 'build'
        configured = subprocess.run([args.cmake, '-S', str(src), '-B', str(build),
            '-DCMAKE_SYSTEM_NAME=iOS', '-DCMAKE_OSX_SYSROOT=iphoneos',
            '-DCMAKE_OSX_ARCHITECTURES=arm64', '-DCMAKE_OSX_DEPLOYMENT_TARGET=17.0'],
            capture_output=True, text=True, timeout=120)
        item = {'header_in_target_sources': with_source, 'configure_exit': configured.returncode}
        if configured.returncode == 0:
            built = subprocess.run([args.cmake, '--build', str(build)], capture_output=True, text=True, timeout=120)
            header = build / 'header_fixture.framework/Headers/core.h'
            item.update(build_exit=built.returncode, header_present=header.exists(),
                        header_matches_source=header.exists() and header.read_bytes() == (src / 'core.h').read_bytes())
        results.append(item)
record = {'scope': 'Minimal real iOS arm64 framework fixture; not a NodeLift iOS app build',
          'cmake_version': subprocess.check_output([args.cmake, '--version'], text=True).splitlines()[0],
          'results': results}
args.output.write_text(json.dumps(record, indent=2) + '\n')
assert all(x['configure_exit'] == x.get('build_exit') == 0 for x in results), record
assert not results[0]['header_present'] and results[1]['header_matches_source'], record
print('Reproduced missing header, then verified header packaging with target source.')
