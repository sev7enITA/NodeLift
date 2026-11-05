"""Exercise the actual Swift client against two real TLS endpoints with one stable identity."""
from pathlib import Path
import argparse,json,tempfile,threading,ssl,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'host'))
from nodelift.roaming import identity,Publisher
from nodelift.host import Server,route_address
from nodelift.state import State
p=argparse.ArgumentParser();p.add_argument('--binary',required=True);p.add_argument('--discovery',action='store_true');args=p.parse_args()
with tempfile.TemporaryDirectory() as folder:
    state=State(Path(folder));cert,key,pem,fingerprint,name=identity(state.folder)
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key)
    address=route_address() if args.discovery else '127.0.0.1'
    servers=[Server((address,0),state,context=context) for _ in range(2)]
    for server in servers:
        server.host_identity=fingerprint
        threading.Thread(target=server.serve_forever,daemon=True).start()
    code,expiry=state.invite()
    ticket={'protocol':2,'url':f'https://{address}:{servers[0].server_port}','certificate':pem,'sha256':fingerprint,'tls_name':name,'invite':code,'expires_at':expiry}
    moved=dict(ticket,url=f'https://{address}:{servers[1].server_port}')
    _,_,wrongpem,wrongsha,wrongname=identity(state.folder/'other')
    wrong=dict(ticket,certificate=wrongpem,sha256=wrongsha,tls_name=wrongname)
    data=Path(folder)/'tickets.json';data.write_text(json.dumps([ticket,moved,wrong]));data.chmod(0o600)
    publisher=Publisher()
    try:
        if args.discovery:publisher.update(address,servers[0].server_port,fingerprint,name)
        result=subprocess.run([args.binary,str(data)]+(['--discovery'] if args.discovery else []),capture_output=True,text=True,timeout=50)
        print(result.stdout);print(result.stderr,file=sys.stderr)
        if result.returncode:raise SystemExit(result.returncode)
        assert len(state.snapshot()['nodes'])==1
    finally:
        publisher.close()
        for server in servers:server.shutdown();server.server_close()
