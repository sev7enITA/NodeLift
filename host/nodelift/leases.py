"""Bounded lease timing ledger. Worker telemetry never authorizes a token."""
import copy
import math
import secrets
import threading
import time
from collections import OrderedDict

IDENTITY = ('id', 'epoch', 'prefix_hash', 'tokenizer_fingerprint', 'model_sha256')
DURATIONS = ('worker_total_ms', 'worker_validation_ms', 'worker_native_ms',
             'native_total_ms', 'native_sync_ms', 'native_after_sync_ms', 'native_decode_ms',
             'lookahead_prior_native_ms', 'lookahead_prior_sync_ms', 'lookahead_prior_after_sync_ms')
COUNTS = ('native_decode_calls', 'native_decode_tokens', 'native_sync_tokens',
          'lookahead_computed', 'lookahead_reused', 'lookahead_prefix_consumed', 'lookahead_discarded')


def worker_timing(value):
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int or value.get('schema_version') != 1:
        return None
    if type(value.get('worker_total_ms')) not in (int, float):return None
    result = {'schema_version': 1, 'evidence': 'self_reported_worker_durations'}
    for key in DURATIONS:
        v = value.get(key)
        if v is not None:
            if type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 600000:
                return None
            result[key] = v
    for key in COUNTS:
        v = value.get(key)
        if v is not None:
            if type(v) is not int or not 0 <= v <= (17 if key.startswith('lookahead_') else 16384):
                return None
            result[key] = v
    for child, parent in (('worker_native_ms','worker_total_ms'), ('worker_validation_ms','worker_total_ms'),
                          ('native_sync_ms','native_total_ms'), ('native_decode_ms','native_total_ms')):
        if child in result and parent in result and result[child] > result[parent] + .1:
            return None
    if all(k in result for k in ('native_total_ms','native_sync_ms','native_after_sync_ms')):
        if abs(result['native_total_ms']-result['native_sync_ms']-result['native_after_sync_ms'])>.1:return None
    lookahead=('lookahead_computed','lookahead_reused','lookahead_prefix_consumed','lookahead_discarded')
    if any(k.startswith('lookahead_') for k in result):
        if not all(k in result for k in lookahead):return None
        if result[lookahead[0]]!=sum(result[k] for k in lookahead[1:]):return None
        if all(k in result for k in ('lookahead_prior_native_ms','lookahead_prior_sync_ms','lookahead_prior_after_sync_ms')):
            if abs(result['lookahead_prior_native_ms']-result['lookahead_prior_sync_ms']-result['lookahead_prior_after_sync_ms'])>.1:return None
    parent=value.get('lookahead_parent_id')
    if isinstance(parent,str) and len(parent)==32 and all(c in '0123456789abcdef' for c in parent):result['lookahead_parent_id']=parent
    if any(k.startswith('lookahead_') for k in result) and 'lookahead_parent_id' not in result:return None
    return result


