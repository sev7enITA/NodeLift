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

    def __init__(self, address, state, context=None, admin_token=None, ticket_factory=None):
        self.state = state
        self.context = context
        self.admin_token = admin_token
        self.ticket_factory = ticket_factory
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
    server_version = "NodeLift/0.1"

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
        except (ValueError, KeyError, TypeError, OverflowError) as error:
            self.close_connection = True
            self.send(400, {"error": str(error)[:200]})
        except (OSError, TimeoutError):
            self.close_connection = True

    def admin(self, method, path):
        host = self.headers.get("Host", "")
        expected = "127.0.0.1:" + str(self.server.server_port)
        if host != expected or self.headers.get("Origin", "http://" + expected) != "http://" + expected:
            raise PermissionError("loopback origin required")
        assets = {"/": ("dashboard.html", "text/html; charset=utf-8"), "/app.js": ("dashboard.js", "text/javascript"), "/style.css": ("dashboard.css", "text/css")}
        if method == "GET" and path in assets:
            name, kind = assets[path]
            return self.send(200, Path(__file__).with_name(name).read_bytes(), kind)
        if not secrets.compare_digest(self.bearer(), self.server.admin_token):
            raise PermissionError("open the dashboard link printed by NodeLift")
        if method == "GET" and path == "/admin/status":
            return self.send(200, self.server.state.snapshot())
        if method == "POST" and path == "/admin/invite":
            self.body()
            return self.send(200, self.server.ticket_factory())
        if method == "POST" and path == "/admin/job":
            v = self.body()
            return self.send(200, self.server.state.queue(v.get("node_id"), v.get("kind")))
        if method == "POST" and path == "/admin/revoke":
            self.server.state.revoke(self.body().get("node_id"))
            return self.send(200, {"revoked": True})
        return self.send(404, {"error": "unknown endpoint"})


def main():
    parser = argparse.ArgumentParser(description="NodeLift qualification host. No LLM inference yet.")
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
        return {"protocol": 1, "url": f"https://{args.address}:{args.port}", "certificate": pem,
                "sha256": fingerprint, "public_key_pin": pin, "invite": invite, "expires_at": expires}
    api = Server((args.address, args.port), state, context=ctx)
    admin_token = secrets.token_urlsafe(32)
    admin = Server(("127.0.0.1", args.dashboard_port), state, admin_token=admin_token, ticket_factory=ticket)
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (api, admin)]
    for t in threads:
        t.start()
    discovery = None
    if args.bonjour:
        try:
            discovery = subprocess.Popen(["dns-sd", "-R", "NodeLift", "_nodelift._tcp", "local", str(args.port), "protocol=1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            print("Bonjour unavailable; pairing ticket still works.")
    print(f"NodeLift 0.1 — companion qualification; LLM engine not enabled.\nDashboard (local, private link): http://127.0.0.1:{args.dashboard_port}/#{admin_token}", flush=True)
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    stop.wait()
    for s in (api, admin):
        s.shutdown()
        s.server_close()
    if discovery:
        discovery.terminate()


if __name__ == "__main__":
    main()
