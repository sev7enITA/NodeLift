import http.client
import json
from pathlib import Path
import struct
import tempfile
import threading
import unittest
from nodelift.engine import Controller
from nodelift.host import Server
from nodelift.state import State

class ModelApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);cls.state=State(cls.root);cls.engine=Controller(cls.state)
        cls.server=Server(('127.0.0.1',0),cls.state,admin_token='admin-test',client_token='client-test',engine=cls.engine)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.tmp.cleanup()
    def request(self,path,body=None,token='admin-test',origin=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2)
        headers={'Authorization':'Bearer '+token}
        if origin:headers['Origin']=origin
        connection.request('GET' if body is None else 'POST',path,None if body is None else json.dumps(body),headers)
        response=connection.getresponse();data=response.read();status=response.status;connection.close();return status,json.loads(data)
    def test_client_and_cross_origin_cannot_configure_or_import(self):
        for path,body in [('/admin/models/import',{'path':'/tmp/test.gguf'}),('/admin/providers/configure',{'backend':'openrouter','api_key':'not-secret'}),('/admin/models/upload/start',{'name':'x.gguf','bytes':24})]:
            self.assertEqual(self.request(path,body,token='client-test')[0],401)
            self.assertEqual(self.request(path,body,origin='https://evil.test')[0],401)
    def test_import_appears_in_native_catalog_and_missing_file_is_400(self):
        path=self.root/'sample.gguf';path.write_bytes(struct.pack('<4sIQQ',b'GGUF',3,1,1))
        status,_=self.request('/admin/models/import',{'path':str(path)});self.assertEqual(status,200)
        status,data=self.request('/admin/engine/status');self.assertEqual(status,200)
        self.assertIn(str(path.resolve()),[m['path'] for m in data['models']])
        self.assertEqual(self.request('/admin/models/import',{'path':'/not/a/model.gguf'})[0],400)
    def test_key_not_returned_in_configuration_status_or_run_errors(self):
        secret='session-only-credential'
        status,data=self.request('/admin/providers/configure',{'backend':'openrouter','api_key':secret});self.assertEqual(status,200);self.assertNotIn(secret,json.dumps(data))
        _,data=self.request('/admin/engine/status');self.assertNotIn(secret,json.dumps(data));self.assertTrue(data['providers']['openrouter_key_set'])
        status,data=self.request('/admin/engine/run',{'prompt':'Hello','backend':'openrouter','provider_model':'unknown'});self.assertEqual(status,400);self.assertNotIn(secret,json.dumps(data))
        self.request('/admin/providers/configure',{'backend':'openrouter','api_key':''})
