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

    def __init__(self, address, state, context=None, admin_token=None, ticket_factory=None, engine=None, client_token=None, pairing_network=None):
        self.state = state
        self.context = context
        self.admin_token = admin_token
        self.ticket_factory = ticket_factory
        self.pairing_network = pairing_network
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
                return self.send(200, {"service": "NodeLift", "protocol": 1, "pairing_scope": self.server.state.pairing_scope()})
            if method == "POST" and path == "/v1/pair":
                v = self.body()
                return self.send(200, self.server.state.pair(v.get("invite"), v.get("name"), v.get("capabilities", {}), v.get("device_key"), v.get("previous")))
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
        if path == "/admin/session/restore":
            # Bootstrap only from the first-party loopback page. No CORS.
            if (method != "POST" or self.client_address[0] != "127.0.0.1"
                    or self.headers.get("Origin") != "http://" + expected
                    or self.headers.get("Sec-Fetch-Site") != "same-origin"
                    or self.headers.get("X-NodeLift-Session") != "restore"
                    or self.headers.get("Content-Type") != "application/json"):
                raise PermissionError("local dashboard recovery required")
            if self.body() != {}:
                raise ValueError("empty recovery request required")
            return self.send(200, {"token": self.server.admin_token})
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
            value = self.body().get("invite")
            changed = bool(self.server.pairing_network and not self.server.pairing_network())
            result = self.server.state.invitation(value, revoke=changed or path.endswith("/revoke"))
            if changed:
                result["network_changed"] = True
            return self.send(200, result)
        if method == "POST" and path == "/admin/job":
            v = self.body()
            return self.send(200, self.server.state.queue(v.get("node_id"), v.get("kind")))
        if method == "POST" and path == "/admin/revoke":
            self.server.state.revoke(self.body().get("node_id"))
            return self.send(200, {"revoked": True})
        return self.send(404, {"error": "unknown endpoint"})



