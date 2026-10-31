"""Real-weight TLS protocol integration with an emulated node. NOT a phone benchmark."""
import hashlib
import http.client
import json
import ssl
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'host'))
from nodelift.engine import Controller,prefix_digest
from nodelift.host import Server,make_identity
from nodelift.native import Native
from nodelift.state import State

target=ROOT/'.models/qwen2.5-1.5b-instruct-q4_k_m.gguf';draft=ROOT/'.models/qwen2.5-0.5b-instruct-q4_k_m.gguf'
with draft.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
checks=[]
with tempfile.TemporaryDirectory(prefix='nodelift-protocol-') as temp, Native() as worker:
    info=worker.call('load',path=str(draft),n_ctx=1024,threads=4,gpu_layers=999)
    state=State(Path(temp));engine=Controller(state)
    engine.configure({'target_model':str(target),'draft_model':str(draft),'n_ctx':1024,'threads':8,'gpu_layers':999})
    cert,key,_,_=make_identity(state.folder,'127.0.0.1')
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key)
    server=Server(('127.0.0.1',0),state,context=context,engine=engine)
    serving=threading.Thread(target=server.serve_forever,daemon=True);serving.start()
    client_context=ssl.create_default_context(cafile=str(cert))
    def connection():return http.client.HTTPSConnection('127.0.0.1',server.server_port,context=client_context,timeout=8)
    conn=connection()
    def request(conn,path,body=None,token=''):
        conn.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,{'Authorization':'Bearer '+token})
        result=conn.getresponse();data=result.read();return result.status,json.loads(data)
    invitation,_=state.invite()
    caps={'model':'Emulated protocol test node, not mobile hardware','engine_ready':True,'draft_sha256':sha,'tokenizer_fingerprint':info['tokenizer_fingerprint']}
    status,paired=request(conn,'/v1/pair',{'invite':invitation,'name':'Loopback test node','capabilities':caps})
    assert status==200
    token=paired['token'];node=paired['node_id']
    behavior={'mode':'valid'};stop=threading.Event();errors=[];late_replies=[];late_received=threading.Event()
    def work_loop():
        c=connection()
        try:
            while not stop.is_set():
                status,result=request(c,'/v1/engine/poll',token=token)
                assert status==200
                work=result.get('work')
                if not work:continue
                if behavior['mode']=='drop':continue
                if behavior['mode']=='slow':time.sleep(.7)
                assert prefix_digest(work['prefix'])==work['prefix_hash']
                answer={k:work[k] for k in ('id','epoch','prefix_hash','tokenizer_fingerprint','model_sha256')}
                if behavior['mode']=='error':answer['error']='injected thermal pause'
                elif behavior['mode']=='wrong':answer['tokens']=[0]*work['count']
                else:answer['tokens']=worker.call('draft',prefix=work['prefix'],count=work['count'])['tokens']
                status,_=request(c,'/v1/engine/result',answer,token)
                if behavior['mode']=='slow' and status==400:
                    late_replies.append(work['id']);late_received.set();continue
                assert status==200
        except Exception as error:
            if not stop.is_set():errors.append(str(error))
        finally:c.close()
    thread=threading.Thread(target=work_loop,daemon=True);thread.start()
    def run(mode,policy='fixed'):
        # Model loading can outlast the server's idle keepalive. A heartbeat
        # uses a fresh connection; the polling worker still reuses its TLS link.
        heartbeat=connection()
        try:assert request(heartbeat,'/v1/heartbeat',caps,token)[0]==200
        finally:heartbeat.close()
        engine.start({'prompt':'Explain the difference between RAM capacity and bandwidth.','max_tokens':32,
                      'mode':mode,'node_id':node,'draft_k':4,'draft_policy':policy,'remote_timeout_ms':500})
        deadline=time.monotonic()+60
        while engine.busy:
            if time.monotonic()>deadline:engine.stop();raise TimeoutError('loopback integration')
            time.sleep(.02)
        value=engine.status()['runs'][0];assert value['status']=='completed',value.get('error')
        return value
    try:
        baseline=run('host')
        for mode in ('valid','wrong','error','drop'):
            behavior['mode']=mode
            if mode=='drop':
                original=engine.mailbox.request
                engine.mailbox.request=lambda node,payload,cancel,**kwargs:original(node,payload,cancel,timeout=.15)
            value=run('remote_draft')
            assert value['tokens']==baseline['tokens'],f'output drift: {mode}'
            if mode in ('error','drop'):assert value['metrics']['fallbacks']==1
            if mode=='wrong':assert value['metrics']['accepted_tokens']==0
            checks.append({'case':mode,'exact_tokens':True,'generated':len(value['tokens']),
                           'fallbacks':value['metrics']['fallbacks'],'blocks':len(value['blocks'])})
        engine.mailbox.request=original
        behavior['mode']='slow'
        value=run('remote_draft','adaptive')
        assert value['tokens']==baseline['tokens'] and value['metrics']['fallbacks']==1
        assert value['metrics']['draft_disabled_reason']=='remote_failure'
        assert late_received.wait(3),'late result was not observed/rejected'
        deadlines=[b['effective_timeout_ms'] for b in value['blocks'] if b.get('effective_timeout_ms') is not None]
        assert len(deadlines)==1 and 0<deadlines[0]<=500
        checks.append({'case':'adaptive deadline and late reply','exact_tokens':True,'generated':len(value['tokens']),
                       'fallbacks':1,'late_replies_rejected':len(late_replies),'effective_deadline_ms':deadlines[0]})
        assert not errors,errors
    finally:
        stop.set();engine.stop();thread.join(7);conn.close();server.shutdown();server.server_close()
        for native in (engine.target,engine.draft):
            if native:native.close()
report={'scope':'loopback TLS with emulated native node; NOT Android/iOS device evidence',
        'real_weights':True,'checks':checks,'timestamp':time.time()}
(ROOT/'artifacts/remote-loopback.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
