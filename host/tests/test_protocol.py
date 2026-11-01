import http.client
import json
from pathlib import Path
import ssl
import tempfile
import threading
import time
import unittest

from nodelift.host import Server, make_identity, public_key_pin
from nodelift.state import State, digest
from nodelift import __version__


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.state = State(Path(cls.tmp.name))
        cls.cert, key, _, cls.fingerprint = make_identity(cls.state.folder, "127.0.0.1")
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cls.cert, key)
        cls.server = Server(("127.0.0.1", 0), cls.state, context=ctx)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.admin = Server(("127.0.0.1", 0), cls.state, admin_token="test-admin", ticket_factory=lambda: {"test": True})
        cls.admin_thread = threading.Thread(target=cls.admin.serve_forever, daemon=True)
        cls.admin_thread.start()

    @classmethod
    def tearDownClass(cls):
        for s in (cls.server, cls.admin):
            s.shutdown(); s.server_close()
        cls.tmp.cleanup()

    def request(self, path, value=None, token="", method=None):
        context = ssl.create_default_context(cafile=str(self.cert))
        conn = http.client.HTTPSConnection("127.0.0.1", self.server.server_port, context=context, timeout=3)
        headers = {"Authorization": "Bearer " + token}
        body = json.dumps(value).encode() if value is not None else None
        conn.request(method or ("POST" if body is not None else "GET"), path, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read()
        status = response.status
        conn.close()
        return status, data

    def pair(self, name="Test node"):
        code, _ = self.state.invite()
        status, data = self.request("/v1/pair", {"invite": code, "name": name, "capabilities": {"os": "test", "physical_memory_bytes": 8192}})
        self.assertEqual(status, 200)
        return json.loads(data)

    def test_pair_invitation_is_single_use(self):
        code, _ = self.state.invite()
        value = {"invite": code, "name": "One use", "capabilities": {}}
        self.assertEqual(self.request("/v1/pair", value)[0], 200)
        self.assertEqual(self.request("/v1/pair", value)[0], 401)

    def test_expired_invitation(self):
        code, _ = self.state.invite()
        with self.state.db() as db:
            db.execute("UPDATE invites SET expires=? WHERE hash=?", (time.time()-1, digest(code)))
        self.assertEqual(self.request("/v1/pair", {"invite":code,"name":"Expired","capabilities":{}})[0],401)

    def test_admin_invitation_status_revoke_and_replay(self):
        def admin(path, code, token="test-admin"):
            c = http.client.HTTPConnection("127.0.0.1", self.admin.server_port, timeout=3)
            c.request("POST", path, json.dumps({"invite":code}), {"Authorization":"Bearer "+token})
            response=c.getresponse(); result=(response.status,json.loads(response.read())); c.close(); return result
        code, _ = self.state.invite()
        other, _ = self.state.invite()
        self.assertEqual(admin('/admin/invite/status',code,token='')[0],401)
        self.assertEqual(admin('/admin/invite/revoke',code,token='')[0],401)
        self.assertEqual(admin('/admin/invite/status',code),(200,{'pending':True}))
        self.assertEqual(admin('/admin/invite/revoke',code),(200,{'pending':False}))
        self.assertEqual(self.request('/v1/pair',{'invite':code,'name':'Revoked'})[0],401)
        self.assertEqual(admin('/admin/invite/status',other),(200,{'pending':True}))
        self.assertEqual(self.request('/v1/pair',{'invite':other,'name':'Used'})[0],200)
        self.assertEqual(admin('/admin/invite/status',other),(200,{'pending':False}))
        self.assertEqual(admin('/admin/invite/status',None)[0],400)

    def test_qr_assets_are_local_and_do_not_contain_invitation(self):
        for path, content in [('/qr.js',b'Project Nayuki'),('/pairing.js',b'NodeLiftPairing')]:
            c=http.client.HTTPConnection('127.0.0.1',self.admin.server_port,timeout=3)
            c.request('GET',path);response=c.getresponse();data=response.read();c.close()
            self.assertEqual(response.status,200);self.assertTrue(content in data)

    def test_concurrent_consume_and_close_have_one_consistent_winner(self):
        from concurrent.futures import ThreadPoolExecutor
        for _ in range(24):
            code, _ = self.state.invite()
            barrier=threading.Barrier(2)
            def consume():
                barrier.wait()
                try:return self.state.pair(code,'Concurrent QR test',{})
                except PermissionError:return None
            def close():
                barrier.wait();return self.state.invitation(code,revoke=True)
            with ThreadPoolExecutor(max_workers=2) as pool:
                paired, closed = pool.submit(consume), pool.submit(close)
                result=paired.result();self.assertFalse(closed.result()['pending'])
            self.assertFalse(self.state.invitation(code)['pending'])
            with self.assertRaises(PermissionError):self.state.pair(code,'Replay',{})
            if result:
                # Close only cancels unused invitations; completed sessions need explicit revocation.
                self.assertEqual(self.state.authenticate(result['token']),result['node_id'])
                self.state.revoke(result['node_id'])

    def test_authentication_and_revocation(self):
        p = self.pair()
        self.assertEqual(self.request("/v1/probe?size=64")[0], 401)
        self.assertEqual(self.request("/v1/probe?size=64", token=p["token"])[0], 200)
        self.state.revoke(p["node_id"])
        self.assertEqual(self.request("/v1/probe?size=64", token=p["token"])[0], 401)

    def test_measured_payload_and_size_bound(self):
        p = self.pair()
        for size in (64,16384,1048576):
            status,data = self.request(f"/v1/probe?size={size}", token=p["token"])
            self.assertEqual(status,200);self.assertEqual(len(data),size)
        self.assertEqual(self.request("/v1/probe?size=1048577",token=p["token"])[0],400)

    def test_job_is_leased_once_and_result_not_replayed(self):
        p = self.pair()
        job = self.state.queue(p["node_id"], "network")["job_id"]
        status,data = self.request("/v1/heartbeat",{},p["token"])
        self.assertEqual(status,200);self.assertEqual(json.loads(data)["job"]["id"],job)
        self.assertIsNone(json.loads(self.request("/v1/heartbeat",{},p["token"])[1])["job"])
        result={"job_id":job,"status":"completed","samples":[{"kind":"rtt","ms":1.5,"bytes":64}]}
        self.assertEqual(self.request("/v1/result",result,p["token"])[0],200)
        self.assertEqual(self.request("/v1/result",result,p["token"])[0],400)

    def test_other_node_cannot_submit_result(self):
        a,b=self.pair("A"),self.pair("B")
        job=self.state.queue(a["node_id"],"network")["job_id"]
        self.state.heartbeat(a["node_id"],{})
        self.assertEqual(self.request("/v1/result",{"job_id":job,"status":"completed","samples":[]},b["token"])[0],400)

    def test_timed_out_job_rejects_late_result(self):
        p=self.pair();job=self.state.queue(p["node_id"],"cpu")["job_id"]
        self.state.heartbeat(p["node_id"],{})
        with self.state.db() as db:
            db.execute("UPDATE jobs SET started=? WHERE id=?",(time.time()-121,job))
        self.assertEqual(self.request("/v1/result",{"job_id":job,"status":"completed","samples":[]},p["token"])[0],400)
        self.assertEqual(next(j for j in self.state.snapshot()["jobs"] if j["id"]==job)["state"],"timed_out")

    def test_nonfinite_telemetry_and_unknown_jobs_rejected(self):
        p=self.pair()
        self.assertEqual(self.request("/v1/heartbeat",{"physical_memory_bytes":float("nan")},p["token"])[0],400)
        with self.assertRaises(ValueError):self.state.queue(p["node_id"],"run-shell")

    def test_tls_untrusted_certificate_rejected(self):
        conn=http.client.HTTPSConnection("127.0.0.1",self.server.server_port,context=ssl.create_default_context(),timeout=3)
        try:
            with self.assertRaises(ssl.SSLCertVerificationError):conn.request("GET","/health")
        finally:conn.close()

    def test_admin_origin_and_token_required(self):
        def request(headers):
            c=http.client.HTTPConnection("127.0.0.1",self.admin.server_port,timeout=3)
            c.request("GET","/admin/status",headers=headers);r=c.getresponse();r.read();code=r.status;c.close();return code
        self.assertEqual(request({}),401)
        self.assertEqual(request({"Authorization":"Bearer test-admin","Origin":"https://attacker.invalid"}),401)
        self.assertEqual(request({"Authorization":"Bearer test-admin"}),200)

    def test_credentials_never_in_snapshot(self):
        p=self.pair();snapshot=json.dumps(self.state.snapshot())
        self.assertNotIn(p["token"],snapshot)
        self.assertNotIn("token_hash",snapshot)

    def test_about_reports_installed_host_not_protocol_snapshot_version(self):
        for token, expected_status in (("", 401), ("test-admin", 200)):
            connection = http.client.HTTPConnection("127.0.0.1", self.admin.server_port, timeout=3)
            try:
                connection.request("GET", "/admin/about", headers={"Authorization": "Bearer " + token})
                response = connection.getresponse()
                data = json.loads(response.read())
                self.assertEqual(response.status, expected_status)
                if expected_status == 200:
                    self.assertEqual(data, {"version": __version__, "component": "host", "release_channel": "source-preview"})
                    self.assertNotEqual(data["version"], self.state.snapshot()["version"])
            finally:
                connection.close()
        self.assertFalse(self.state.snapshot()["inference_available"])

    def test_host_inventory_is_only_returned_to_dashboard_admin(self):
        c = http.client.HTTPConnection("127.0.0.1", self.admin.server_port, timeout=5)
        try:
            c.request("GET", "/admin/status", headers={"Authorization": "Bearer test-admin"})
            response = c.getresponse()
            value = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(value["host"]["id"], "host")
            self.assertIsNone(value["host"]["available_memory_bytes"])
            self.assertIsInstance(value["observed_at"], (int, float))
            self.assertNotIn("hostname", value["host"])
        finally:
            c.close()

    def test_public_key_pin_is_sha256_base64(self):
        import base64
        self.assertEqual(len(base64.b64decode(public_key_pin(self.cert))),32)

    def test_network_only_node_cannot_receive_cpu(self):
        p=self.pair()
        self.state.heartbeat(p["node_id"],{"supported_jobs":["network"]})
        with self.assertRaises(ValueError):self.state.queue(p["node_id"],"cpu")

    def test_connection_id_identifies_persistent_socket(self):
        p=self.pair()
        context=ssl.create_default_context(cafile=str(self.cert))
        c=http.client.HTTPSConnection("127.0.0.1",self.server.server_port,context=context,timeout=3)
        ids=[]
        try:
            for _ in range(2):
                c.request("GET","/v1/probe?size=64",headers={"Authorization":"Bearer "+p["token"]})
                r=c.getresponse();self.assertEqual(r.status,200);ids.append(r.getheader("X-NodeLift-Connection-ID"));r.read()
            self.assertTrue(ids[0]);self.assertEqual(ids[0],ids[1])
        finally:c.close()


if __name__ == "__main__":unittest.main()
