"""NodeLift host: standard-library HTTPS companion protocol and loopback dashboard."""
import argparse
import base64
import hashlib
import http.server
import ipaddress
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import ssl
import subprocess
import threading
from urllib.parse import parse_qs, urlsplit

from .state import State
from .telemetry import host_inventory
from . import __version__

MAX_BODY = 1024 * 1024
PAYLOAD = os.urandom(MAX_BODY)


def make_identity(folder, address):
    # Only IP addresses are accepted: no interpolation into openssl configuration.
    ipaddress.ip_address(address)
    cert, key, meta = folder / "host.pem", folder / "host.key", folder / "identity.json"
    if meta.exists() and json.loads(meta.read_text())["address"] != address:
        raise ValueError("host IP changed; use a new --state directory and re-pair devices")
    if not cert.exists() or not key.exists():
        config = folder / "openssl.cnf"
        config.write_text("[req]\ndistinguished_name=dn\nx509_extensions=ext\nprompt=no\n[dn]\nCN=NodeLift\n[ext]\nsubjectAltName=IP:" + address + ",IP:127.0.0.1\nbasicConstraints=critical,CA:TRUE\nkeyUsage=critical,digitalSignature,keyEncipherment,keyCertSign\nextendedKeyUsage=serverAuth\n")
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "30", "-config", str(config), "-keyout", str(key), "-out", str(cert)], check=True, capture_output=True)
        key.chmod(0o600)
        cert.chmod(0o600)
        meta.write_text(json.dumps({"address": address}))
    pem = cert.read_text()
    der = ssl.PEM_cert_to_DER_cert(pem)
    return cert, key, pem, hashlib.sha256(der).hexdigest()


