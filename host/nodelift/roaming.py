"""Stable TLS identity and optional native DNS-SD advertisement. No credentials in discovery."""
from pathlib import Path
import hashlib
import json
import secrets
import shutil
import ssl
import subprocess


def identity(folder):
    folder = folder / "roaming-identity"
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    cert, key, metadata = folder/"host.pem", folder/"host.key", folder/"identity.json"
    if metadata.exists():
        name = json.loads(metadata.read_text())["tls_name"]
    else:
        if cert.exists() or key.exists():
            raise ValueError("Incomplete roaming identity; restore its backup before continuing.")
        name = "nodelift-" + secrets.token_hex(16) + ".local"
        metadata.write_text(json.dumps({"tls_name": name}))
    import re
    if not re.fullmatch(r"nodelift-[0-9a-f]{32}\.local", name):
        raise ValueError("Invalid roaming identity")
    if not cert.exists() or not key.exists():
        if cert.exists() or key.exists():
            raise ValueError("Incomplete roaming identity; restore its backup before continuing.")
        config = folder/"openssl.cnf"
        config.write_text("[req]\ndistinguished_name=dn\nx509_extensions=ext\nprompt=no\n[dn]\nCN="+name+"\n[ext]\nsubjectAltName=DNS:"+name+"\nbasicConstraints=critical,CA:TRUE\nkeyUsage=critical,digitalSignature,keyEncipherment,keyCertSign\nextendedKeyUsage=serverAuth\n")
        subprocess.run(["openssl","req","-x509","-newkey","rsa:2048","-nodes","-days","365","-config",str(config),"-keyout",str(key),"-out",str(cert)],check=True,capture_output=True,timeout=20)
        key.chmod(0o600);cert.chmod(0o600)
    # Never silently rotate an expired pinned identity.
    subprocess.run(["openssl","x509","-in",str(cert),"-checkend","0","-noout"],check=True,capture_output=True,timeout=5)
    pem=cert.read_text();fingerprint=hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem)).hexdigest()
    return cert,key,pem,fingerprint,name


class Publisher:
    def __init__(self):
        self.process=None;self.record=None
        self.command=shutil.which("dns-sd") or shutil.which("avahi-publish-service")
    def update(self,address,port,fingerprint,tls_name):
        record=(address,port,fingerprint,tls_name)
        if self.record==record and self.process and self.process.poll() is None:return
        self.close();self.record=record
        if not self.command:return
        name="NodeLift-"+fingerprint[:12]
        txt=["protocol=2","id="+fingerprint,"address="+address,"port="+str(port)]
        command=([self.command,"-R",name,"_nodelift._tcp","local",str(port)] if Path(self.command).stem == "dns-sd" else [self.command,name,"_nodelift._tcp",str(port)])
        try:self.process=subprocess.Popen(command+txt,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except OSError:self.process=None
    def close(self):
        if self.process:
            self.process.terminate()
            try:self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=2)
        self.process=None;self.record=None
    @property
    def available(self):return bool(self.process and self.process.poll() is None)
