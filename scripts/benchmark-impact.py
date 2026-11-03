#!/usr/bin/env python3
"""Explicit local SSE benchmark collector and offline analysis. No cloud requests."""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import platform
import random
import re
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'host'))
from nodelift.impact import VERSION, analyze, digest

PROMPTS = ('Explain why the sky appears blue in two short sentences.',
           'Write a Python function that returns the larger of two integers.',
           'List three practical ways to reduce household electricity use.')


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name+'.tmp')
    with open(tmp, 'w', opener=lambda p, f: os.open(p, f, 0o600)) as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


class Client:
    def __init__(self, state):
        matches = re.findall(r'http://127\.0\.0\.1:(\d{1,5})/#([A-Za-z0-9_-]{32,})', (state/'host-session.log').read_text())
        if not matches:
            raise ValueError('No active local dashboard session; reopen NodeLift.')
        port, self.admin_token = matches[-1]
        self.port = int(port)
        self.client_token = self.admin('client-access')['api_key']

    def admin(self, path, body=None):
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        try:
            c.request('GET' if body is None else 'POST', '/admin/'+path,
                      None if body is None else json.dumps(body),
                      {'Authorization': 'Bearer '+self.admin_token, 'Content-Type': 'application/json'})
            r = c.getresponse()
            raw = r.read(2*1024*1024)
            if r.status != 200:
                raise ValueError('Local admin request failed: '+str(r.status))
            return json.loads(raw)
        finally:
            c.close()

    def capture(self, prompt, mode, node, budget, timeout_ms, policy="fixed", draft_k=4, pipeline="serial", verification_mode="serial"):
        body = {'model': 'nodelift', 'messages': [{'role': 'user', 'content': prompt}],
                'stream': True, 'temperature': 0, 'max_tokens': budget,
                'nodelift_mode': mode, 'nodelift_draft_k': draft_k,
                'nodelift_draft_policy': policy, 'nodelift_remote_timeout_ms': timeout_ms,
                'nodelift_pipeline':pipeline,'nodelift_verification_mode':verification_mode}
        if mode == 'remote_draft':
            body['nodelift_node_id'] = node
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=30)
        started = time.perf_counter_ns()
        wall_started = time.time_ns()
        run_id, first, done, error, finish = None, None, False, None, None
        arrivals, text = [], []
        try:
            c.request('POST', '/v1/chat/completions', json.dumps(body),
                      {'Authorization': 'Bearer '+self.client_token, 'Content-Type': 'application/json'})
            r = c.getresponse()
            if r.status != 200:
                raise ValueError('SSE HTTP '+str(r.status))
            if not (r.getheader('Content-Type') or '').startswith('text/event-stream'):
                raise ValueError('SSE content type required')
            for raw in r:
                elapsed = (time.perf_counter_ns()-started)/1e6
                if elapsed > 300000:
                    raise TimeoutError('client deadline')
                if len(raw) > 1024*1024:
                    raise ValueError('SSE line too large')
                if not raw.startswith(b'data:'):
                    continue
                line = raw[5:].strip()
                if line == b'[DONE]':
                    done = True
                    break
                event = json.loads(line)
                if 'error' in event:
                    raise ValueError('server generation error')
                identifier = event.get('id', '')
                if identifier.startswith('chatcmpl-'):
                    current = identifier.removeprefix('chatcmpl-')
                    if run_id and current != run_id:
                        raise ValueError('SSE run changed')
                    run_id = current
                for choice in event.get('choices', []):
                    content = choice.get('delta', {}).get('content', '')
                    if content:
                        if first is None:
                            first = elapsed
                        text.append(content)
                        arrivals.append({'at_ms': elapsed, 'characters': len(content)})
                    if choice.get('finish_reason'):
                        finish = choice['finish_reason']
        except (ValueError, OSError, http.client.HTTPException) as exc:
            error = type(exc).__name__
        except KeyboardInterrupt:
            error = 'cancelled'
        finally:
            ended = time.perf_counter_ns()
            wall_ended = time.time_ns()
            c.close()
            if not done and run_id:
                try:
                    self.admin('engine/stop', {'run_id': run_id})
                except (ValueError, OSError):
                    pass
        final = None
        if run_id:
            for _ in range(20):
                status = self.admin('engine/status')
                final = next((x for x in status['runs'] if x['id'] == run_id), None)
                if final and final['status'] in ('completed', 'failed', 'cancelled'):
                    break
                time.sleep(.1)
        clock_drift_ms = abs((wall_ended-wall_started)-(ended-started))/1e6
        if clock_drift_ms > 1000:
            error = 'clock_discontinuity'
        good = bool(done and not error and first is not None and final and final['status'] == 'completed')
        if good and final.get('text') != ''.join(text):
            good, error = False, 'stream_output_mismatch'
        tokens = final.get('tokens', []) if final else []
        metrics = final.get('metrics', {}) if final else {}
        result = {'run_id': run_id, 'status': 'completed' if good else 'cancelled' if error == 'cancelled' else 'failed',
                  'error_code': error, 'start_monotonic_ns': started, 'end_monotonic_ns': ended, 'clock_discontinuity_ms': clock_drift_ms, 'duration_ms': (ended-started)/1e6, 'ttft_ms': first,
                  'tokens_sha256': digest(tokens) if tokens else None, 'token_count': len(tokens),
                  'finish_reason': finish, 'fallback': bool(metrics.get('fallbacks') or (final or {}).get('fallback_reason')),
                  'chunk_arrivals': arrivals, 'stream_text_sha256': digest(''.join(text)),
                  'metrics': metrics,
                  'blocks': [{k: b.get(k) for k in ('generated','accepted','proposed','draft_ms','block_ms','effective_mode','verification_batch_width','native_ms','effective_timeout_ms','decision','round_ms','ready_offset_ms','published_offset_ms','native_timing','local_draft_timing','remote_timing','uncommitted_proposals','verification_mode')} for b in (final or {}).get('blocks', [])],
                  'identity': (final or {}).get('identity', {}),
                  'remote_trace': (final or {}).get('remote_trace', []),
                  'lookahead_trace': (final or {}).get('lookahead_trace', []),
                  'lookahead_cleanup_incomplete': (final or {}).get('lookahead_cleanup_incomplete', False)}
        return result



