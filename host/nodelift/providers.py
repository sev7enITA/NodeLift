"""Opt-in OpenAI text bridges. Credentials live only in this process.

No retries, redirects, provider fallback, or automatic cloud selection.
"""
import http.client
import json
import re
import socket
import threading
import time
from urllib.parse import urlsplit


class Providers:
    def __init__(self):
        self.lock = threading.RLock()
        self.keys = {'openrouter': '', 'local_api': ''}
        self.local_port = 8000
        self.catalogs = {'openrouter': [], 'local_api': []}
        self.active = None
        self.active_socket = None

    def status(self):
        with self.lock:
            return {'openrouter_key_set': bool(self.keys['openrouter']),
                    'local_key_set': bool(self.keys['local_api']),
                    'local_url': f'http://127.0.0.1:{self.local_port}/v1',
                    'models': {k: list(v) for k, v in self.catalogs.items()}}

    def configure(self, values):
        backend = values.get('backend')
        if not isinstance(backend, str) or backend not in self.keys: raise ValueError('Unknown external backend')
        with self.lock:
            if self.active is not None: raise ValueError('Stop the provider run before changing access')
            port = self.local_port
            if backend == 'local_api' and 'base_url' in values:
                if not isinstance(values['base_url'], str): raise ValueError('Use a loopback HTTP endpoint ending in /v1')
                url = urlsplit(values['base_url'])
                if url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost') or url.username or url.password or url.path.rstrip('/') != '/v1' or url.query or url.fragment:
                    raise ValueError('Use a loopback HTTP endpoint ending in /v1')
                port = url.port or 80
                if not 1 <= port <= 65535 or port in (9867, 9868): raise ValueError('Choose a separate local model server port')
            key = values.get('api_key', self.keys[backend])
            if not isinstance(key, str) or len(key) > 512 or any(ord(c) < 33 or ord(c) > 126 for c in key):
                raise ValueError('Invalid provider API key')
            if port != self.local_port: self.catalogs['local_api'] = []
            self.local_port = port
            self.keys[backend] = key
            return self.status()

    def _connection(self, backend):
        if backend == 'openrouter': return http.client.HTTPSConnection('openrouter.ai', timeout=20), '/api/v1'
        if backend == 'local_api': return http.client.HTTPConnection('127.0.0.1', self.local_port, timeout=20), '/v1'
        raise ValueError('Unknown external backend')

    def _headers(self, backend):
        headers = {'Content-Type': 'application/json', 'User-Agent': 'NodeLift/0.3'}
        if self.keys[backend]: headers['Authorization'] = 'Bearer ' + self.keys[backend]
        return headers

    def models(self, backend):
        with self.lock:
            connection, prefix = self._connection(backend)
            headers = self._headers(backend)
            port = self.local_port
        try:
            # The public OpenRouter model list needs no key.
            if backend == 'openrouter': headers.pop('Authorization', None)
            connection.request('GET', prefix + '/models', headers=headers)
            response = connection.getresponse()
            if response.status != 200: raise ValueError('Model catalog request failed (HTTP %d)' % response.status)
            raw = response.read(8 * 1024**2 + 1)
            if len(raw) > 8 * 1024**2: raise ValueError('Provider catalog too large')
            document=json.loads(raw)
            if not isinstance(document,dict) or not isinstance(document.get('data'),list): raise ValueError('Invalid provider model catalog')
            rows=document['data']
            models = []
            for row in rows[:5000]:
                if not isinstance(row,dict) or not isinstance(row.get('architecture') or {},dict) or not isinstance(row.get('pricing') or {},dict): raise ValueError('Invalid provider model catalog')
                identity = row.get('id')
                if not valid_model(identity): continue
                outputs = (row.get('architecture') or {}).get('output_modalities', ['text'])
                if 'text' not in outputs: continue
                models.append({'id': identity, 'name': str(row.get('name') or identity)[:200],
                               'context_length': row.get('context_length'), 'pricing': row.get('pricing') or {}})
            with self.lock:
                if backend == 'local_api' and port != self.local_port: raise ValueError('Local endpoint changed; refresh its models')
                self.catalogs[backend] = models
            return {'models': models}
        except (OSError, ValueError, KeyError, TypeError, http.client.HTTPException) as error:
            raise ValueError('Provider catalog unavailable; check the endpoint and connection') from error
        finally: connection.close()

    def validate(self, backend, model):
        if not isinstance(backend, str) or backend not in self.keys or not valid_model(model): raise ValueError('Choose an external backend and model')
        with self.lock:
            if backend == 'openrouter' and not self.keys[backend]: raise ValueError('Add an OpenRouter key for this host session')
            if not any(m['id'] == model for m in self.catalogs[backend]): raise ValueError('Refresh the provider catalog and select a model')

    def cancel(self):
        with self.lock:
            connection = self.active
            transport = self.active_socket or (connection.sock if connection else None)
        if transport:
            try: transport.shutdown(socket.SHUT_RDWR)
            except OSError: pass

    def stream(self, backend, model, messages, max_tokens, cancelled):
        with self.lock:
            if self.active is not None: raise ValueError('Provider is already running')
            self.validate(backend, model)
            connection, prefix = self._connection(backend)
            headers = self._headers(backend)
            self.active = connection
        response = None
        payload = {'model': model, 'messages': messages, 'max_tokens': max_tokens, 'temperature': 0,
                   'stream': True, 'stream_options': {'include_usage': True}}
        if backend == 'openrouter': payload['provider'] = {'allow_fallbacks': False, 'data_collection': 'deny'}
        try:
            if cancelled.is_set(): raise ValueError('Provider run cancelled')
            connection.request('POST', prefix + '/chat/completions', json.dumps(payload).encode(), headers)
            with self.lock: self.active_socket = connection.sock
            transport = connection.sock
            if transport: transport.settimeout(60)
            if cancelled.is_set(): raise ValueError('Provider run cancelled')
            response = connection.getresponse()
            if response.status != 200: raise ValueError('Provider request failed (HTTP %d)' % response.status)
            if 'text/event-stream' not in response.getheader('Content-Type', ''): raise ValueError('Provider did not return a text stream')
            deadline = time.monotonic() + 300
            event = []; finished = False
            for raw_line in stream_lines(response, cancelled, deadline, transport):
                line = raw_line.decode('utf-8').rstrip('\r')
                if line.startswith('data:'): event.append(line[5:].lstrip())
                elif not line and event:
                    data = '\n'.join(event); event = []
                    if data == '[DONE]':
                        if not finished: raise ValueError('Provider omitted the completion reason')
                        return
                    value = json.loads(data)
                    if not isinstance(value,dict): raise ValueError('Invalid provider event')
                    if value.get('error'): raise ValueError('Provider reported a generation error')
                    delta = ''; reason = None
                    choices = value.get('choices') or []
                    if not isinstance(choices,list): raise ValueError('Invalid provider event')
                    if choices:
                        if len(choices) != 1: raise ValueError('Multiple provider choices are not supported')
                        choice = choices[0]
                        if not isinstance(choice,dict): raise ValueError('Invalid provider event')
                        if choice.get('index', 0) != 0: raise ValueError('Multiple provider choices are not supported')
                        change = choice.get('delta') or {}
                        if not isinstance(change,dict): raise ValueError('Invalid provider event')
                        if change.get('tool_calls') or change.get('function_call'): raise ValueError('Only provider text completions are supported')
                        delta = change.get('content') or ''
                        if not isinstance(delta, str): raise ValueError('Only provider text completions are supported')
                        if finished and delta: raise ValueError('Provider sent text after completion')
                        reason = choice.get('finish_reason')
                        if reason is not None:
                            if reason not in ('stop', 'length'): raise ValueError('Provider did not complete a text response')
                            finished = True
                    usage = value.get('usage')
                    if usage is not None:
                        if not isinstance(usage,dict): raise ValueError('Invalid provider event')
                        names = ('prompt_tokens', 'completion_tokens', 'total_tokens')
                        usage = {k: usage[k] for k in names} if all(type(usage.get(k)) is int and usage[k] >= 0 for k in names) else None
                    yield {'text': delta, 'finish_reason': reason, 'usage': usage}
            raise ValueError('Provider stream ended before completion')
        except (OSError, http.client.HTTPException, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError('Provider connection interrupted; no automatic retry was sent') from error
        finally:
            if response is not None: response.close()
            connection.close()
            with self.lock:
                if self.active is connection:
                    self.active = None
                    self.active_socket = None


def valid_model(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:@+-]{0,199}', value))


def stream_lines(response, cancelled, deadline, transport=None):
    """Bound partial lines as well as complete events; read1 avoids slow-line stalls."""
    pending=b''; total=0
    while True:
        if cancelled.is_set(): raise ValueError('Provider run cancelled')
        remaining=deadline-time.monotonic()
        if remaining<=0: raise ValueError('Provider run deadline exceeded')
        if transport: transport.settimeout(min(60, remaining))
        chunk=response.read1(65536)
        if not chunk:return
        total+=len(chunk)
        if total>8*1024**2:raise ValueError('Provider stream exceeds supported limits')
        pending+=chunk
        while b'\n' in pending:
            line,pending=pending.split(b'\n',1)
            if len(line)>65536:raise ValueError('Provider stream exceeds supported limits')
            yield line
        if len(pending)>65536:raise ValueError('Provider stream exceeds supported limits')
