"""One-block local experiment; never emits tokens without target verification."""
from concurrent.futures import ThreadPoolExecutor
import time


def reusable(base, predicted, prefix, count):
    consumed=len(prefix)-len(base)
    if consumed<0 or consumed>len(predicted) or prefix!=base+predicted[:consumed]:
        return [],0
    return predicted[consumed:consumed+count],consumed


class LocalLookahead:
    def __init__(self,native,cancel):
        self.native=native;self.cancel=cancel
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='nodelift-lookahead')
        self.pending=None;self.rows=[]

    def _draft(self,prefix,count):
        if self.cancel.is_set():raise RuntimeError('cancelled')
        begin=time.perf_counter()
        value=self.native.call('draft',prefix=prefix,count=count)
        return {'base':prefix,'tokens':value['tokens'],'native':value.get('timing'),
                'started':begin,'finished':time.perf_counter(),'used':False}

    def initialize(self,prefix,count):
        self.pending=self.pool.submit(self._draft,list(prefix),count)

    def request(self,prefix,count,remaining):
        begin=time.perf_counter();proposal=[];consumed=0;row=None
        if self.pending is not None:
            future=self.pending;self.pending=None
            row=future.result();self.rows.append(row)
            proposal,consumed=reusable(row['base'],row['tokens'],prefix,count)
            row.update(reused=len(proposal),prefix_consumed=consumed,
                       discarded=len(row['tokens'])-consumed-len(proposal))
        if not proposal:
            value=self._draft(list(prefix),count);self.rows.append(value)
            proposal=value['tokens'];value.update(reused=len(proposal),prefix_consumed=0,discarded=0)
        if remaining>len(proposal)+1 and proposal:
            # One extra token predicts the target's possible bonus. Reuse still
            # requires exact authoritative prefix agreement on the next call.
            self.pending=self.pool.submit(self._draft,list(prefix)+proposal,min(count+1,remaining-len(proposal)))
        return {'tokens':proposal,'wait_ms':(time.perf_counter()-begin)*1000}

    def close(self):
        try:
            if self.pending is not None:
                row=self.pending.result();row.update(reused=0,prefix_consumed=0,discarded=len(row['tokens']))
                self.rows.append(row)
        finally:
            self.pending=None;self.pool.shutdown(wait=True,cancel_futures=True)
        return [{k:v for k,v in row.items() if k not in ('base','tokens')} | {'computed':len(row['tokens'])} for row in self.rows]
