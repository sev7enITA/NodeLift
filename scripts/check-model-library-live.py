#!/usr/bin/env python3
"""Exercise real host HTTP import/upload/cancel/provider controls with an existing GGUF.

Uses temporary state and no user credentials. Public OpenRouter catalog is optional;
local provider catalog uses an explicitly synthetic HTTP fixture. Native inference
uses the supplied model and a fixed public prompt. This is not a speed benchmark.
"""
import argparse
import hashlib
import http.client
import http.server
import json
from pathlib import Path
import secrets
import tempfile
import threading
import time
from nodelift.host import Server
from nodelift.engine import Controller
from nodelift.state import State


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--inference-model',type=Path,help='Optional chat-capable GGUF for the inference check')
    parser.add_argument('--public-catalog',action='store_true')
    args=parser.parse_args();model=args.model.resolve(strict=True)
    report={'scope':'Real loopback HTTP and supplied-model inference; synthetic local provider catalog; no cloud generation','checks':{}}
    class ProviderFixture(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            body=json.dumps({'data':[{'id':'synthetic-audit-model','context_length':2048}]}).encode()
            self.send_response(200 if self.path=='/v1/models' else 404)
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    with tempfile.TemporaryDirectory(prefix='nodelift-model-api-audit-') as folder:
        state=State(Path(folder));engine=Controller(state);token=secrets.token_urlsafe(32)
        server=Server(('127.0.0.1',0),state,admin_token=token,engine=engine)
        provider=http.server.ThreadingHTTPServer(('127.0.0.1',0),ProviderFixture)
        for s in (server,provider):threading.Thread(target=s.serve_forever,daemon=True).start()
        def request(path,body=None,raw=False,expected=200):
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=40)
            headers={'Authorization':'Bearer '+token,'Content-Type':'application/octet-stream' if raw else 'application/json'}
            data=body if raw else json.dumps(body) if body is not None else None
            conn.request('GET' if body is None else 'POST','/admin/'+path,data,headers)
            r=conn.getresponse();value=json.loads(r.read());conn.close()
            assert r.status==expected,(path,r.status,value)
            return value
        def finish_transfer():
            until=time.monotonic()+30
            while time.monotonic()<until:
                row=request('engine/status')['library']['transfer']
                if row['status'] not in ('transferring','verifying'):return row
                time.sleep(.1)
            raise AssertionError('transfer deadline')
        try:
            request('models/import',{'path':str(model)})
            assert str(model) in [m['path'] for m in request('engine/status')['models']]
            request('models/import',{'path':str(Path(folder)/'missing.gguf')},expected=400)
            report['checks']['direct_path_and_missing_file']='passed'
            data=model.read_bytes();transfer=request('models/upload/start',{'name':'audit-real-model.gguf','bytes':len(data)})
            route='models/upload/chunk?id='+transfer['id']+'&offset='
            request(route+'1',data[:24],raw=True,expected=400)
            for offset in range(0,len(data),1048576):request(route+str(offset),data[offset:offset+1048576],raw=True)
            request('models/upload/finish',{'id':transfer['id']});result=finish_transfer()
            assert result['status']=='completed' and result['sha256']==hashlib.sha256(data).hexdigest()
            assert Path(result['path']).read_bytes()==data
            report['checks']['real_gguf_chunked_upload_hash_and_publication']='passed'
            transfer=request('models/upload/start',{'name':'cancel-test.gguf','bytes':len(data)})
            request('models/upload/chunk?id='+transfer['id']+'&offset=0',data[:24],raw=True)
            request('models/cancel',{'id':transfer['id']})
            assert finish_transfer()['status']=='cancelled'
            assert not list(engine.library.folder.glob('.nodelift-*.part'))
            report['checks']['upload_cancellation_and_partial_cleanup']='passed'
            request('providers/configure',{'backend':'local_api','base_url':f'http://127.0.0.1:{provider.server_port}/v1','api_key':'synthetic-audit-key'})
            listed=request('providers/models',{'backend':'local_api'});assert listed['models'][0]['id']=='synthetic-audit-model'
            status=request('engine/status');assert 'synthetic-audit-key' not in json.dumps(status)
            request('providers/configure',{'backend':'local_api','api_key':''})
            assert not request('engine/status')['providers']['local_key_set']
            report['checks']['local_api_configure_catalog_clear_key_fixture']='passed'
            if args.public_catalog:
                models=request('providers/models',{'backend':'openrouter'})['models'];assert models
                report['checks']['openrouter_live_public_catalog']={'count':len(models),'cloud_generation':False}
            inference_model=(args.inference_model or model).resolve(strict=True)
            request('models/import',{'path':str(inference_model)})
            request('engine/configure',{'target_model':str(inference_model),'draft_model':'','n_ctx':256,'threads':2,'gpu_layers':0})
            identity=request('engine/run',{'backend':'native','mode':'host','prompt':'Once upon a time','max_tokens':16})['run_id']
            until=time.monotonic()+90
            while time.monotonic()<until:
                status=request('engine/status');run=next(r for r in status['runs'] if r['id']==identity)
                if not status['busy']:break
                time.sleep(.1)
            assert run['status']=='completed',(run['status'],run.get('error'))
            assert run['text'],run
            report['checks']['native_load_and_16_token_run']={'status':run['status'],'text_nonempty':bool(run['text']),'backend':run['backend']}
            report['all_passed']=True
        except Exception as error:
            report['all_passed']=False;report['failure']=str(error)
            raise
        finally:
            args.report.write_text(json.dumps(report,indent=2)+'\n')
            engine.stop()
            if not engine.busy:
                for native in (engine.target,engine.draft):
                    if native:native.close()
            for s in (server,provider):s.shutdown();s.server_close()
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
