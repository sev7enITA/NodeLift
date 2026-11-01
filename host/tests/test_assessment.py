import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nodelift.state import State, digest


class DeviceAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.now = 1000
        self.clock = patch('nodelift.state.time.time', side_effect=lambda:self.now)
        self.clock.start()
        self.state = State(self.temp.name, automatic_assessment=True)
        self.caps = {'supported_jobs':['network','cpu'],'battery_percent':90,'thermal':'nominal',
                     'engine_ready':True,'draft_sha256':'control','tokenizer_fingerprint':'control'}
        invite,_ = self.state.invite()
        self.peer = self.state.pair(invite,'Fixture',self.caps,device_key='a'*64,peer_address='192.168.1.2')
        self.node = self.peer['node_id']

    def tearDown(self):
        self.clock.stop();self.temp.cleanup()

    def snapshot(self):return self.state.snapshot()['nodes'][0]
    def next_job(self, **kw):return self.state.heartbeat(self.node,self.caps,**kw)['job']
    def finish(self, job, status='completed', samples=None):
        return self.state.finish(self.node,{'job_id':job['id'],'status':status,'samples':samples or []})
    def network(self):
        return [{'kind':'rtt','bytes':64,'ms':m} for m in (1,2,3,10)]+[
            {'kind':'download','bytes':1048576,'ms':100}, {'kind':'upload','bytes':1048576,'ms':200}]

    def test_sequential_automatic_once_and_measured_classification(self):
        self.assertEqual(self.snapshot()['assessment']['state'],'pending')
        self.assertEqual(len(self.state.snapshot()['jobs']),2)
        job=self.next_job();self.assertEqual(job['kind'],'network')
        self.assertIsNone(self.next_job())
        self.assertEqual(self.snapshot()['assessment']['state'],'running')
        self.finish(job,samples=self.network())
        job=self.next_job();self.assertEqual(job['kind'],'cpu')
        self.finish(job,samples=[{'kind':'cpu','iterations':3000,'ms':1500,'checksum':1}])
        report=self.snapshot()['assessment']
        self.assertEqual(report['classification'],'draft_candidate')
        self.assertEqual(report['state'],'completed')
        self.assertFalse(report['llm_qualified'])
        self.assertEqual(report['network']['rtt_p95_ms'],10)
        self.assertEqual(report['network']['download_mib_s'],10)
        self.assertEqual(report['network']['upload_mib_s'],5)
        self.assertEqual(report['cpu']['iterations_per_second'],2000)
        self.assertIsNone(self.next_job())
        invite,_=self.state.invite();self.state.pair(invite,'Fixture',self.caps,device_key='a'*64)
        self.assertEqual(len(self.state.snapshot()['jobs']),2,'Re-pair must not silently rerun assessment')

    def test_assessment_jobs_do_not_overlap_across_devices(self):
        invite,_=self.state.invite();second=self.state.pair(invite,'Second fixture',self.caps)
        first=self.next_job()
        self.assertIsNone(self.state.heartbeat(second['node_id'],self.caps)['job'])
        self.finish(first,samples=self.network())
        other=self.state.heartbeat(second['node_id'],self.caps)['job']
        self.assertEqual(other['kind'],'network')
        self.assertIsNone(self.next_job())

    def test_failed_network_does_not_claim_llm_or_hide_cpu_pass(self):
        self.finish(self.next_job(),status='failed')
        self.finish(self.next_job(),samples=[{'kind':'cpu','iterations':1,'ms':1}])
        report=self.snapshot()['assessment']
        self.assertEqual((report['state'],report['reason']),('partial','network_failed'))
        self.assertEqual(report['classification'],'needs_attention')
        self.assertIsNone(report['network']);self.assertFalse(report['llm_qualified'])

    def test_deadline_releases_next_step_and_assessment_retry_is_bounded(self):
        self.next_job();self.now+=121
        job=self.next_job();self.assertEqual(job['kind'],'cpu')
        self.finish(job,samples=[{'kind':'cpu','iterations':1,'ms':1}])
        self.assertEqual(self.snapshot()['assessment']['state'],'partial')
        self.state.assess(self.node)
        with self.assertRaisesRegex(ValueError,'pending'):self.state.assess(self.node)
        self.assertEqual(self.snapshot()['assessment']['state'],'pending')
        self.assertIsNone(self.snapshot()['assessment']['cpu'],'New assessment must not reuse old CPU sample')

    def test_energy_and_busy_defer_automatic_work(self):
        response=self.state.heartbeat(self.node,self.caps,allow_assessment=False)
        self.assertIsNone(response['job']);self.assertEqual(response['assessment'],{'phase':'deferred','reason':'host_busy'})
        self.caps['battery_percent']=10
        response=self.state.heartbeat(self.node,self.caps)
        self.assertIsNone(response['job']);self.assertEqual(response['assessment']['reason'],'low_battery')
        self.caps['battery_percent']=90;self.caps['thermal']='severe';self.assertIsNone(self.next_job())
        self.caps['thermal']='nominal';self.assertEqual(self.next_job()['kind'],'network')

    def test_incomplete_completed_payload_does_not_qualify(self):
        self.finish(self.next_job(),samples=[{'kind':'rtt','ms':0,'bytes':64}])
        self.finish(self.next_job(),samples=[])
        self.assertEqual(self.snapshot()['assessment']['state'],'failed')

    def test_unsupported_peer_gets_no_jobs(self):
        invite,_=self.state.invite();peer=self.state.pair(invite,'No jobs',{'supported_jobs':[]})
        node=next(n for n in self.state.snapshot()['nodes'] if n['id']==peer['node_id'])
        self.assertEqual(node['assessment']['state'],'unsupported')
        self.assertIsNone(self.state.heartbeat(peer['node_id'],{'supported_jobs':[]})['job'])

    def test_ip_and_session_times_are_observed_and_reconnect_is_inferred(self):
        n=self.snapshot();self.assertEqual(n['first_paired_at'],1000);self.assertEqual(n['session_count'],1)
        self.now=1010;self.state.authenticate(self.peer['token'],peer_address='192.168.1.3')
        n=self.snapshot();self.assertEqual(n['ip_address'],'192.168.1.3');self.assertEqual(n['session_started_at'],1000)
        self.now=1031;self.state.authenticate(self.peer['token'],peer_address='192.168.1.4')
        n=self.snapshot();self.assertEqual(n['session_count'],2);self.assertEqual(n['previous_session_ended_at'],1010)
        self.assertEqual(n['session_started_at'],1031)
        self.state.heartbeat(self.node,{**self.caps,'ip_address':'1.1.1.1','session_started_at':999999})
        self.assertEqual(self.snapshot()['ip_address'],'192.168.1.4')
        with self.assertRaises(PermissionError):self.state.authenticate('wrong',peer_address='1.2.3.4')
        self.assertEqual(self.snapshot()['ip_address'],'192.168.1.4')

    def test_route_change_invalidates_assessment_classification(self):
        self.finish(self.next_job(),samples=self.network())
        self.finish(self.next_job(),samples=[{'kind':'cpu','iterations':1,'ms':1}])
        self.state.authenticate(self.peer['token'],peer_address='192.168.2.4')
        self.assertEqual(self.snapshot()['assessment']['reason'],'connection_changed')
        self.assertEqual(self.snapshot()['assessment']['classification'],'needs_assessment')

    def test_legacy_history_is_unknown_until_new_observation(self):
        with tempfile.TemporaryDirectory() as folder:
            with sqlite3.connect(Path(folder)/'state.sqlite3') as db:
                db.execute('CREATE TABLE nodes (id TEXT PRIMARY KEY,token_hash TEXT UNIQUE NOT NULL,name TEXT NOT NULL,capabilities TEXT NOT NULL,last_seen REAL NOT NULL,revoked INTEGER DEFAULT 0)')
                db.execute('INSERT INTO nodes VALUES (?,?,?,?,?,0)',('old',digest('secret'),'Old','{}',500))
            state=State(folder,automatic_assessment=True);n=state.snapshot()['nodes'][0]
            self.assertIsNone(n['ip_address']);self.assertIsNone(n['first_paired_at']);self.assertIsNone(n['session_started_at'])
            self.assertEqual(n['assessment']['reason'],'needs_assessment')
            state.authenticate('secret',peer_address='192.168.1.8')
            n=state.snapshot()['nodes'][0];self.assertIsNone(n['first_paired_at']);self.assertEqual(n['session_started_at'],1000)

if __name__=='__main__':unittest.main()
