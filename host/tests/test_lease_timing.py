import threading
import unittest
from nodelift.leases import Mailbox,worker_timing
from nodelift.lookahead import LocalLookahead,reusable

class LeaseTimingTests(unittest.TestCase):
    def run_lease(self,box,epoch='e',sequence=0,timeout=1,op='draft'):
        payload=dict(epoch=epoch,sequence=sequence,pipeline='bounded_v1',op=op,prefix=[1,2],prefix_hash='p',tokenizer_fingerprint='v',model_sha256='m',vocab_size=10,count=4 if op=='draft' else 0)
        out={}
        def request():
            try:out['result']=box.request('phone',payload,threading.Event(),timeout)
            except Exception as e:out['error']=e
        thread=threading.Thread(target=request);thread.start()
        work=box.poll('phone',.5)['work'];self.assertIsNotNone(work)
        return thread,out,work

    def test_late_work_is_recorded_never_credited_and_prefix_is_not_retained(self):
        box=Mailbox();t,out,w=self.run_lease(box,timeout=.02);t.join(1)
        self.assertIsInstance(out['error'],TimeoutError)
        with self.assertRaises(ValueError):box.submit('phone',{**w,'tokens':[3,4], 'telemetry':{'schema_version':1,'worker_total_ms':1}})
        row=box.trace('e')[0]
        self.assertEqual(row['late_proposal_tokens'],2);self.assertEqual(row['committed_proposals'],0)
        self.assertEqual(row['outcome'],'late_discarded');self.assertNotIn('prefix',next(iter(box.history.values()))['message'])
        with self.assertRaises(ValueError):box.submit('phone',{**w,'tokens':[3]})

    def test_sequence_and_parent_identity_are_independent_of_untrusted_timings(self):
        box=Mailbox();t,out,w=self.run_lease(box)
        with self.assertRaises(ValueError):box.submit('phone',{**w,'tokens':[3],'sequence':True})
        box.submit('phone',{**w,'tokens':[3,4],'telemetry':{'schema_version':1,'worker_total_ms':1}});t.join(1)
        box.verified('phone',w['id'],1)
        self.assertEqual(box.trace('e')[0]['uncommitted_proposals'],1)
        t,out,w2=self.run_lease(box,sequence=1)
        box.submit('phone',{**w2,'tokens':[5], 'telemetry':{'schema_version':1,'worker_total_ms':1,'lookahead_parent_id':w['id'],'lookahead_reused':1,'lookahead_computed':2,'lookahead_prefix_consumed':1,'lookahead_discarded':0}});t.join(1)
        self.assertEqual(box.trace('e')[1]['worker']['lookahead_reused'],1)
        t,out,w3=self.run_lease(box,epoch='new',sequence=1)
        box.submit('phone',{**w3,'tokens':[5], 'telemetry':{'schema_version':1,'worker_total_ms':1,'lookahead_parent_id':w['id']}});t.join(1)
        self.assertIsNone(box.trace('new')[0]['worker'])
        self.assertEqual(out['result']['tokens'],[5])

    def test_telemetry_rejects_nonfinite_bool_and_impossible_durations(self):
        for field,value in [('worker_total_ms',float('nan')),('worker_total_ms',True),('native_decode_tokens',True),('lookahead_reused',18),('worker_native_ms',3)]:
            self.assertIsNone(worker_timing({'schema_version':1,'worker_total_ms':2,field:value}))
        self.assertIsNone(worker_timing({'schema_version':1}))
        self.assertIsNone(worker_timing({'schema_version':1,'worker_total_ms':2,'native_total_ms':2,'native_sync_ms':1,'native_after_sync_ms':2}))
        self.assertIsNone(worker_timing({'schema_version':1,'worker_total_ms':2,'lookahead_computed':1,'lookahead_reused':2,'lookahead_prefix_consumed':0,'lookahead_discarded':0}))
        self.assertIsNotNone(worker_timing({'schema_version':1,'worker_total_ms':2,'native_total_ms':1,'native_sync_ms':.8,'native_decode_ms':.9}))

    def test_finish_reports_no_tokens_and_retention_is_bounded(self):
        box=Mailbox();box.max_history=2
        for i in range(4):
            t,out,w=self.run_lease(box,sequence=i,op='finish')
            box.submit('phone',{**w,'tokens':[]});t.join(1)
        self.assertLessEqual(len(box.history),2)

    def test_null_total_is_missing_telemetry_without_discarding_valid_tokens(self):
        box=Mailbox();t,out,w=self.run_lease(box)
        box.submit('phone',{**w,'tokens':[3], 'telemetry':{'schema_version':1,'worker_total_ms':None}})
        t.join(1)
        self.assertEqual(out['result']['tokens'],[3])
        row=box.trace('e')[0]
        self.assertEqual(row['worker_timing_status'],'missing_or_invalid')
        self.assertIsNone(row['worker'])
        self.assertNotIn('unattributed_ms',row)

    def test_rejection_diagnostics_do_not_authorize_or_consume_a_lease(self):
        box=Mailbox();t,out,w=self.run_lease(box)
        with self.assertRaises(ValueError):box.submit('another-phone',{**w,'tokens':[3]})
        self.assertNotIn('rejected_response_count',box.trace('e')[0])
        for update,code in [({'prefix_hash':'private-content'},'identity_mismatch'),
                            ({'sequence':True},'sequence_mismatch'),
                            ({'tokens':[True]},'invalid_token_ids'),
                            ({'tokens':[]},'empty_draft')]:
            with self.assertRaises(ValueError):box.submit('phone',{**w,'tokens':[3],**update})
            row=box.trace('e')[0]
            self.assertEqual(row['last_rejection_code'],code)
            self.assertEqual(row['committed_proposals'],0)
            self.assertNotIn('private-content',str(row))
            self.assertFalse(next(iter(box.history.values()))['received'])
        box.submit('phone',{**w,'tokens':[3]});t.join(1)
        self.assertEqual(out['result']['tokens'],[3])
        self.assertEqual(box.trace('e')[0]['rejected_response_count'],4)
        with self.assertRaises(ValueError):box.submit('phone',{**w,'tokens':[3]})
        self.assertEqual(box.trace('e')[0]['last_rejection_code'],'undelivered_or_replayed')

