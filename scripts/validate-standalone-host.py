#!/usr/bin/env python3
"""Exercise a frozen host on loopback with an explicit local GGUF."""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host', type=Path, required=True)
parser.add_argument('--model', type=Path, required=True)
args = parser.parse_args()


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


env = dict(os.environ, PATH='/usr/bin:/bin:/usr/sbin:/sbin')
env.pop('PYTHONHOME', None)
env.pop('PYTHONPATH', None)
with tempfile.TemporaryDirectory(prefix='nodelift-host-validation-') as temp:
    dashboard, pairing = port(), port()
    log = Path(temp)/'private-session.log'
    with log.open('w+') as stream:
        process = subprocess.Popen([str(args.host.resolve()), '--address', '127.0.0.1',
                                    '--port', str(pairing), '--dashboard-port', str(dashboard),
                                    '--state', str(Path(temp)/'state')],
                                   stdout=stream, stderr=subprocess.DEVNULL, env=env)
        try:
            deadline, token = time.monotonic()+45, None
            while time.monotonic() < deadline:
                found = re.search(r'http://127\.0\.0\.1:\d+/#([A-Za-z0-9_-]+)', log.read_text())
                if found:
                    token = found.group(1)
                    break
                if process.poll() is not None:
                    raise RuntimeError('host exited before dashboard startup')
                time.sleep(.2)
            if not token:
                raise RuntimeError('dashboard startup deadline')
            base = 'http://127.0.0.1:'+str(dashboard)

            def call(path, body=None, admin=True):
                data = None if body is None else json.dumps(body).encode()
                headers = {'Authorization': 'Bearer '+token, 'Content-Type': 'application/json'} if admin else {}
                with urlopen(Request(base+path, data=data, headers=headers), timeout=90) as response:
                    return response.read()

            if b'NodeLift' not in call('/', admin=False) or b'<svg' not in call('/brand/nodelift-mark.svg', admin=False):
                raise RuntimeError('dashboard assets unavailable')
            network=json.loads(call('/admin/status'))['network']
            ticket=json.loads(call('/admin/invite', {}))
            if not network['companion_auto_reconnect'] or not network['discovery_available'] or ticket['protocol'] != 2 or not ticket.get('tls_name'):
                raise RuntimeError('protocol-2 host discovery unavailable')
            if not json.loads(call('/admin/engine/status'))['available']:
                raise RuntimeError('native library unavailable')
            if json.loads(call('/admin/probe', {}))['schema'] != 'nodelift.node-probe.v1':
                raise RuntimeError('probe endpoint unavailable')
            model = str(args.model.resolve(strict=True))
            call('/admin/models/import', {'path': model})
            call('/admin/engine/configure', {'target_model': model, 'n_ctx': 256, 'threads': 4, 'gpu_layers': 0})
            identity = json.loads(call('/admin/engine/run', {'prompt': 'Hello.', 'mode': 'host', 'max_tokens': 8}))['run_id']
            deadline, run = time.monotonic()+120, None
            while time.monotonic() < deadline:
                run = next((v for v in json.loads(call('/admin/engine/status'))['runs'] if v['id'] == identity), None)
                if run and run['status'] in ('completed', 'failed', 'cancelled'):
                    break
                time.sleep(.2)
            if not run or run['status'] != 'completed':
                raise RuntimeError('native GGUF generation did not complete: '+str((run or {}).get('status', 'missing')))
            print(json.dumps({'dashboard_and_brand': 'passed', 'native_library': 'loaded', 'inventory': 'passed',
                              'native_gguf_generation': 'completed', 'output_tokens': len(run['tokens']),
                              'transport': 'loopback only', 'state': 'temporary', 'pairing_protocol': 2, 'discovery_publisher': 'running'}))
        finally:
            process.terminate()
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
