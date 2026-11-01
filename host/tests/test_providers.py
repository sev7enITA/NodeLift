import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from nodelift.providers import Providers
from nodelift.engine import Controller
from nodelift.state import State

class Response(io.BytesIO):
    status=200
    def getheader(self,name,default=''):return 'text/event-stream'
class Connection:
    def __init__(self,data,status=200):self.response=Response(data);self.response.status=status;self.requests=[];self.sock=None;self.closed=False
    def request(self,*args,**kwargs):self.requests.append((args,kwargs))
    def getresponse(self):return self.response
    def close(self):self.closed=True

def event(value):return ('data: '+json.dumps(value,ensure_ascii=False)+'\n\n').encode()
def completion(usage=True):
    out=event({'choices':[{'delta':{'content':'Hello 世界'},'finish_reason':None}]})
    out+=event({'choices':[{'delta':{},'finish_reason':'stop'}]})
    if usage:out+=event({'choices':[],'usage':{'prompt_tokens':3,'completion_tokens':2,'total_tokens':5}})
    return out+b'data: [DONE]\n\n'

class ProviderTests(unittest.TestCase):
    def configured(self,backend='openrouter'):
        p=Providers();p.configure({'backend':backend,'api_key':'test-secret'});p.catalogs[backend]=[{'id':'owner/model'}];return p
    def test_secret_session_only_no_network_on_status(self):
        p=self.configured()
        with patch.object(p,'_connection',side_effect=AssertionError('unexpected network')):
            self.assertNotIn('test-secret',json.dumps(p.status()))
        self.assertFalse(Providers().status()['openrouter_key_set'])
        p.configure({'backend':'openrouter','api_key':''});self.assertFalse(p.status()['openrouter_key_set'])
    def test_loopback_only_and_no_self_routing(self):
        p=Providers()
        for url in ('https://evil.test/v1','http://192.168.1.1/v1','http://localhost:9868/v1','http://user:pass@localhost/v1','http://localhost/v1?q=x','http://localhost/elsewhere'):
            with self.subTest(url=url),self.assertRaises(ValueError):p.configure({'backend':'local_api','base_url':url})
        p.configure({'backend':'local_api','base_url':'http://localhost:1234/v1/'});self.assertEqual(p.local_port,1234)
    def test_requires_explicit_model_key_and_host_mode(self):
        p=Providers()
        with self.assertRaises(ValueError):p.validate('openrouter','owner/model')
        p=self.configured()
        with self.assertRaises(ValueError):p.validate('openrouter','unknown')
        with tempfile.TemporaryDirectory() as directory:
            engine=Controller(State(Path(directory)));engine.providers=p
            with self.assertRaises(ValueError):engine.start({'prompt':'test','backend':'openrouter','provider_model':'owner/model','mode':'remote_draft'})
            self.assertFalse(engine.busy)
    def test_stream_unicode_usage_and_no_fallback_payload(self):
        p=self.configured();connection=Connection(completion())
        with patch.object(p,'_connection',return_value=(connection,'/api/v1')):
            rows=list(p.stream('openrouter','owner/model',[{'role':'user','content':'test'}],16,threading.Event()))
        self.assertEqual(''.join(r['text'] for r in rows),'Hello 世界');self.assertEqual(rows[-1]['usage']['total_tokens'],5)
        payload=json.loads(connection.requests[0][0][2]);self.assertFalse(payload['provider']['allow_fallbacks']);self.assertEqual(payload['provider']['data_collection'],'deny')
        self.assertTrue(connection.closed);self.assertIsNone(p.active)
    def test_incomplete_error_and_redirect_never_retried(self):
        for data,status in ((completion()[:-14],200),(b'data: [DONE]\n\n',200),(event({'error':{'message':'test-secret'}}),200),(b'test-secret',302),(b'test-secret',401)):
            p=self.configured();connection=Connection(data,status)
            with patch.object(p,'_connection',return_value=(connection,'/api/v1')):
                with self.assertRaises(ValueError) as error:list(p.stream('openrouter','owner/model',[],16,threading.Event()))
                self.assertNotIn('test-secret',str(error.exception))
            self.assertEqual(len(connection.requests),1)
    def test_cancel_before_request_sends_nothing(self):
        p=self.configured();connection=Connection(completion());cancel=threading.Event();cancel.set()
        with patch.object(p,'_connection',return_value=(connection,'/api/v1')),self.assertRaises(ValueError):list(p.stream('openrouter','owner/model',[],16,cancel))
        self.assertEqual(connection.requests,[])
    def test_public_catalog_omits_authorization(self):
        p=self.configured();connection=Connection(json.dumps({'data':[{'id':'owner/model','architecture':{'output_modalities':['text']},'pricing':{'prompt':'0.01'}}]}).encode())
        with patch.object(p,'_connection',return_value=(connection,'/api/v1')):p.models('openrouter')
        self.assertNotIn('Authorization',connection.requests[0][1]['headers'])
        self.assertEqual(p.status()['models']['openrouter'][0]['pricing']['prompt'],'0.01')
    def test_controller_no_fabricated_tokens_and_distinct_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            engine=Controller(State(Path(directory)));engine.providers=self.configured('local_api');connection=Connection(completion(False))
            with patch.object(engine.providers,'_connection',return_value=(connection,'/v1')):
                engine.start({'prompt':'hello','backend':'local_api','provider_model':'owner/model'})
                deadline=time.monotonic()+2
                while engine.busy and time.monotonic()<deadline:time.sleep(.01)
            row=engine.runs[-1];self.assertEqual(row['status'],'completed');self.assertEqual(row['measurement_scope'],'local_external_server')
            self.assertNotIn('tokens',row);self.assertNotIn('usage',row);self.assertNotIn('tokens_per_second',row['metrics'])

