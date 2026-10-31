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
        raise ValueError('Collegamento di sessione non trovato.')
    port, token = matches[-1]
    origin = 'http://127.0.0.1:' + port
    request = urllib.request.Request(origin + '/admin/status', headers={'Authorization': 'Bearer ' + token})
    with urllib.request.urlopen(request, timeout=5) as response:
        if response.status != 200:
            raise ValueError('Sessione non disponibile.')
    webbrowser.open(origin + '/#' + token)
    print('Dashboard NodeLift aperta nel browser.')
except (OSError, ValueError):
    print('NodeLift non è attivo oppure il collegamento è scaduto. Avvia il server e apri il collegamento Dashboard stampato nel terminale.')
    raise SystemExit(1)
PY
