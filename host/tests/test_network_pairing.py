"""Regression for a QR retaining an address removed by a hotspot/DHCP change."""
import http.client
import ssl
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from nodelift.host import PairingEndpoint, Server, local_address_available
from nodelift.state import State


class NetworkPairingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = State(Path(self.tmp.name))
        self.endpoint = PairingEndpoint(self.state, "auto", 0)
    def tearDown(self):
        self.endpoint.close()
        self.tmp.cleanup()
    def ticket_at(self, address):
        with patch('nodelift.host.route_address', return_value=address):
            return self.endpoint.ticket()
    def test_address_change_keeps_history_but_replaces_tls_endpoint_and_old_qr(self):
        first = self.ticket_at('127.0.0.1')
        paired = self.state.pair(first['invite'], 'Existing companion', {})
        outstanding = self.ticket_at('127.0.0.1')
        # macOS does not bind other 127/8 addresses by default. Bind the fixture
        # server to 127.0.0.1 while still issuing/verifying the new address's SAN.
        real_server = Server
        with patch('nodelift.host.local_address_available', return_value=True), patch(
            'nodelift.host.Server', side_effect=lambda address, *a, **kw: real_server(('127.0.0.1', 0), *a, **kw)
        ):
            second = self.ticket_at('127.0.0.2')
        self.assertIn('127.0.0.2:', second['url'])
        self.assertNotEqual(first['sha256'], second['sha256'])
        self.assertFalse(self.state.invitation(outstanding['invite'])['pending'])
        self.assertEqual(self.state.authenticate(paired['token']), paired['node_id'])
        # Verify hostname/SAN and exact expected certificate using actual TLS.
        context = ssl.create_default_context(cadata=second['certificate'])
        with socket.create_connection(('127.0.0.1', self.endpoint.api.server_port), timeout=3) as raw:
            with context.wrap_socket(raw, server_hostname='127.0.0.2') as tls:
                tls.sendall(b'GET /health HTTP/1.1\r\nHost: 127.0.0.2\r\nConnection: close\r\n\r\n')
                self.assertIn(b'200 OK', tls.recv(2048))
        again = self.ticket_at('127.0.0.1')
        self.assertEqual(first['sha256'], again['sha256'])
    def test_missing_network_does_not_issue_an_invitation(self):
        with patch('nodelift.host.route_address', side_effect=ValueError('offline')):
            with self.assertRaises(ValueError): self.endpoint.ticket()
        with self.state.db() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM invites').fetchone()[0], 0)
    def test_stale_explicit_address_rejected(self):
        self.endpoint.requested='192.0.2.100'
        with patch('nodelift.host.local_address_available', return_value=False):
            with self.assertRaisesRegex(ValueError,'address changed'): self.endpoint.ticket()
    def test_readiness_detects_move_without_minting_qr(self):
        self.ticket_at('127.0.0.1')
        with patch('nodelift.host.route_address', return_value='127.0.0.2'):
            self.assertFalse(self.endpoint.network_ready())
    def test_never_bind_wildcard_or_public_address(self):
        self.assertFalse(local_address_available('0.0.0.0'))
        self.assertFalse(local_address_available('8.8.8.8'))
        self.assertFalse(local_address_available('192.0.2.1'))
        self.assertFalse(local_address_available('not-an-ip'))

if __name__ == '__main__': unittest.main()
