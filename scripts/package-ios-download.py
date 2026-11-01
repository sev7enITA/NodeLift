#!/usr/bin/env python3
"""Wrap a manifest-verified unsigned device app in Payload/, without rebuilding/signing."""
import argparse
import hashlib
import json
import plistlib
import stat
import zipfile
from pathlib import Path, PurePosixPath


def package(source, manifest_path, output):
    manifest = json.loads(manifest_path.read_text())
    raw = source.read_bytes()
    expected = manifest['assets'][source.name]
    if len(raw) != expected['bytes'] or hashlib.sha256(raw).hexdigest() != expected['sha256']:
        raise ValueError('Input differs from the published build manifest')
    if output.exists():
        raise ValueError('Output already exists; refusing to replace a release artifact')
    with zipfile.ZipFile(source) as archive:
        members = [m for m in archive.infolist() if m.filename.startswith('NodeLift.app/')]
        names = [m.filename for m in members]
        if len(names) != len(set(names)) or not members:
            raise ValueError('Missing or duplicate app members')
        for member in members:
            if '..' in PurePosixPath(member.filename).parts or stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError('Unexpected archive path or symlink')
            if member.filename.endswith('embedded.mobileprovision') or '/_CodeSignature/' in member.filename:
                raise ValueError('Only unsigned apps without provisioning profiles are supported')
        info = plistlib.loads(archive.read('NodeLift.app/Info.plist'))
        if (info['DTPlatformName'] != 'iphoneos' or
                info['CFBundleIdentifier'] != 'dev.nodelift.companion' or
                info['CFBundleShortVersionString'] != manifest['version']):
            raise ValueError('Unexpected app identity, version or platform')
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as result:
            for member in members:
                data = archive.read(member.filename)
                target = zipfile.ZipInfo('Payload/' + member.filename, member.date_time)
                target.create_system = member.create_system
                target.external_attr = member.external_attr
                target.compress_type = zipfile.ZIP_DEFLATED
                result.writestr(target, data)
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(output) as packaged:
        assert packaged.testzip() is None
        assert all(original.read(name) == packaged.read('Payload/' + name) for name in names)
    return {'name': output.name, 'bytes': output.stat().st_size,
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'source_archive': source.name, 'source_sha256': expected['sha256'],
            'source_commit': manifest['source_commit'], 'version': manifest['version'],
            'minimum_os': info['MinimumOSVersion'], 'platform': 'iphoneos',
            'signing': 'unsigned; personal signing and provisioning required',
            'app_payload_byte_identical': True, 'device_installation_tested': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.source, args.manifest, args.output), indent=2))
