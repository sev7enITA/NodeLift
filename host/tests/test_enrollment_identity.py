"""Enrollment identity, credential continuity and owner-confirmed legacy merges."""
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from nodelift.state import State


def proof(token, invitation):
    return hmac.new(hashlib.sha256(token.encode()).digest(),
                    ('nodelift-repair-v1\n'+invitation).encode(), hashlib.sha256).hexdigest()


class EnrollmentIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = State(self.tmp.name)
        self.key = secrets.token_hex(32)

    def tearDown(self):
        self.tmp.cleanup()

    def enroll(self, key=None, previous=None):
        invite, _ = self.state.invite()
        p = {'node_id':previous['node_id'], 'proof':proof(previous['token'], invite)} if previous else None
        return self.state.pair(invite, 'Identical phone model', {}, key, p)

    def test_same_installation_keeps_node_and_rotates_credential(self):
        first = self.enroll(self.key)
        second = self.enroll(self.key)
        self.assertEqual(first['node_id'], second['node_id'])
        self.assertTrue(second['reused'])
        self.assertNotEqual(first['token'], second['token'])
        with self.assertRaises(PermissionError): self.state.authenticate(first['token'])
        self.assertEqual(self.state.authenticate(second['token']), first['node_id'])
        self.assertEqual(len(self.state.snapshot()['nodes']), 1)

    def test_same_model_different_identity_does_not_merge(self):
        self.enroll(self.key); self.enroll(secrets.token_hex(32))
        self.assertEqual(len(self.state.snapshot()['nodes']), 2)
        # Legacy clients remain distinct: matching telemetry is not proof.
        self.enroll(); self.enroll()
        self.assertEqual(len(self.state.snapshot()['nodes']), 4)

    def test_legacy_adoption_requires_proof_and_retains_jobs(self):
        old = self.enroll()
        self.state.queue(old['node_id'], 'cpu')
        new = self.enroll(self.key, old)
        self.assertEqual(old['node_id'], new['node_id'])
        self.assertEqual(self.state.snapshot()['jobs'][0]['state'], 'cancelled')
        self.assertEqual(len(self.state.snapshot()['nodes']), 1)

    def test_forged_proof_does_not_consume_invitation(self):
        old = self.enroll(); invite, _ = self.state.invite()
        with self.assertRaises(PermissionError):
            self.state.pair(invite, 'Fake', {}, self.key, {'node_id':old['node_id'],'proof':'0'*64})
        self.assertTrue(self.state.invitation(invite)['pending'])
        self.assertEqual(self.state.authenticate(old['token']), old['node_id'])

    def test_proof_is_bound_to_invitation_and_cannot_replace_identity(self):
        old = self.enroll(); invite, _ = self.state.invite()
        with self.assertRaises(PermissionError):
            self.state.pair(invite, 'Fake', {}, self.key, {'node_id':old['node_id'],'proof':proof(old['token'],'another-invitation')})
        current = self.enroll(self.key, old)
        with self.assertRaises(PermissionError): self.enroll(secrets.token_hex(32), current)

    def test_lost_response_and_restart_can_recover_using_persisted_identity(self):
        initial_scope = self.state.pairing_scope()
        first = self.enroll(self.key)
        self.state = State(self.tmp.name)
        self.assertEqual(self.state.pairing_scope(), initial_scope)
        self.assertEqual(first['node_id'], self.enroll(self.key)['node_id'])
        self.assertNotIn(self.key, json.dumps(self.state.snapshot()))
        with self.state.db() as db:
            self.assertNotEqual(db.execute('SELECT identity_hash FROM nodes').fetchone()[0], self.key)

    def test_concurrent_invites_do_not_create_two_nodes(self):
        invites = [self.state.invite()[0] for _ in range(2)]
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda invite:self.state.pair(invite,'Same',{},self.key),invites))
        self.assertEqual(results[0]['node_id'],results[1]['node_id'])
        self.assertEqual(len(self.state.snapshot()['nodes']),1)

    def test_revoked_identity_needs_new_valid_invitation(self):
        first = self.enroll(self.key); self.state.revoke(first['node_id'])
        with self.assertRaises(PermissionError): self.state.pair('expired','Same',{},self.key)
        current = self.enroll(self.key)
        self.assertEqual(first['node_id'], current['node_id'])
        self.assertEqual(self.state.authenticate(current['token']),first['node_id'])

    def test_owner_merge_preserves_history_and_current_credential(self):
        old = self.enroll(); current = self.enroll()
        with self.state.db() as db:
            db.execute("INSERT INTO jobs (id,node,kind,state,created) VALUES ('test',?,'cpu','completed',1)",(old['node_id'],))
        self.state.merge_nodes(old['node_id'],current['node_id'],'Owner confirmed same physical phone')
        snapshot = self.state.snapshot()
        self.assertEqual(len(snapshot['nodes']),1)
        self.assertEqual(snapshot['jobs'][0]['node'],current['node_id'])
        self.assertEqual(snapshot['jobs'][0]['original_node'],old['node_id'])
        self.assertEqual(self.state.authenticate(current['token']),current['node_id'])
        with self.assertRaises(PermissionError): self.state.authenticate(old['token'])
        with self.assertRaises(PermissionError): self.enroll(self.key,old)

    def test_identity_cannot_be_used_without_valid_invite(self):
        self.enroll(self.key)
        with self.assertRaises(PermissionError): self.state.pair('missing','Fake',{},self.key)
        self.assertEqual(len(self.state.snapshot()['nodes']),1)


if __name__ == '__main__': unittest.main()
