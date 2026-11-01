#!/usr/bin/env python3
"""Validate authored local documentation/image links and current release entry points."""
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = 'https://github.com/sev7enITA/NodeLift/'


def check():
    errors = []
    pages = list(ROOT.glob('*.md')) + list((ROOT/'docs').rglob('*.md'))
    checked = 0
    for page in pages:
        source = re.sub(r'^```.*?^```[^\n]*', '', page.read_text(), flags=re.M | re.S)
        targets = re.findall(r'!?\[[^\]\n]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)', source)
        targets += re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', source)
        for raw in targets:
            raw = raw.strip('<>')
            if raw.startswith(PUBLIC+'blob/main/') or raw.startswith(PUBLIC+'tree/main/'):
                local = ROOT / unquote(urlsplit(raw).path.split('/main/', 1)[1])
            elif raw.startswith(PUBLIC+'wiki/'):
                title = unquote(urlsplit(raw).path.rsplit('/', 1)[1])
                local = ROOT/'docs/wiki'/f'{title}.md'
            elif urlsplit(raw).scheme or raw.startswith(('#', '//')):
                continue
            else:
                local = page.parent / unquote(urlsplit(raw).path)
            checked += 1
            if not local.exists():
                errors.append(f'{page.relative_to(ROOT)}: missing target {raw}')
    readme = (ROOT/'README.md').read_text()
    version = re.search(r'versionName = "([^"]+)"', (ROOT/'apps/android/app/build.gradle.kts').read_text()).group(1)
    if f'releases/tag/v{version}' not in readme:
        errors.append('README does not link to the current companion release')
    if f'releases/download/v{version}/NodeLift-{version}-android-debug.apk' not in readme:
        errors.append('README does not link to the current Android asset')
    for name in ('Home', 'Quickstart', 'Android', 'iOS-and-iPadOS', 'Models-and-providers', 'Benchmarking', 'Troubleshooting', 'Development-and-workflows', 'Architecture', 'About-and-credits', '_Sidebar', '_Footer'):
        if not (ROOT/'docs/wiki'/f'{name}.md').exists():
            errors.append('Missing Wiki source: '+name)
    return {'pages': len(pages), 'local_targets_checked': checked, 'companion_version': version, 'errors': errors}


if __name__ == '__main__':
    report = check()
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report['errors']))
