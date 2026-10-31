"""Disposable loopback fixture for Android emulator integration, no user data."""
import json
from pathlib import Path
import signal
import ssl
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'host'))
from nodelift.host import Server,make_identity
from nodelift.state import State

with tempfile.TemporaryDirectory(prefix='nodelift-android-qa-') as folder:
    state=State(Path(folder));cert,key,pem,sha=make_identity(state.folder,'10.0.2.2')
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(cert,key)
    server=Server(('127.0.0.1',0),state,context=ctx)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    invite,expiry=state.invite()
    path=ROOT/'apps/android/app/src/androidTest/assets/pairing.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({'protocol':1,'url':f'https://10.0.2.2:{server.server_port}','certificate':pem,'sha256':sha,'invite':invite,'expires_at':expiry}))
    path.chmod(0o600)
    stop=threading.Event()
    signal.signal(signal.SIGTERM,lambda *_:stop.set());signal.signal(signal.SIGINT,lambda *_:stop.set())
    print('Android QA fixture ready; ephemeral invitation written to ignored test asset.',flush=True)
    stop.wait(240)
    server.shutdown();server.server_close();path.unlink(missing_ok=True)