class SlowStreamTests(unittest.TestCase):
    def test_partial_lines_obey_wall_deadline_and_utf8_boundaries(self):
        from nodelift.providers import stream_lines
        now=[0.0]
        class Slow:
            def read1(self,count):now[0]+=1;return b'x'
        with patch('nodelift.providers.time.monotonic',side_effect=lambda:now[0]):
            with self.assertRaisesRegex(ValueError,'deadline'):list(stream_lines(Slow(),threading.Event(),3))
        self.assertLessEqual(now[0],3)
        class Bytes:
            def __init__(self):self.data=iter('data: 世界\n\n'.encode())
            def read1(self,count):
                try:return bytes([next(self.data)])
                except StopIteration:return b''
        lines=list(stream_lines(Bytes(),threading.Event(),time.monotonic()+1))
        self.assertEqual(lines[0].decode(),'data: 世界')
    def test_oversized_partial_line_rejected(self):
        from nodelift.providers import stream_lines
        with self.assertRaisesRegex(ValueError,'limits'):list(stream_lines(Response(b'x'*70000),threading.Event(),time.monotonic()+1))
    def test_cancel_retains_transport_after_http_connection_detaches(self):
        p=Providers()
        class Transport:
            stopped=False
            def shutdown(self,how):self.stopped=True
        transport=Transport();p.active=Connection(b'');p.active_socket=transport;p.cancel()
        self.assertTrue(transport.stopped)

class ProviderShapeTests(unittest.TestCase):
    def test_network_event_shapes_are_sanitized_and_release_connection(self):
        for payload in ([],1,{'choices':{'x':'y'}},{'choices':[1]},{'choices':[{'delta':[1]}]},{'choices':[],'usage':[1]}):
            p=ProviderTests().configured();connection=Connection(event(payload))
            with patch.object(p,'_connection',return_value=(connection,'/api/v1')):
                with self.assertRaisesRegex(ValueError,'Invalid provider event'):list(p.stream('openrouter','owner/model',[],16,threading.Event()))
            self.assertTrue(connection.closed);self.assertIsNone(p.active)
    def test_second_stream_cannot_replace_active_connection(self):
        p=ProviderTests().configured();connection=Connection(completion())
        with patch.object(p,'_connection',return_value=(connection,'/api/v1')):
            stream=p.stream('openrouter','owner/model',[],16,threading.Event());next(stream)
            with self.assertRaisesRegex(ValueError,'already running'):next(p.stream('openrouter','owner/model',[],16,threading.Event()))
            stream.close()
        self.assertIsNone(p.active);self.assertTrue(connection.closed)
    def test_bad_catalog_shapes_do_not_replace_valid_catalog(self):
        for payload in ([],{'data':{}},{'data':[1]},{'data':[{'id':'x','architecture':[1]}]}):
            p=ProviderTests().configured();connection=Connection(json.dumps(payload).encode())
            with patch.object(p,'_connection',return_value=(connection,'/api/v1')),self.assertRaises(ValueError):p.models('openrouter')
            self.assertEqual(p.catalogs['openrouter'],[{'id':'owner/model'}])

    def test_controller_closes_generator_when_its_output_limit_fails(self):
        closed=[]
        def events(*args):
            try:yield {'text':'x'*(1024**2+1),'usage':None,'finish_reason':None}
            finally:closed.append(True)
        with tempfile.TemporaryDirectory() as directory:
            engine=Controller(State(Path(directory)))
            run={'id':'oversize','backend':'local_api','provider_model':'owner/model','prompt':'test','max_tokens':1,'text':'','metrics':{}}
            with patch.object(engine.providers,'stream',side_effect=events):engine._execute_provider(run,{})
            self.assertEqual(run['status'],'failed');self.assertEqual(run['text'],'');self.assertEqual(closed,[True])
