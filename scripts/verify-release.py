#!/usr/bin/env python3
"""Verify public NodeLift release integrity without executing downloaded packages."""
import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path

API = 'https://api.github.com/repos/sev7enITA/NodeLift'
MAX_ASSET = 128 * 1024 * 1024


def read_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'NodeLift-release-verifier/1', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('Metadata exceeds the supported size')
    return json.loads(raw)


def read_asset(asset, tag, retain=False):
    name = asset['name']
    if not re.fullmatch(r'[A-Za-z0-9._-]+', name):
        raise ValueError('Invalid asset name')
    expected_url = f'https://github.com/sev7enITA/NodeLift/releases/download/{tag}/{name}'
    if asset['browser_download_url'] != expected_url:
        raise ValueError('Unexpected release download origin')
    size = asset['size']
    limit = 2 * 1024 * 1024 if retain else MAX_ASSET
    if not isinstance(size, int) or not 0 < size <= limit:
        raise ValueError('Asset size outside supported limits')
    digest = hashlib.sha256(); received = 0; kept = []
    request = urllib.request.Request(expected_url, headers={'User-Agent': 'NodeLift-release-verifier/1'})
    with urllib.request.urlopen(request, timeout=60) as response:
        while chunk := response.read(1024 * 1024):
            received += len(chunk)
            if received > size or received > limit:
                raise ValueError('Download exceeded declared size')
            digest.update(chunk)
            if retain:
                kept.append(chunk)
    result = digest.hexdigest()
    if received != size or asset.get('digest') != 'sha256:'+result:
        raise ValueError('GitHub asset digest or size mismatch: '+name)
    return {'name': name, 'bytes': received, 'sha256': result}, b''.join(kept)


def verify(tag):
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Use a release tag such as v0.2.3')
    release = read_json(API+'/releases/tags/'+tag)
    if release.get('draft') or release.get('tag_name') != tag:
        raise ValueError('Expected a published release with the selected tag')
    assets = {asset['name']: asset for asset in release['assets']}
    manifest_name = f'NodeLift-{tag[1:]}-build-manifest.json'
    manifest_receipt, raw = read_asset(assets[manifest_name], tag, retain=True)
    manifest = json.loads(raw)
    if manifest.get('version') != tag[1:]:
        raise ValueError('Manifest version differs from selected release')
    commit = manifest.get('source_commit', '')
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Missing immutable source commit')
    ref = read_json(API+'/git/ref/tags/'+tag)['object']
    if ref['type'] == 'tag':
        ref = read_json(API+'/git/tags/'+ref['sha'])['object']
    if ref['type'] != 'commit' or ref['sha'] != commit:
        raise ValueError('Manifest source differs from the release tag')
    receipts = [manifest_receipt]
    if not manifest.get('assets'):
        raise ValueError('Manifest has no package inventory')
    for name, expected in manifest['assets'].items():
        receipt, _ = read_asset(assets[name], tag)
        if receipt['bytes'] != expected['bytes'] or receipt['sha256'] != expected['sha256']:
            raise ValueError('Published package differs from manifest: '+name)
        receipts.append(receipt)
    return {'release': release['html_url'], 'source_commit': commit, 'integrity_verified': True,
            'scope': 'published bytes and tag identity; no execution, signing or device qualification', 'assets': receipts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = verify(args.tag)
    text = json.dumps(report, indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
