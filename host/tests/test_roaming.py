import json
import socket
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from nodelift.host import PairingEndpoint, Server
from nodelift.state import State
from nodelift.roaming import identity

class RoamingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.state=State(Path(self.tmp.name))
        self.endpoint=PairingEndpoint(self.state,"auto",0,roaming=True)
        self.endpoint.publisher.command=None
    def tearDown(self):self.endpoint.close();self.tmp.cleanup()
    def ticket(self):
        with patch('nodelift.host.route_address',return_value='127.0.0.1'):return self.endpoint.ticket()
    def test_stable_identity_survives_address_change_and_preserves_enrollment(self):
        first=self.ticket();paired=self.state.pair(first['invite'],'Roaming test',{})
        outstanding=self.ticket()
        with patch('nodelift.host.route_address',return_value='127.0.0.2'),patch('nodelift.host.local_address_available',return_value=True),patch('nodelift.host.Server',side_effect=lambda address,*args,**kw:Server(('127.0.0.1',0),*args,**kw)):
            self.endpoint.refresh_network();second=self.endpoint.ticket()
        self.assertEqual(first['sha256'],second['sha256']);self.assertEqual(first['tls_name'],second['tls_name'])
        self.assertNotEqual(first['url'],second['url']);self.assertFalse(self.state.invitation(outstanding['invite'])['pending'])
        self.assertEqual(self.state.authenticate(paired['token']),paired['node_id'])
        context=ssl.create_default_context(cadata=first['certificate'])
        with socket.create_connection(('127.0.0.1',self.endpoint.api.server_port),timeout=3) as raw:
            with context.wrap_socket(raw,server_hostname=first['tls_name']) as tls:
                tls.sendall(('GET /v1/session HTTP/1.1\r\nHost: '+first['tls_name']+'\r\nAuthorization: Bearer '+paired['token']+'\r\nConnection: close\r\n\r\n').encode())
                body=b''
                while block:=tls.recv(4096):body+=block
                self.assertIn(paired['node_id'].encode(),body)
        self.assertEqual(len(self.state.snapshot()['nodes']),1)
    def test_wrong_logical_hostname_fails_tls(self):
        first=self.ticket();context=ssl.create_default_context(cadata=first['certificate'])
        with self.assertRaises(ssl.SSLCertVerificationError):
            with socket.create_connection(('127.0.0.1',self.endpoint.api.server_port),timeout=3) as raw:
                context.wrap_socket(raw,server_hostname='nodelift-'+('0'*32)+'.local')
    def test_missing_key_never_rotates_identity_silently(self):
        self.ticket();(self.state.folder/'roaming-identity/host.key').unlink()
        with self.assertRaises(ValueError):identity(self.state.folder)
    def test_changed_identity_is_not_accepted(self):
        first=self.ticket()
        with tempfile.TemporaryDirectory() as other:
            _,_,pem,_,_=identity(Path(other))
            context=ssl.create_default_context(cadata=pem)
            with self.assertRaises(ssl.SSLCertVerificationError):
                with socket.create_connection(('127.0.0.1',self.endpoint.api.server_port),timeout=3) as raw:
                    context.wrap_socket(raw,server_hostname=first['tls_name'])
