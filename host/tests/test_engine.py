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
    def test_stop_during_load_does_not_create_draft_or_begin_prefill(self):
        entered=threading.Event();release=threading.Event();instances=[]
        class LoadingNative:
            def __init__(self):self.calls=[];self.was_cancelled=False;instances.append(self)
            def call(self,op,**args):
                self.calls.append(op)
                if op=='load':entered.set();release.wait(2);return {'tokenizer_fingerprint':'test'}
                raise AssertionError('no inference should start after stop')
            def cancel(self):self.was_cancelled=True
            def close(self):pass
        with tempfile.TemporaryDirectory() as folder:
            engine=Controller(State(Path(folder)));engine.busy=True
            run={'id':'load-stop','mode':'local_draft','draft_policy':'fixed','prompt':'Hello','max_tokens':32,
                 'draft_k':4,'text':'','metrics':{},'blocks':[]}
            config={'n_ctx':256,'target_model':'target','draft_model':'draft','threads':4,'gpu_layers':0}
            with patch('nodelift.engine.Native',LoadingNative),patch.object(engine,'_sha',return_value='test'):
                thread=threading.Thread(target=engine._execute,args=(run,config));thread.start()
                try:
                    self.assertTrue(entered.wait(1));engine.stop()
                finally:release.set();thread.join(2)
            self.assertFalse(thread.is_alive());self.assertEqual(run['status'],'cancelled')
            self.assertEqual(len(instances),1);self.assertTrue(instances[0].was_cancelled)
            self.assertEqual(instances[0].calls,['load'])

    def test_adaptive_cold_draft_cost_is_measured_and_short_run_never_loads_it(self):
        now=[0.0];loads=[]
        class ColdNative:
            def call(self,op,**args):
                if op=='tokenize':return {'tokens':[1]}
                if op=='draft':
                    now[0]+=.005
                    return {'tokens':[2]*args['count'],'eos':False}
                if op=='verify':
                    now[0]+=.005
                    return {'tokens':[2],'accepted':0,'proposed':len(args['proposal']),'eos':False}
                if op=='text':return {'bytes_hex':'78'}
                return {}
        with tempfile.TemporaryDirectory() as folder:
            engine=Controller(State(Path(folder)));engine.target=ColdNative()
            engine.target_info={'tokenizer_fingerprint':'test'}
            def load(config,use_draft):
                loads.append(use_draft)
                if use_draft:now[0]+=.250;engine.draft=ColdNative()
            def run(count):
                record={'id':str(count),'mode':'local_draft','draft_policy':'adaptive','prompt':'Hello','max_tokens':count,
                        'draft_k':4,'text':'','metrics':{},'blocks':[]}
                engine._execute(record,{'n_ctx':256,'target_model':'unused','draft_model':'unused'})
                return record
            with patch.object(engine,'_load',side_effect=load),patch.object(engine,'_sha',return_value='test'),patch('nodelift.engine.time.perf_counter',side_effect=lambda:now[0]):
                short=run(3)
                self.assertEqual(short['status'],'completed',short.get('error'));self.assertEqual(loads,[False]);self.assertIsNone(engine.draft)
                long=run(12)
            self.assertEqual(long['status'],'completed',long.get('error'))
            self.assertEqual(loads,[False,False,True])
            self.assertGreater(long['blocks'][4]['draft_ms'],250)
            self.assertEqual(long['metrics']['draft_disabled_reason'],'probe_cost_exceeded')

    def test_cancelled_proposal_is_never_verified_or_published(self):
        class CancellingNative:
            def __init__(self):self.calls=[]
            def call(self,op,**args):
                self.calls.append(op)
                if op=='tokenize':return {'tokens':[1]}
                if op=='draft':engine.cancelled.set();return {'tokens':[2],'eos':False}
                return {}
        with tempfile.TemporaryDirectory() as folder:
            engine=Controller(State(Path(folder)));engine.target=CancellingNative();engine.draft=CancellingNative()
            engine.target_info={'tokenizer_fingerprint':'test'}
            run={'id':'stop','mode':'local_draft','draft_policy':'fixed','prompt':'Hello','max_tokens':32,
                 'draft_k':4,'text':'','metrics':{},'blocks':[]}
            with patch.object(engine,'_load'),patch.object(engine,'_sha',return_value='test'):
                engine._execute(run,{'n_ctx':256,'target_model':'unused','draft_model':'unused'})
            self.assertEqual(run['status'],'cancelled');self.assertEqual(run['tokens'],[])
            self.assertNotIn('verify',engine.target.calls);self.assertFalse(run['blocks'])

    def test_adaptive_controller_preserves_output_and_stops_slow_draft(self):
        now=[0.0]
        class ControlledNative:
            def __init__(self,draft=False):self.drafter=draft;self.calls=[]
            def call(self,op,**args):
                self.calls.append(op)
                if op=='tokenize':return {'tokens':[1]}
                if op=='draft':
                    now[0]+=.040 if self.drafter else .005
                    return {'tokens':list(range(len(args['prefix'])+1,len(args['prefix'])+args['count']+1)),'eos':False}
                if op=='verify':
                    now[0]+=.005
                    n=min(len(args['proposal'])+1,args['remaining'])
                    return {'tokens':list(range(len(args['prefix'])+1,len(args['prefix'])+n+1)),
                            'accepted':min(len(args['proposal']),n),'proposed':len(args['proposal']),'eos':False}
                if op=='text':return {'bytes_hex':('x'*len(args['tokens'])).encode().hex()}
                return {}
        with tempfile.TemporaryDirectory() as folder:
            engine=Controller(State(Path(folder)));engine.target=ControlledNative();engine.draft=ControlledNative(True)
            engine.target_info={'tokenizer_fingerprint':'test'}
            run={'id':'adaptive','mode':'local_draft','draft_policy':'adaptive','prompt':'Hello','max_tokens':32,
                 'draft_k':4,'text':'','metrics':{},'blocks':[]}
            with patch.object(engine,'_load'),patch.object(engine,'_sha',return_value='test'),patch('nodelift.engine.time.perf_counter',side_effect=lambda:now[0]):
                engine._execute(run,{'n_ctx':256,'target_model':'unused','draft_model':'unused'})
            self.assertEqual(run['status'],'completed',run.get('error'))
            self.assertEqual(run['tokens'],list(range(2,34)))
            self.assertEqual(engine.draft.calls.count('draft'),2)
            self.assertNotIn('prefill',engine.draft.calls)
            self.assertEqual(run['metrics']['draft_disabled_reason'],'no_measured_gain')
            self.assertEqual(run['metrics']['fallbacks'],0)
            self.assertTrue(all(b['effective_mode']=='host' for b in run['blocks'][-4:]))

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
