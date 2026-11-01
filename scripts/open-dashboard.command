#!/bin/zsh
set -eu
python3 - <<'PY'
from pathlib import Path
import re
import urllib.request
import webbrowser

log = Path.home()/'.local/share/nodelift/host-session.log'
try:
    matches = re.findall(r'http://127\.0\.0\.1:(\d{1,5})/#([A-Za-z0-9_-]{32,})', log.read_text())
    if not matches:
        raise ValueError('Dashboard session link not found.')
    port, token = matches[-1]
    origin = 'http://127.0.0.1:' + port
    request = urllib.request.Request(origin + '/admin/status', headers={'Authorization': 'Bearer ' + token})
    with urllib.request.urlopen(request, timeout=5) as response:
        if response.status != 200:
            raise ValueError('Dashboard session is unavailable.')
    webbrowser.open(origin + '/#' + token)
    print('NodeLift dashboard opened in the browser.')
except (OSError, ValueError):
    print('NodeLift is not running or the session link has expired. Start the server and open the Dashboard link printed in the terminal. Each browser tab needs its own session link.')
    raise SystemExit(1)
PY
