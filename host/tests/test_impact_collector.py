"""Real HTTP/SSE parsing, not inference performance evidence."""
import http.server
import importlib.util
import json
from pathlib import Path
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch
import unittest

spec=importlib.util.spec_from_file_location('impact_collector',Path(__file__).resolve().parents[2]/'scripts/benchmark-impact.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)


class CollectorTests(unittest.TestCase):
    def stream(self, events, administrative_clock_shift=False, **capture_options):
        requests=[]
        self.requests=requests
        clock_offset=[0]
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
                self.wfile.write(b': heartbeat\n\n')
                for event in events:
                    self.wfile.write(b'data: '+(event.encode() if isinstance(event,str) else json.dumps(event).encode())+b'\n\n')
                    self.wfile.flush()
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        c=collector.Client.__new__(collector.Client);c.port=server.server_port;c.client_token='test'
        stopped=[]
        def admin(path,body=None):
            if administrative_clock_shift:clock_offset[0]=2_000_000_000
            if path=='engine/stop':stopped.append(body);return {}
            return {'runs':[{'id':'id','status':'completed','tokens':[1,2], 'metrics':{},'identity':{},'text':' hello'}]}
        c.admin=admin
        clock=SimpleNamespace(perf_counter_ns=time.perf_counter_ns, time_ns=lambda:time.time_ns()+clock_offset[0], sleep=time.sleep)
        try:
            with patch.object(collector,'time',clock):
                return c.capture('public prompt','host',None,2,500,**capture_options),stopped
        finally:server.shutdown();server.server_close();t.join()

    def event(self, content=None, reason=None, identifier='id'):
        delta={'role':'assistant'} if content is None else {'content':content}
        return {'id':'chatcmpl-'+identifier,'choices':[{'delta':delta,'finish_reason':reason}]}

    def test_empty_role_and_heartbeat_excluded_whitespace_is_predeclared_text(self):
        r,stopped=self.stream([self.event(),self.event(''),self.event(' '),self.event('hello'),self.event('', 'length'),'[DONE]'])
        self.assertEqual(r['status'],'completed');self.assertEqual(len(r['chunk_arrivals']),2)
        self.assertEqual(r['ttft_ms'],r['chunk_arrivals'][0]['at_ms'])
        self.assertEqual(r['stream_text_sha256'],collector.digest(' hello'))
        self.assertEqual(stopped,[])
        self.assertLessEqual(r['ttft_ms'],r['duration_ms'])
        self.assertGreater(r['end_monotonic_ns'],r['start_monotonic_ns'])

    def test_admin_lookup_after_stream_is_not_part_of_clock_discontinuity(self):
        r,_=self.stream([self.event(' hello'),self.event('', 'length'),'[DONE]'],administrative_clock_shift=True)
        self.assertEqual(r['status'],'completed')
        self.assertLess(r['clock_discontinuity_ms'],1000)

    def test_policy_and_block_width_are_sent_explicitly(self):
        self.stream([self.event(' hello'),self.event('', 'length'),'[DONE]'],policy='adaptive',draft_k=8)
        self.assertEqual(self.requests[0]['nodelift_draft_policy'],'adaptive')
        self.assertEqual(self.requests[0]['nodelift_draft_k'],8)

    def test_missing_done_is_failed_and_only_owned_run_stopped(self):
        r,stopped=self.stream([self.event('hello')])
        self.assertEqual(r['status'],'failed');self.assertEqual(stopped,[{'run_id':'id'}])

    def test_changed_run_id_cannot_mix_streams(self):
        r,stopped=self.stream([self.event('hi'),self.event('there',identifier='different'),'[DONE]'])
        self.assertEqual(r['status'],'failed');self.assertEqual(stopped,[{'run_id':'id'}])

    def test_error_or_empty_stream_is_not_success(self):
        for events in ([self.event(),{'error':{'message':'private server error'}},'[DONE]'],[self.event(),'[DONE]']):
            r,_=self.stream(events);self.assertEqual(r['status'],'failed')
            self.assertNotIn('private server error',json.dumps(r))


if __name__=='__main__':unittest.main()
