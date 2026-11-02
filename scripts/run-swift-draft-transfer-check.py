#!/usr/bin/env python3
"""Exercise the actual iOS transfer source on macOS against a synthetic pinned TLS server."""
import argparse, hashlib, json, ssl, subprocess, sys, tempfile, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'host'))
from nodelift.host import make_identity

parser = argparse.ArgumentParser()
parser.add_argument('--binary', type=Path, required=True)
args = parser.parse_args()
payload = b'GGUF' + b'synthetic-only' * 32768
modes = iter(['valid', 'hash-mismatch', 'wrong-length', 'truncated', 'redirect', 'unauthorized', 'cancelled'])
class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *args): pass
    def handle(self):
        try: super().handle()
        except (BrokenPipeError, ConnectionResetError, ssl.SSLError): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        data = json.dumps({'error': body['error']}).encode()
        self.send_response(body['status']); self.send_header('Content-Length', str(len(data)))
        self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.headers.get('Authorization') != 'Bearer synthetic-draft-test':
            self.send_error(401); return
        if self.path == '/v1/engine/model-info':
            self.server.mode = next(modes)
            digest = hashlib.sha256(payload).hexdigest() if self.server.mode != 'hash-mismatch' else '0'*64
            data = json.dumps({'bytes':len(payload), 'sha256':digest}).encode()
            self.send_response(200); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
        if self.path != '/v1/engine/model': self.send_error(404); return
        mode = self.server.mode
        if mode == 'unauthorized': self.send_error(401); return
        if mode == 'redirect':
            self.send_response(302); self.send_header('Location','/unexpected'); self.send_header('Content-Length','0'); self.end_headers(); return
        self.send_response(200)
        self.send_header('Content-Length',str(len(payload)+(1 if mode == 'wrong-length' else 0)))
        self.end_headers()
        try:
            if mode == 'truncated':
                self.wfile.write(payload[:100]); self.close_connection = True
            elif mode == 'cancelled':
                for i in range(0,len(payload),1024):
                    self.wfile.write(payload[i:i+1024]); self.wfile.flush(); time.sleep(.02)
            else: self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError, ssl.SSLError): pass
with tempfile.TemporaryDirectory(prefix='nodelift-draft-qa-') as folder:
    cert,key,pem,sha = make_identity(Path(folder),'127.0.0.1')
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); context.load_cert_chain(cert,key)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    server.socket=context.wrap_socket(server.socket,server_side=True)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    ticket=Path(folder)/'ticket.json'
    ticket.write_text(json.dumps({'protocol':1,'url':f'https://127.0.0.1:{server.server_port}','certificate':pem,'sha256':sha}))
    wrong_folder = Path(folder)/'wrong'; wrong_folder.mkdir()
    _,_,wrong_pem,wrong_sha = make_identity(wrong_folder,'127.0.0.1')
    wrong = Path(folder)/'wrong.json'
    wrong.write_text(json.dumps({'protocol':1,'url':f'https://127.0.0.1:{server.server_port}','certificate':wrong_pem,'sha256':wrong_sha}))
    try: subprocess.run([str(args.binary),str(ticket),str(wrong)],check=True,timeout=60)
    finally: server.shutdown(); server.server_close()