class LookaheadTests(unittest.TestCase):
    def test_exact_prefix_or_discard(self):
        self.assertEqual(reusable([1,2],[3,4,5],[1,2,3],2),([4,5],1))
        for prefix in ([1],[1,9],[1,2,9],[1,2,3,4,5,6]):
            self.assertEqual(reusable([1,2],[3,4,5],prefix,2),([],0))

    def test_one_worker_overlap_and_mismatch_fallback(self):
        entered=threading.Event();release=threading.Event();active=[0,0]
        class Draft:
            def call(self,op,**kw):
                active[0]+=1;active[1]=max(active)
                if kw['prefix']==[1]:entered.set();release.wait(1)
                try:return {'tokens':list(range(kw['prefix'][-1]+1,kw['prefix'][-1]+1+kw['count']))}
                finally:active[0]-=1
        pipe=LocalLookahead(Draft(),threading.Event());pipe.initialize([1],2)
        self.assertTrue(entered.wait(1));release.set()
        self.assertEqual(pipe.request([1],2,8)['tokens'],[2,3])
        # A target correction invalidates every predicted token.
        self.assertEqual(pipe.request([1,2,9],2,5)['tokens'],[10,11])
        rows=pipe.close();self.assertEqual(active[1],1)
        self.assertTrue(any(r['discarded']>0 for r in rows))
        self.assertTrue(all(r['computed']==r['reused']+r['prefix_consumed']+r['discarded'] for r in rows))
