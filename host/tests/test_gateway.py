"""HTTP contract tests. Stub inference here; real-weight tests live in scripts/."""
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from nodelift.host import Server
from nodelift.state import State


class CompletedEngine:
    def __init__(self):
        self.lock = threading.RLock()
        self.runs = []
        self.requests = []

    def start(self, values):
        self.requests.append(values)
        self.runs = [{'id':'contract-run', 'status':'completed', 'text':'Città 🌍',
                      'finish_reason':'stop', 'tokens':[1,2,3], 'prompt_tokens':4}]
        return {'run_id':'contract-run'}

    def stop(self, run_id):
        return {'stopping':False}


class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.engine = CompletedEngine()
        cls.server = Server(('127.0.0.1',0), State(Path(cls.tmp.name)),
                            admin_token='admin-test', client_token='client-test', engine=cls.engine)
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.tmp.cleanup()

    def request(self, path, value=None, token='client-test'):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2)
        body=json.dumps(value) if value is not None else None
        connection.request('POST' if body is not None else 'GET',path,body,
                           {'Authorization':'Bearer '+token})
        response=connection.getresponse();data=response.read();status=response.status
        connection.close();return status,data

    def body(self, **extra):
        return {'model':'nodelift','messages':[{'role':'user','content':'Hello'}],**extra}

    def test_separate_client_and_admin_authority(self):
        self.assertEqual(self.request('/v1/models',token='')[0],401)
        self.assertEqual(self.request('/v1/models',token='admin-test')[0],401)
        self.assertEqual(self.request('/admin/status')[0],401)
        status,data=self.request('/v1/models')
        self.assertEqual(status,200);self.assertEqual(json.loads(data)['data'][0]['id'],'nodelift')

    def test_sampling_options_rejected_before_inference(self):
        count=len(self.engine.requests)
        for extra in ({'temperature':.2},{'frequency_penalty':.1},{'logit_bias':{'1':1}},
                      {'tools':[]},{'stop':['end']},{'stream':'true'},{'n':True},
                      {'max_tokens':1,'max_completion_tokens':2},{'seed':0},{'model':'other'}):
            with self.subTest(extra=extra):
                self.assertEqual(self.request('/v1/chat/completions',self.body(**extra))[0],400)
        self.assertEqual(len(self.engine.requests),count)

    def test_nonstream_usage_and_multiturn(self):
        messages=[{'role':'system','content':'Italiano'},{'role':'user','content':'Ciao'},
                  {'role':'assistant','content':'Salve'},{'role':'user','content':'Continua'}]
        status,data=self.request('/v1/chat/completions',self.body(messages=messages))
        result=json.loads(data)
        self.assertEqual(status,200);self.assertEqual(result['usage']['total_tokens'],7)
        self.assertEqual(result['choices'][0]['message']['content'],'Città 🌍')
        self.assertEqual(self.engine.requests[-1]['messages'],messages)
        status,_=self.request('/v1/chat/completions',self.body(temperature=None,top_p=None,max_tokens=None,nodelift_remote_timeout_ms=1500))
        self.assertEqual(status,200);self.assertEqual(self.engine.requests[-1]['max_tokens'],128)
        self.assertEqual(self.engine.requests[-1]['remote_timeout_ms'],1500)

    def test_sse_valid_unicode_order_and_termination(self):
        status,data=self.request('/v1/chat/completions',self.body(stream=True))
        self.assertEqual(status,200)
        events=[line[6:] for line in data.decode().splitlines() if line.startswith('data: ')]
        self.assertEqual(events[-1],'[DONE]')
        chunks=[json.loads(value) for value in events[:-1]]
        self.assertEqual(chunks[0]['choices'][0]['delta']['role'],'assistant')
        self.assertEqual(''.join(c['choices'][0]['delta'].get('content','') for c in chunks),'Città 🌍')
        self.assertEqual(chunks[-1]['choices'][0]['finish_reason'],'stop')