def public_key_pin(cert):
    public = subprocess.run(["openssl", "x509", "-in", str(cert), "-pubkey", "-noout"], check=True, capture_output=True).stdout
    der = subprocess.run(["openssl", "pkey", "-pubin", "-outform", "DER"], input=public, check=True, capture_output=True).stdout
    return base64.b64encode(hashlib.sha256(der).digest()).decode()


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, state, context=None, admin_token=None, ticket_factory=None, engine=None, client_token=None):
        self.state = state
        self.context = context
        self.admin_token = admin_token
        self.ticket_factory = ticket_factory
        self.engine = engine
        self.client_token = client_token
        self.slots = threading.BoundedSemaphore(32)
        super().__init__(address, Handler)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            request.settimeout(10)
            request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            if self.context:
                request = self.context.wrap_socket(request, server_side=True)
            super().process_request_thread(request, address)
        except (OSError, ssl.SSLError):
            request.close()
        finally:
            self.slots.release()

    def handle_error(self, request, address):
        # Broken connections are expected when a companion is paused.
        pass


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "NodeLift/0.3.0"

    def setup(self):
        super().setup()
        self.connection_id = secrets.token_hex(8)

    def log_message(self, *_):
        pass  # Never put invitations, bearer tokens or query strings in logs.

    def send(self, status, payload, content_type="application/json"):
        if not isinstance(payload, bytes):
            payload = json.dumps(payload, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-NodeLift-Connection-ID", self.connection_id)
        if content_type.startswith("text/html"):
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def body(self, raw=False):
        if self.headers.get("Transfer-Encoding"):
            raise ValueError("chunked requests unsupported")
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not lengths[0].isdigit():
            raise ValueError("one Content-Length required")
        length = int(lengths[0])
        if length > MAX_BODY:
            raise ValueError("body too large")
        data = self.rfile.read(length)
        if len(data) != length:
            raise ValueError("incomplete body")
        if raw:
            return data
        value = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value

    def bearer(self):
        auth = self.headers.get("Authorization", "")
        return auth[7:] if auth.startswith("Bearer ") else ""

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def dispatch(self, method):
        try:
            route = urlsplit(self.path)
            path = route.path
            if self.server.admin_token is not None:
                return self.admin(method, path)
            if method == "GET" and path == "/health":
                return self.send(200, {"service": "NodeLift", "protocol": 1})
            if method == "POST" and path == "/v1/pair":
                v = self.body()
                return self.send(200, self.server.state.pair(v.get("invite"), v.get("name"), v.get("capabilities", {})))
            node = self.server.state.authenticate(self.bearer())
            if self.server.engine:
                if method == "GET" and path == "/v1/engine/poll":
                    return self.send(200, self.server.engine.mailbox.poll(node))
                if method == "POST" and path == "/v1/engine/result":
                    return self.send(200, self.server.engine.mailbox.submit(node, self.body()))
                if method == "GET" and path == "/v1/engine/model-info":
                    return self.send(200, self.server.engine.model_offer())
                if method == "GET" and path == "/v1/engine/model":
                    model = self.server.engine.model_path()
                    with model.open('rb') as stream:
                        self.send_response(200)
                        self.send_header('Content-Type','application/octet-stream')
                        self.send_header('Content-Length',str(model.stat().st_size))
                        self.send_header('Cache-Control','no-store')
                        self.end_headers()
                        while block := stream.read(262144):self.wfile.write(block)
                    return
            if method == "GET" and path == "/v1/probe":
                size = int(parse_qs(route.query).get("size", ["64"])[0])
                if not 1 <= size <= MAX_BODY:
                    raise ValueError("probe size outside limits")
                return self.send(200, PAYLOAD[:size], "application/octet-stream")
            if method == "POST" and path == "/v1/upload":
                data = self.body(raw=True)
                return self.send(200, {"bytes": len(data)})
            if method == "POST" and path == "/v1/heartbeat":
                return self.send(200, self.server.state.heartbeat(node, self.body()))
            if method == "POST" and path == "/v1/result":
                return self.send(200, self.server.state.finish(node, self.body()))
            self.send(404, {"error": "unknown endpoint"})
        except PermissionError as error:
            self.close_connection = True
            self.send(401, {"error": str(error)})
        except (ValueError, KeyError, TypeError, OverflowError, RuntimeError) as error:
            self.close_connection = True
            self.send(400, {"error": str(error)[:200]})
        except (OSError, TimeoutError):
            self.close_connection = True

    def admin(self, method, path):
        host = self.headers.get("Host", "")
        expected = "127.0.0.1:" + str(self.server.server_port)
        if host != expected or self.headers.get("Origin", "http://" + expected) != "http://" + expected:
            raise PermissionError("loopback origin required")
        assets = {"/qr.js": ("vendor/qrcodegen.js", "text/javascript"), "/pairing.js": ("pairing.js", "text/javascript"), "/": ("dashboard.html", "text/html; charset=utf-8"), "/app.js": ("dashboard.js", "text/javascript"), "/graph.js": ("graph.js", "text/javascript"), "/models.js": ("models.js", "text/javascript"), "/i18n.js": ("i18n.js", "text/javascript"), "/style.css": ("dashboard.css", "text/css")}
        if method == "GET" and path in assets:
            name, kind = assets[path]
            return self.send(200, (Path(__file__).parent / name).read_bytes(), kind)
        if method == "GET" and path.startswith('/brand/'):
            name = path.removeprefix('/brand/')
            folder = Path(__file__).resolve().parents[2]/'assets/brand'
            if name in ('nodelift-emblem.png','nodelift-mark.svg','nodelift-lockup.png') and (folder/name).is_file():
                return self.send(200,(folder/name).read_bytes(),'image/svg+xml' if name.endswith('.svg') else 'image/png')
            return self.send(404,{'error':'brand asset unavailable'})
        if path in ('/v1/models','/v1/chat/completions') and self.server.engine:
            if not self.server.client_token or not secrets.compare_digest(self.bearer(),self.server.client_token):raise PermissionError('client API key required')
            if method=='GET' and path=='/v1/models':return self.send(200,{'object':'list','data':[{'id':'nodelift','object':'model','owned_by':'local'}]})
            if method=='POST' and path=='/v1/chat/completions':
                from .gateway import chat
                return chat(self,self.server.engine,self.body())
            return self.send(405,{'error':'method not allowed'})
        if not secrets.compare_digest(self.bearer(), self.server.admin_token):
            raise PermissionError("open the dashboard link printed by NodeLift")
        if method == "GET" and path == "/admin/about":
            return self.send(200, {"version": __version__, "component": "host", "release_channel": "source-preview"})
        if self.server.engine:
            if method == 'GET' and path == '/admin/client-access':return self.send(200,{'base_url':'http://127.0.0.1:'+str(self.server.server_port)+'/v1','api_key':self.server.client_token,'model':'nodelift'})
            library = self.server.engine.library
            query = parse_qs(urlsplit(self.path).query)
            if method == 'POST' and path == '/admin/models/import':
                result = library.import_path(self.body().get('path'))
                self.server.engine.catalog_deadline = 0
                return self.send(200, result)
            if method == 'GET' and path == '/admin/models/search':return self.send(200,library.search(query.get('q',[''])[0]))
            if method == 'GET' and path == '/admin/models/inspect':return self.send(200,library.inspect(query.get('repo',[''])[0],query.get('revision',['main'])[0]))
            if method == 'POST' and path == '/admin/models/download':return self.send(200,library.download(self.body()))
            if method == 'POST' and path == '/admin/models/upload/start':return self.send(200,library.upload_start(self.body()))
            if method == 'POST' and path == '/admin/models/upload/chunk':return self.send(200,library.upload_chunk(query.get('id',[''])[0],int(query.get('offset',['-1'])[0]),self.body(raw=True)))
            if method == 'POST' and path == '/admin/models/upload/finish':return self.send(200,library.finish(self.body().get('id')))
            if method == 'POST' and path == '/admin/models/cancel':return self.send(200,library.cancel(self.body().get('id')))
            if method == 'POST' and path == '/admin/providers/configure':return self.send(200,self.server.engine.configure_provider(self.body()))
            if method == 'POST' and path == '/admin/providers/models':return self.send(200,self.server.engine.providers.models(self.body().get('backend')))
            if method == 'GET' and path == '/admin/engine/status':return self.send(200,self.server.engine.status())
            if method == 'POST' and path == '/admin/engine/configure':return self.send(200,self.server.engine.configure(self.body()))
            if method == 'POST' and path == '/admin/engine/run':return self.send(200,self.server.engine.start(self.body()))
            if method == 'POST' and path == '/admin/engine/stop':return self.send(200,self.server.engine.stop(self.body().get('run_id')))
        if method == "GET" and path == "/admin/status":
            return self.send(200, {**self.server.state.snapshot(), "host": host_inventory()})
        if method == "POST" and path == "/admin/invite":
            self.body()
            return self.send(200, self.server.ticket_factory())
        if method == "POST" and path in ("/admin/invite/status", "/admin/invite/revoke"):
            return self.send(200, self.server.state.invitation(self.body().get("invite"), revoke=path.endswith("/revoke")))
        if method == "POST" and path == "/admin/job":
            v = self.body()
            return self.send(200, self.server.state.queue(v.get("node_id"), v.get("kind")))
        if method == "POST" and path == "/admin/revoke":
            self.server.state.revoke(self.body().get("node_id"))
            return self.send(200, {"revoked": True})
        return self.send(404, {"error": "unknown endpoint"})


def main():
    parser = argparse.ArgumentParser(description="NodeLift local host and experimental greedy inference engine.")
    parser.add_argument("--address", default="127.0.0.1", help="Host LAN IPv4 address to put in the certificate and pairing ticket")
    parser.add_argument("--port", type=int, default=9867)
    parser.add_argument("--dashboard-port", type=int, default=9868)
    parser.add_argument("--state", type=Path, default=Path.home()/".local/share/nodelift")
    parser.add_argument("--bonjour", action="store_true", help="Advertise the host on the local network via dns-sd")
    args = parser.parse_args()
    address = ipaddress.IPv4Address(args.address)
    if not (address.is_private or address.is_loopback) or address.is_unspecified:
        parser.error("use the private LAN IPv4 address of this computer")
    state = State(args.state)
    cert, key, pem, fingerprint = make_identity(state.folder, args.address)
    pin = public_key_pin(cert)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(cert, key)
    def ticket():
        invite, expires = state.invite()
        return {"protocol": 1, "url": f"https://{args.address}:{api.server_port}", "certificate": pem,
                "sha256": fingerprint, "public_key_pin": pin, "invite": invite, "expires_at": expires}
    from .engine import Controller
    engine = Controller(state)
    api = Server((args.address, args.port), state, context=ctx, engine=engine)
    admin_token = secrets.token_urlsafe(32)
    client_file = state.folder/'client-api-key'
    if client_file.exists():client_token=client_file.read_text().strip()
    else:
        client_token=secrets.token_urlsafe(32)
        with open(client_file,'w',opener=lambda p,f:os.open(p,f,0o600)) as stream:stream.write(client_token)
    admin = Server(("127.0.0.1", args.dashboard_port), state, admin_token=admin_token, ticket_factory=ticket, engine=engine,client_token=client_token)
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (api, admin)]
    for t in threads:
        t.start()
    discovery = None
    if args.bonjour:
        try:
            discovery = subprocess.Popen(["dns-sd", "-R", "NodeLift", "_nodelift._tcp", "local", str(args.port), "protocol=1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            print("Bonjour unavailable; pairing ticket still works.")
    print(f"NodeLift 0.3.0 — experimental native inference; mobile speedup unqualified.\nDashboard (local, private link): http://127.0.0.1:{admin.server_port}/#{admin_token}", flush=True)
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    stop.wait()
    engine.stop()
    for s in (api, admin):
        s.shutdown()
        s.server_close()
    if discovery:
        discovery.terminate()


if __name__ == "__main__":
    main()
