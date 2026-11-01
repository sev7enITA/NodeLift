"""Starts an isolated loopback host and checks the real Swift client implementation."""
import argparse
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

parser=argparse.ArgumentParser();parser.add_argument('--binary',type=Path,default=ROOT/'artifacts/swift-protocol-check');args=parser.parse_args()

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
    next_code,next_expiry=state.invite()
    next_ticket=Path(folder)/'next-ticket.json'
    next_ticket.write_text(json.dumps({'protocol':1,'url':f'https://127.0.0.1:{server.server_port}','certificate':pem,'sha256':sha,'invite':next_code,'expires_at':next_expiry}))
    next_ticket.chmod(0o600)
    wrong_state=State(Path(folder)/'wrong-host')
    _,_,wrong_pem,wrong_sha=make_identity(wrong_state.folder,'127.0.0.1')
    wrong_ticket=Path(folder)/'wrong-ticket.json'
    wrong_ticket.write_text(json.dumps({'protocol':1,'url':f'https://127.0.0.1:{server.server_port}','certificate':wrong_pem,'sha256':wrong_sha}))
    try:
        result=subprocess.run([str(args.binary),str(ticket),str(wrong_ticket),str(next_ticket)],timeout=45,capture_output=True,text=True)
        print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
        if result.returncode:raise SystemExit(result.returncode)
        assert len(state.snapshot()['nodes'])==1, 'Swift re-pair created a duplicate node'
        print('PASS: real Swift TLS re-pair retained one host enrollment.')
    finally:server.shutdown();server.server_close()