def telemetry(node):
    """Out-of-band snapshots, not power measurements or continuous monitoring."""
    caps = (node or {}).get('capabilities', {})
    return {'host_load_average': list(os.getloadavg()) if hasattr(os, 'getloadavg') else None,
            'observed_at_unix': time.time(),
            'companion': {k: caps.get(k) for k in ('thermal', 'battery_percent', 'available_memory_bytes',
                         'process_memory_bytes', 'app_version', 'lifecycle', 'transport')},
            'capabilities_updated_at': (node or {}).get('capabilities_updated_at'),
            'evidence': 'OS load averages and self-reported companion snapshots; not measured energy'}


def collect(args):
    client = Client(args.state)
    status = client.admin('engine/status')
    if status.get('busy') or not status.get('available'):
        raise ValueError('Native engine must be available and idle.')
    config = status['config']
    target = file_hash(config['target_model'])
    draft = file_hash(config['draft_model']) if config.get('draft_model') else 'none'
    native = file_hash(args.native_library)
    before = client.admin('status')
    nodes = before['nodes']
    node = next((n for n in nodes if n['id'] == args.node), None)
    if args.candidate == 'remote_draft':
        if not node or not node['online'] or not node['capabilities'].get('engine_ready'):
            raise ValueError('Selected physical companion must be online with its draft engine ready.')
        if node['capabilities'].get('draft_sha256') != draft:
            raise ValueError('Companion draft hash does not match host configuration.')
    connection = digest({'label': args.connection, 'host': before.get('host', {}).get('ip_address'),
                         'peer': (node or {}).get('ip_address')})
    # Paths and LAN addresses are never exported. Hashes identify exact artifacts.
    config_public = {k: v for k, v in config.items() if k not in ('target_model', 'draft_model')}
    config_public.update(max_tokens=args.tokens, draft_k=args.draft_k, remote_timeout_ms=args.remote_timeout_ms,
                         draft_policy=args.policy, temperature=0)
    scope = {'target_sha256': target, 'draft_sha256': draft, 'native_sha256': native,
             'config_sha256': digest(config_public), 'host_id': digest(platform.node()),
             'node_id': digest(args.node) if args.node else 'host', 'connection': connection,
             'candidate': args.candidate, 'warmup_policy': 'one-unscored-pair; shared-residency-uncontrolled'}
    sid = uuid.uuid4().hex
    rng = random.Random(args.seed)
    orders = (['AB', 'BA']*((3*args.repetitions+1)//2))[:3*args.repetitions]
    rng.shuffle(orders)
    plan = [{'id': str(i), 'prompt_sha256': digest(PROMPTS[i%3]), 'order': orders[i], 'max_tokens': args.tokens}
            for i in range(3*args.repetitions)]
    session = {'id': sid, 'plan': plan, 'plan_sha256': digest(plan), 'scope_sha256': digest(scope),
               'attempts': [], 'configuration': config_public, 'seed': args.seed, 'warmup': [], 'started_at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    data = {'schema_version': 1, 'runner': VERSION, 'collector_sha256': file_hash(__file__), 'scope': scope,
            'evidence_kind': 'control' if args.candidate == 'host' else 'physical' if args.candidate == 'remote_draft' else 'local',
            'display': {'target_model': Path(config['target_model']).name, 'draft_model': Path(config['draft_model']).name if config.get('draft_model') else 'none', 'candidate_device': str((node or {}).get('capabilities', {}).get('model', 'local host')), 'connection_label': args.connection},
            'sessions': [session]}
    if args.output.exists():
        raise ValueError('Output already exists; use a fresh file to retain previous evidence.')
    atomic(args.output, data)  # Frozen plan exists before any inference.
    artifact_stats = {str(p): (Path(p).stat().st_size, Path(p).stat().st_mtime_ns, Path(p).stat().st_ino) for p in (config['target_model'], config['draft_model'], str(args.native_library)) if p}
    initial_epoch = (node or {}).get('session_started_at')

    def check_scope():
        for path, original in artifact_stats.items():
            st = Path(path).stat()
            if (st.st_size, st.st_mtime_ns, st.st_ino) != original:
                raise ValueError('Model or native artifact changed')
        s = client.admin('engine/status')
        if s.get('busy') or s['config'] != config:
            raise ValueError('Host busy or configuration drift')
        snap = client.admin('status')
        if snap.get('host', {}).get('ip_address') != before.get('host', {}).get('ip_address'):
            raise ValueError('Host connection changed')
        peer = next((n for n in snap['nodes'] if n['id'] == args.node), None)
        if args.candidate == 'remote_draft' and (not peer or not peer['online'] or
                not peer['capabilities'].get('engine_ready') or peer['capabilities'].get('draft_sha256') != draft or
                peer.get('session_started_at') != initial_epoch or peer.get('ip_address') != node.get('ip_address')):
            raise ValueError('Companion offline or connection epoch changed')
        if peer and peer.get('capabilities', {}).get('thermal') in ('severe','critical','emergency','shutdown'):
            raise ValueError('Companion thermal condition unsuitable for further load')
        if peer and isinstance(peer.get('capabilities', {}).get('battery_percent'), (int,float)) and peer['capabilities']['battery_percent'] < 20:
            raise ValueError('Companion battery below 20 percent')
        return peer

    for mode in ('host', args.candidate):
        check_scope()
        warm = client.capture(PROMPTS[0], mode, args.node, args.tokens, args.remote_timeout_ms, args.policy, args.draft_k)
        warm.pop('identity', None)
        session['warmup'].append(warm)
        atomic(args.output, data)
        if warm['status'] != 'completed':
            raise ValueError('Warmup failed; frozen plan retained with missing attempts.')
    for p in plan:
        for arm in ('host', 'candidate') if p['order'] == 'AB' else ('candidate', 'host'):
            try:
                peer_before = check_scope()
                before_telemetry = telemetry(peer_before)
                result = client.capture(PROMPTS[int(p['id'])%3], 'host' if arm == 'host' else args.candidate,
                                        args.node, args.tokens, args.remote_timeout_ms, args.policy, args.draft_k)
                identity = result.pop('identity')
                identity_ok = (identity.get('target_sha256') == target and
                               (identity.get('draft_sha256') or 'none') == (draft if arm == 'candidate' and args.candidate != 'host' else 'none') and identity.get('config') == config)
                if not identity_ok:
                    result['status'], result['error_code'] = 'invalid', 'run_identity_mismatch'
                try:
                    peer_after = check_scope()
                    result['telemetry_before'] = before_telemetry
                    result['telemetry_after'] = telemetry(peer_after)
                except ValueError:
                    result['status'], result['error_code'] = 'invalid', 'post_run_scope_drift'
            except (ValueError, OSError, KeyboardInterrupt) as exc:
                result = {'status': 'cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed',
                          'fallback': False, 'error_code': type(exc).__name__}
            result.update(pair_id=p['id'], arm=arm, scope_sha256=digest(scope),
                          prompt_sha256=p['prompt_sha256'], max_tokens=p['max_tokens'])
            session['attempts'].append(result)
            atomic(args.output, data)
            print('Recorded pair '+p['id']+' '+arm+': '+result['status'], flush=True)
            if result['status'] in ('cancelled', 'invalid'):
                raise ValueError('Collection stopped; partial evidence retained.')
    report = analyze(data)
    atomic(args.output.with_suffix('.report.json'), report)
    print('Report: '+report['verdict']+'. No qualified routing recommendation.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('analyze')
    a.add_argument('input', type=Path)
    a.add_argument('--output', type=Path, required=True)
    m = sub.add_parser('merge')
    m.add_argument('inputs', type=Path, nargs='+')
    m.add_argument('--output', type=Path, required=True)
    c = sub.add_parser('collect')
    c.add_argument('--state', type=Path, default=Path.home()/'.local/share/nodelift')
    c.add_argument('--native-library', type=Path, required=True)
    c.add_argument('--candidate', choices=('host', 'local_draft', 'remote_draft'), required=True)
    c.add_argument('--node')
    c.add_argument('--connection', required=True, help='stable topology label; only its hash is exported')
    c.add_argument('--repetitions', type=int, choices=range(1, 11), default=1)
    c.add_argument('--tokens', type=int, choices=range(1, 513), default=64)
    c.add_argument('--remote-timeout-ms', type=int, choices=range(500, 60001), default=10000)
    c.add_argument('--policy', choices=('fixed','adaptive'), default='fixed')
    c.add_argument('--draft-k', type=int, choices=range(1,17), default=4)
    c.add_argument('--seed', type=int, default=731921)
    c.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    try:
        if args.command == 'collect':
            collect(args)
        elif args.command == 'analyze':
            atomic(args.output, analyze(json.loads(args.input.read_text())))
        else:
            values = [json.loads(f.read_text()) for f in args.inputs]
            for v in values:
                analyze(v)
            first = values[0]
            if any(v['scope'] != first['scope'] or v['evidence_kind'] != first['evidence_kind'] for v in values):
                raise ValueError('Cannot merge different model/device/connection scopes or evidence kinds.')
            first['sessions'] = [s for v in values for s in v['sessions']]
            analyze(first)
            atomic(args.output, first)
    except (ValueError, OSError, KeyError) as exc:
        # Paths, tokens, server prompts and transport exception details stay private.
        print('Benchmark stopped: '+(str(exc) if isinstance(exc, ValueError) else type(exc).__name__), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
