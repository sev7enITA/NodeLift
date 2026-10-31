"""Starts an isolated loopback host and checks the real Swift client implementation."""
import hashlib
import json
from pathlib import Path
import ssl
import subprocess
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'host'))
from nodelift.host import Server, make_identity
from nodelift.state import State

with tempfile.TemporaryDirectory(prefix='nodelift-swift-qa-') as folder:
    state=State(Path(folder))
    cert,key,pem,sha=make_identity(state.folder,'127.0.0.1')
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key)
    server=Server(('127.0.0.1',0),state,context=context)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    code,expiry=state.invite()
    ticket=Path(folder)/'ticket.json'
    ticket.write_text(json.dumps({'protocol':1,'url':f'https://127.0.0.1:{server.server_port}','certificate':pem,'sha256':sha,'invite':code,'expires_at':expiry}))
    ticket.chmod(0o600)
    wrong_state=State(Path(folder)/'wrong-host')
    _,_,wrong_pem,wrong_sha=make_identity(wrong_state.folder,'127.0.0.1')
    wrong_ticket=Path(folder)/'wrong-ticket.json'
    wrong_ticket.write_text(json.dumps({'protocol':1,'url':f'https://127.0.0.1:{server.server_port}','certificate':wrong_pem,'sha256':wrong_sha}))
    try:
        result=subprocess.run([str(ROOT/'artifacts/swift-protocol-check'),str(ticket),str(wrong_ticket)],timeout=45,capture_output=True,text=True)
        print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
        if result.returncode:raise SystemExit(result.returncode)
    finally:server.shutdown();server.server_close()
