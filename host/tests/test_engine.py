import threading
import time
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from nodelift.engine import Controller, Mailbox, prefix_digest
from nodelift.state import State


class MailboxTests(unittest.TestCase):
    def payload(self):
        return {'epoch':'epoch','prefix_hash':prefix_digest([1,2]),'tokenizer_fingerprint':'vocab',
                'model_sha256':'model','count':4,'vocab_size':10}

    def launch(self,box,stop,timeout=1):
        outcome={}
        def run():
            try:outcome['value']=box.request('phone',self.payload(),stop,timeout)
            except Exception as e:outcome['error']=e
        thread=threading.Thread(target=run);thread.start()
        return thread,outcome

    def test_identity_and_replay(self):
        box=Mailbox();thread,out=self.launch(box,threading.Event())
        job=box.poll('phone',.5)['work'];self.assertIsNotNone(job)
        with self.assertRaises(ValueError):box.submit('other',{**job,'tokens':[3]})
        with self.assertRaises(ValueError):box.submit('phone',{**job,'epoch':'stale','tokens':[3]})
        with self.assertRaises(ValueError):box.submit('phone',{**job,'tokens':[True]})
        with self.assertRaises(ValueError):box.submit('phone',{**job,'tokens':[10]})
        box.submit('phone',{**job,'tokens':[3,4]});thread.join(1)
        self.assertEqual(out['value']['tokens'],[3,4])
        with self.assertRaises(ValueError):box.submit('phone',{**job,'tokens':[3]})

    def test_timeout_rejects_late_response(self):
        box=Mailbox();thread,out=self.launch(box,threading.Event(),.05)
        job=box.poll('phone',.01)['work'];thread.join(1)
        self.assertIsInstance(out['error'],TimeoutError)
        with self.assertRaises(ValueError):box.submit('phone',{**job,'tokens':[3]})

    def test_cancel_and_single_delivery(self):
        box=Mailbox();stop=threading.Event();thread,out=self.launch(box,stop)
        self.assertIsNotNone(box.poll('phone',.5)['work'])
        self.assertIsNone(box.poll('phone',.01)['work'])
        stop.set();thread.join(1)
        self.assertIn('cancelled',str(out['error']))
        self.assertFalse(box.pending)

    def test_duplicate_lease_and_empty_draft(self):
        box=Mailbox();stop=threading.Event();thread,out=self.launch(box,stop)
        job=box.poll('phone',.5)['work']
        with self.assertRaises(RuntimeError):box.request('phone',self.payload(),stop,.01)
        with self.assertRaises(ValueError):box.submit('phone',{**job,'tokens':[]})
        box.submit('phone',{**job,'error':'thermal pause'});thread.join(1)
        self.assertEqual(out['value']['error'],'thermal pause')


class ControllerTests(unittest.TestCase):
    def test_stream_keeps_partial_utf8_until_complete_and_detokenizes_only_delta(self):
        class SplitNative:
            def __init__(self):self.index=0;self.text_requests=[]
            def call(self, op, **args):
                if op=='tokenize':return {'tokens':[42]}
                if op=='draft':
                    self.index+=1;return {'tokens':[self.index], 'eos':self.index==2}
                if op=='text':
                    self.text_requests.append(args['tokens'])
                    return {'bytes_hex':{1:'f09f',2:'8c8d'}[args['tokens'][0]]}
                return {}
        with tempfile.TemporaryDirectory() as folder:
            engine=Controller(State(Path(folder)));engine.target=SplitNative()
            engine.target_info={'tokenizer_fingerprint':'test'}
            run={'id':'split','mode':'host','prompt':'Hello','max_tokens':2,'draft_k':1,'text':'','metrics':{},'blocks':[]}
            snapshots=[]
            with patch.object(engine,'_load'),patch.object(engine,'_sha',return_value='test'),patch.object(engine,'_publish',side_effect=lambda r:snapshots.append(r['text'])):
                engine._execute(run,{'n_ctx':256,'target_model':'unused'})
            self.assertEqual(run['status'],'completed');self.assertEqual(run['text'],'🌍')
            self.assertNotIn('�',''.join(snapshots));self.assertIn('',snapshots)
            self.assertEqual(engine.target.text_requests,[[1],[2]])

    def test_disappearing_catalog_entry_does_not_break_status(self):
        with tempfile.TemporaryDirectory() as folder:
            engine=Controller(State(Path(folder)))
            with patch.object(Path,'rglob',return_value=iter([Path('/missing-model.gguf')])),patch.object(Path,'stat',side_effect=FileNotFoundError):
                self.assertEqual(engine.models(refresh=True),[])

    def test_remote_timeout_bounds_before_worker_start(self):
        with tempfile.TemporaryDirectory() as folder:
            engine=Controller(State(Path(folder)))
            for timeout in (True,0,499,60001,'500'):
                with self.assertRaises(ValueError):engine.start({'prompt':'Hello','remote_timeout_ms':timeout})
            self.assertFalse(engine.busy)
