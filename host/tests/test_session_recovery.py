"""Loopback browser recovery must not expose administrator access cross-site."""
import http.client
import json
import secrets
import threading
import unittest
from nodelift.host import Server


class SessionRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.token = secrets.token_urlsafe(32)
        self.server = Server(('127.0.0.1', 0), None, admin_token=self.token)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = 'http://127.0.0.1:' + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, changes=None, method='POST', body='{}', path='/admin/session/restore'):
        headers = {'Origin': self.origin, 'Sec-Fetch-Site': 'same-origin',
                   'X-NodeLift-Session': 'restore', 'Content-Type': 'application/json'}
        for key, value in (changes or {}).items():
            if value is None:
                headers.pop(key, None)
            else:
                headers[key] = value
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        c.request(method, path, body, headers)
        r = c.getresponse()
        result = r.status, dict(r.getheaders()), json.loads(r.read())
        c.close()
        return result

    def test_recovery_accepts_missing_or_stale_credentials(self):
        for auth in [None, 'Bearer expired']:
            status, headers, data = self.request({'Authorization': auth})
            self.assertEqual(status, 200)
            self.assertEqual(data, {'token': self.token})
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertNotIn('Access-Control-Allow-Origin', headers)
        # A server restart replaces the key; the recovery route returns the new one.
        self.server.admin_token = secrets.token_urlsafe(32)
        self.assertEqual(self.request()[2]['token'], self.server.admin_token)

    def test_cross_site_missing_metadata_and_rebinding_rejected(self):
        for changes in [{'Origin': None}, {'Origin': 'null'}, {'Origin': 'https://example.com'},
                        {'Sec-Fetch-Site': None}, {'Sec-Fetch-Site': 'cross-site'},
                        {'Sec-Fetch-Site': 'same-site'}, {'X-NodeLift-Session': None},
                        {'Content-Type': 'text/plain'}, {'Host': 'attacker.example'}]:
            with self.subTest(changes=changes):
                status, _, data = self.request(changes)
                self.assertEqual(status, 401)
                self.assertNotIn(self.token, json.dumps(data))

    def test_get_and_nonempty_body_rejected(self):
        self.assertEqual(self.request(method='GET')[0], 401)
        self.assertEqual(self.request(body='{"extra":true}')[0], 400)

    def test_admin_endpoints_still_require_bearer(self):
        self.assertEqual(self.request(method='GET', path='/admin/about')[0], 401)
        self.assertEqual(self.request({'Authorization': 'Bearer '+self.token}, method='GET', path='/admin/about')[0], 200)


if __name__ == '__main__':
    unittest.main()