class Mailbox:
    def __init__(self):
        self.condition = threading.Condition()
        self.pending = {}
        self.history = OrderedDict()
        self.max_history = 512
        self.retention_seconds = 600

    def _prune(self):
        now = time.monotonic()
        for key, entry in list(self.history.items()):
            if entry['finished'] is not None and now-entry['finished'] > self.retention_seconds:
                del self.history[key]
        while len(self.history) > self.max_history:
            key = next((k for k,e in self.history.items() if e['finished'] is not None), None)
            if key is None: break
            del self.history[key]

    def request(self, node, payload, cancel, timeout=30):
        message = {**copy.deepcopy(payload), 'id': secrets.token_hex(16)}
        created = time.monotonic()
        entry = {'message':message, 'created':created, 'expires':created+timeout,
                 'delivered':False, 'result':None, 'finished':None, 'received':False,
                 'record':{'id':message['id'], 'epoch':message['epoch'], 'op':message.get('op','draft'),
                           'sequence':message.get('sequence'), 'created_monotonic':created,
                           'outcome':'queued', 'committed_proposals':0, 'late_proposal_tokens':0,
                           'lookahead_requested':message.get('pipeline')=='bounded_v1'}}
        with self.condition:
            if node in self.pending: raise RuntimeError('node already has an inference lease')
            self._prune()
            self.pending[node] = entry
            self.history[(node,message['id'])] = entry
            self.condition.notify_all()
            try:
                while entry['result'] is None:
                    if cancel.is_set():
                        entry['record']['outcome']='cancelled';raise RuntimeError('cancelled')
                    remaining = entry['expires']-time.monotonic()
                    if remaining <= 0:
                        entry['record']['outcome']='expired';raise TimeoutError('remote draft deadline exceeded')
                    self.condition.wait(min(remaining,.2))
                return entry['result']
            finally:
                if self.pending.get(node) is entry: del self.pending[node]
                entry['finished']=time.monotonic()
                entry['record']['host_wait_ms']=(entry['finished']-created)*1000
                # Keep identity and bounded diagnostics, never prompt/prefix contents.
                entry['message']={k:v for k,v in message.items() if k != 'prefix'}
                self._prune();self.condition.notify_all()

    def poll(self, node, timeout=5):
        deadline=time.monotonic()+timeout
        with self.condition:
            while True:
                entry=self.pending.get(node)
                if entry and not entry['delivered'] and entry['expires']>time.monotonic():
                    now=time.monotonic();entry['delivered']=True;entry['dispatched']=now
                    entry['record'].update(outcome='dispatched',dispatch_monotonic=now,
                                           host_queue_ms=(now-entry['created'])*1000)
                    return {'work':copy.deepcopy(entry['message'])}
                remaining=deadline-time.monotonic()
                if remaining<=0:return {'work':None}
                self.condition.wait(remaining)

    def submit(self, node, result):
        with self.condition:
            self._prune();entry=self.history.get((node,result.get('id')))
            if not entry:
                raise ValueError('unknown, expired or replayed inference lease')
            def reject(code, message):
                # Record only a bounded reason code and host clock, never the
                # rejected payload. Diagnostics do not mark the lease received.
                record=entry['record']
                record['rejected_response_count']=min(record.get('rejected_response_count',0)+1,1000000)
                record['last_rejection_code']=code
                record['last_rejection_monotonic']=time.monotonic()
                raise ValueError(message)
            if not entry['delivered'] or entry['received']:
                reject('undelivered_or_replayed','unknown, expired or replayed inference lease')
            expected=entry['message']
            for field in IDENTITY:
                if result.get(field)!=expected[field]:reject('identity_mismatch','stale or mismatched draft identity')
            if expected.get('pipeline')=='bounded_v1' and (type(result.get('sequence')) is not int or result['sequence']!=expected['sequence']):
                reject('sequence_mismatch','stale draft sequence')
            ids=result.get('tokens',[])
            if not isinstance(ids,list) or len(ids)>expected['count'] or any(type(i) is not int or i<0 or i>=expected['vocab_size'] for i in ids):
                reject('invalid_token_ids','invalid draft token IDs')
            if not ids and not result.get('error') and expected.get('op')!='finish':reject('empty_draft','empty successful draft')
            now=time.monotonic();timing=worker_timing(result.get('telemetry'))
            if timing and timing.get('lookahead_parent_id'):
                parent=self.history.get((node,timing['lookahead_parent_id']))
                if not parent or parent['message']['epoch']!=expected['epoch'] or parent['record']['outcome']!='returned' or parent['message'].get('sequence')!=expected.get('sequence',0)-1:
                    timing=None
            entry['received']=True
            late=entry['finished'] is not None or entry['expires']<=now
            record=entry['record'];record.update(received_monotonic=now,
                host_dispatch_to_result_ms=(now-entry['dispatched'])*1000,
                received_proposal_tokens=len(ids),worker=timing,
                worker_timing_status='valid_self_report' if timing else 'missing_or_invalid',late=late)
            if timing and 'worker_total_ms' in timing:
                record['unattributed_ms']=record['host_dispatch_to_result_ms']-timing['worker_total_ms']
                record['unattributed_scope']='transport, scheduling and unmeasured overhead; not network RTT'
            if late:
                record.update(outcome='late_discarded',late_proposal_tokens=len(ids))
                raise ValueError('unknown, expired or replayed inference lease')
            record['outcome']='worker_error' if result.get('error') else 'returned'
            entry['result']={'tokens':ids,'error':str(result.get('error',''))[:300],
                             'lease_id':expected['id'],'timing':copy.deepcopy(record)}
            self.condition.notify_all();return {'accepted':True}

    def verified(self,node,lease_id,accepted):
        with self.condition:
            entry=self.history.get((node,lease_id))
            if entry and entry['record'].get('outcome')=='returned':
                received=entry['record'].get('received_proposal_tokens',0)
                if type(accepted) is not int or not 0<=accepted<=received:raise ValueError('invalid committed count')
                entry['record'].update(committed_proposals=accepted,uncommitted_proposals=received-accepted)

    def trace(self,epoch):
        with self.condition:
            self._prune()
            return [copy.deepcopy(e['record']) for e in self.history.values() if e['message']['epoch']==epoch]