def pairing_address_allowed(address):
    try:
        value = ipaddress.IPv4Address(address)
        return any(value in ipaddress.IPv4Network(cidr) for cidr in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8"))
    except ValueError:
        return False


def local_address_available(address):
    """Check interface ownership without sending traffic or accepting a wildcard bind."""
    try:
        value = ipaddress.IPv4Address(address)
        if not pairing_address_allowed(address):
            return False
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.bind((str(value), 0))
        return True
    except (OSError, ValueError):
        return False


def route_address():
    """Ask the OS which local IPv4 it would route from; UDP connect sends no packet."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.0.2.1", 9))
            address = probe.getsockname()[0]
    except OSError:
        raise ValueError("Connect the computer to Wi-Fi or Ethernet, then create a new QR code.") from None
    if not local_address_available(address) or ipaddress.ip_address(address).is_loopback:
        raise ValueError("Connect the computer to Wi-Fi or Ethernet, then create a new QR code.")
    return address


class PairingEndpoint:
    """Bind only the selected LAN interface. Preserve enrollment/history across DHCP changes.

    A new address gets a separate pinned TLS identity. Existing companions must scan
    a fresh invitation; never weaken hostname or certificate checks to hide a move.
    """
    def __init__(self, state, address="auto", port=9867, engine=None):
        self.state, self.requested, self.port, self.engine = state, address, port, engine
        self.api = None
        self.address = None
        self.identity = None
        self.lock = threading.RLock()

    def desired_address(self):
        address = route_address() if self.requested == "auto" else self.requested
        if not local_address_available(address):
            raise ValueError("The computer's network address changed. Restart NodeLift with --address auto and create a new QR code.")
        return address

    def network_ready(self):
        try:
            return self.api is not None and self.address == self.desired_address()
        except ValueError:
            return False

    def ensure(self):
        with self.lock:
            address = self.desired_address()
            if self.api is not None and self.address == address:
                return
            # Reuse the legacy pin only at the address for which it was issued.
            folder = self.state.folder
            metadata = folder / "identity.json"
            if metadata.exists() and json.loads(metadata.read_text()).get("address") != address:
                folder = folder / "identities" / address
                folder.mkdir(parents=True, exist_ok=True, mode=0o700)
            cert, key, pem, fingerprint = make_identity(folder, address)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(cert, key)
            try:
                candidate = Server((address, self.port), self.state, context=context, engine=self.engine)
            except OSError:
                raise ValueError("The local connection could not start. Check the computer's network and whether another NodeLift host is running.") from None
            threading.Thread(target=candidate.serve_forever, daemon=True).start()
            previous = self.api
            self.api, self.address = candidate, address
            self.identity = (pem, fingerprint, public_key_pin(cert))
            if previous:
                previous.shutdown()
                previous.server_close()
                # Old QR codes cannot establish a connection at their embedded address.
                with self.state.db() as db:
                    db.execute("DELETE FROM invites")

    def ticket(self):
        with self.lock:
            self.ensure()  # A failed bind never produces an invitation.
            invite, expires = self.state.invite()
            pem, fingerprint, pin = self.identity
            return {"protocol": 1, "url": f"https://{self.address}:{self.api.server_port}",
                    "certificate": pem, "sha256": fingerprint, "public_key_pin": pin,
                    "invite": invite, "expires_at": expires}

    def close(self):
        with self.lock:
            if self.api:
                self.api.shutdown()
                self.api.server_close()
                self.api = None


def main():
    parser = argparse.ArgumentParser(description="NodeLift local host and experimental greedy inference engine.")
    parser.add_argument("--address", default="auto", help="auto follows the current private IPv4 route when creating a QR; an explicit address stays fixed")
    parser.add_argument("--port", type=int, default=9867)
    parser.add_argument("--dashboard-port", type=int, default=9868)
    parser.add_argument("--state", type=Path, default=Path.home()/".local/share/nodelift")
    parser.add_argument("--bonjour", action="store_true", help="Advertise the host on the local network via dns-sd")
    args = parser.parse_args()
    if args.address != "auto":
        try:
            address = ipaddress.IPv4Address(args.address)
            if not pairing_address_allowed(args.address):
                raise ValueError()
        except ValueError:
            parser.error("use auto or the private LAN IPv4 address of this computer")
    state = State(args.state)
    from .engine import Controller
    engine = Controller(state)
    endpoint = PairingEndpoint(state, args.address, args.port, engine)
    try:
        endpoint.ensure()
    except ValueError as error:
        print(str(error), flush=True)  # Dashboard stays available to retry Add device.
    admin_token = secrets.token_urlsafe(32)
    client_file = state.folder/'client-api-key'
    if client_file.exists():client_token=client_file.read_text().strip()
    else:
        client_token=secrets.token_urlsafe(32)
        with open(client_file,'w',opener=lambda p,f:os.open(p,f,0o600)) as stream:stream.write(client_token)
    admin = Server(("127.0.0.1", args.dashboard_port), state, admin_token=admin_token, ticket_factory=endpoint.ticket, engine=engine,client_token=client_token, pairing_network=endpoint.network_ready)
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (admin,)]
    for t in threads:
        t.start()
    discovery = None
    if args.bonjour:
        try:
            discovery = subprocess.Popen(["dns-sd", "-R", "NodeLift", "_nodelift._tcp", "local", str(args.port), "protocol=1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            print("Bonjour unavailable; pairing ticket still works.")
    print(f"NodeLift 0.3.0: experimental native inference; mobile speedup unqualified.\nDashboard (local, private link): http://127.0.0.1:{admin.server_port}/#{admin_token}", flush=True)
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    stop.wait()
    engine.stop()
    endpoint.close()
    for s in (admin,):
        s.shutdown()
        s.server_close()
    if discovery:
        discovery.terminate()


if __name__ == "__main__":
    main()
