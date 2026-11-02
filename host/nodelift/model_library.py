"""Explicit GGUF imports and verified, public Hugging Face downloads.

No model code is executed here. A valid header is only an import check: the
pinned native runtime still decides whether a model architecture can load.
"""
import copy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import struct
import threading
import time
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener


MAX_MODEL = 512 * 1024**3
CHUNK = 1024**2


def model_metadata(row):
    """Allowlisted Hub observations, never a model-quality or RAM-fit judgment."""
    identity = repo_id(row.get('id'))
    def text(value):
        return value[:240] if isinstance(value,str) and value.strip() else None
    def count(value):
        return value if type(value) is int and 0 <= value <= 2**53 else None
    def values(value):
        raw = [value] if isinstance(value,str) else value if isinstance(value,list) else []
        return [v[:240] for v in raw[:12] if isinstance(v,str) and v.strip()]
    def date(value):
        if not isinstance(value,str) or len(value)>40:return None
        try:
            parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
            return value if parsed.tzinfo else None
        except ValueError:return None
    card = row.get('cardData') if isinstance(row.get('cardData'),dict) else {}
    gguf = row.get('gguf') if isinstance(row.get('gguf'),dict) else {}
    tensors = row.get('safetensors') if isinstance(row.get('safetensors'),dict) else {}
    config = row.get('config') if isinstance(row.get('config'),dict) else {}
    return {'id':identity,'author':text(row.get('author')) or identity.split('/')[0],
            'model_card':'https://huggingface.co/'+identity,
            'last_modified':date(row.get('lastModified')),'created_at':date(row.get('createdAt')),
            'downloads':count(row.get('downloads')),'downloads_30d':count(row.get('downloads')),
            'likes':count(row.get('likes')),'task':text(row.get('pipeline_tag')) or text(card.get('pipeline_tag')),
            'license':text(card.get('license')),'languages':values(card.get('language')),
            'base_models':values(card.get('base_model')),
            'parameters':count(gguf.get('total')) or count(tensors.get('total')),
            'architecture':text(gguf.get('architecture')) or text(config.get('model_type')),
            'context_length':count(gguf.get('context_length')) or count(config.get('max_position_embeddings')),
            'gated':row.get('gated') in (True,'auto','manual') if 'gated' in row else None}


class HubRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        host = target.hostname or ''
        if target.scheme != 'https' or target.port not in (None, 443) or not any(
                host == domain or host.endswith('.' + domain) for domain in ('huggingface.co', 'hf.co')):
            raise ValueError('Hugging Face redirect outside supported hosts')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def hub_open(url):
    # Public downloads only; never attach an account credential to CDN redirects.
    return build_opener(HubRedirect()).open(Request(url, headers={'User-Agent': 'NodeLift/0.3'}), timeout=20)


def hub_json(url):
    try:
        with hub_open(url) as response:
            raw = response.read(8 * CHUNK + 1)
        if len(raw) > 8 * CHUNK: raise ValueError('Hugging Face response too large')
        return json.loads(raw)
    except (OSError, ValueError) as error:
        raise ValueError('Hugging Face request failed; check the public repository and connection') from error


def repo_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', value):
        raise ValueError('Use a Hugging Face owner/repository identifier')
    return value


def single_gguf(name):
    return isinstance(name, str) and name.lower().endswith('.gguf') and not re.search(r'-\d{5}-of-\d{5}\.gguf$', name, re.I)


def check_gguf(path):
    if not path.is_file() or not single_gguf(path.name):
        raise ValueError('Select one complete GGUF file; split models are not supported')
    with path.open('rb') as stream: header = stream.read(24)
    if len(header) != 24: raise ValueError('Invalid GGUF header')
    magic, version, tensors, metadata = struct.unpack('<4sIQQ', header)
    if magic != b'GGUF' or version not in (2, 3) or not 0 < tensors < 10**7 or not 0 < metadata < 10**7:
        raise ValueError('Invalid GGUF header')


class ModelLibrary:
    def __init__(self, folder):
        self.folder = folder / 'models'
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.registry_path = folder / 'model-library.json'
        self.lock = threading.RLock()
        self.records = {}
        self.transfer = None
        self.cancelled = threading.Event()
        self.warning = None
        if self.registry_path.exists():
            try: self.records = self._read_registry(self.registry_path)
            except (OSError, ValueError):
                self.warning = 'Model registry could not be read; import existing files to recover missing entries'
                try:
                    self.records = self._read_registry(self.registry_path.with_suffix('.bak'))
                    self.warning = 'Model registry recovered from its previous backup; the last import may need repeating'
                except (OSError, ValueError): pass
        # Reap only old owned crash leftovers, never a recent/live transfer or user file.
        for path in self.folder.glob('.nodelift-*.part'):
            try:
                if re.fullmatch(r'\.nodelift-[a-f0-9]{32}\.part', path.name) and time.time()-path.stat().st_mtime>86400:
                    path.unlink(missing_ok=True)
            except OSError: self.warning = 'A temporary model file could not be removed; check available disk space'

    def paths(self):
        with self.lock: return [Path(p) for p in self.records]

    def source(self, path):
        with self.lock: return dict(self.records.get(str(Path(path).resolve()), {}))

    @staticmethod
    def _read_registry(path):
        data=json.loads(path.read_text())
        if not isinstance(data,dict) or any(not isinstance(k,str) or not isinstance(v,dict) for k,v in data.items()):
            raise ValueError('Invalid model registry')
        return {str(Path(key).resolve()): value for key, value in data.items()}

    @staticmethod
    def _save_registry(path, records):
        temporary=path.with_suffix(path.suffix+'.tmp')
        with open(temporary,'w',opener=lambda p,f:os.open(p,f,0o600)) as stream:
            json.dump(records,stream);stream.flush();os.fsync(stream.fileno())
        temporary.replace(path)
        if os.name != 'nt':
            descriptor=os.open(path.parent,os.O_RDONLY)
            try:os.fsync(descriptor)
            finally:os.close(descriptor)

    def _register(self, path, source):
        path = Path(path).resolve()
        with self.lock:
            records = {**self.records, str(path): source}
            self._save_registry(self.registry_path.with_suffix('.bak'),self.records)
            self._save_registry(self.registry_path,records)
            self.records = records
        return {'path': str(path), 'source': source}

    def import_path(self, value):
        if not isinstance(value, str) or len(value) > 4096: raise ValueError('Model path required')
        path = Path(value).expanduser()
        if not path.is_absolute(): raise ValueError('Use an absolute model path')
        try:
            path = path.resolve(strict=True)
            check_gguf(path)
            return self._register(path, {'kind': 'local', 'bytes': path.stat().st_size})
        except OSError as error:
            raise ValueError('Model file is unavailable or unreadable') from error

    def search(self, query):
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 160: raise ValueError('Enter a model search')
        rows = hub_json('https://huggingface.co/api/models?' + urlencode({'search': query.strip(), 'filter': 'gguf', 'limit': 12, 'sort': 'downloads', 'direction': -1, 'expand':['author','createdAt','lastModified','downloads','likes','pipeline_tag','cardData','gguf','safetensors','gated','config']}, doseq=True))
        if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows): raise ValueError('Hugging Face returned invalid model metadata')
        models=[]
        for row in rows[:12]:
            try:models.append(model_metadata(row))
            except ValueError:continue
        return {'models':models}

    def inspect(self, repo, revision='main'):
        repo = repo_id(repo)
        if not isinstance(revision, str) or revision in ('.','..') or not re.fullmatch(r'[A-Za-z0-9_.-]{1,120}', revision): raise ValueError('Invalid model revision')
        data = hub_json('https://huggingface.co/api/models/' + repo + '/revision/' + quote(revision, safe='') + '?blobs=true')
        if not isinstance(data,dict) or not isinstance(data.get('siblings',[]),list) or not isinstance(data.get('cardData') or {},dict): raise ValueError('Hugging Face returned invalid model metadata')
        sha = data.get('sha', '')
        if not isinstance(sha,str) or not re.fullmatch(r'[a-f0-9]{40}', sha): raise ValueError('Hugging Face did not return an immutable revision')
        files = []
        for row in data.get('siblings', []):
            if not isinstance(row,dict) or not isinstance(row.get('lfs') or {},dict): raise ValueError('Hugging Face returned invalid model metadata')
            name = row.get('rfilename', '')
            if not single_gguf(name): continue
            digest = (row.get('lfs') or {}).get('sha256', '')
            size = row.get('size')
            if not isinstance(digest,str) or not re.fullmatch(r'[a-f0-9]{64}', digest) or type(size) is not int or not 24 <= size <= MAX_MODEL: continue
            files.append({'name': name, 'bytes': size, 'sha256': digest})
        return {'repo': repo, 'revision': sha, 'license': (data.get('cardData') or {}).get('license', 'See model card'),
                'model_card': 'https://huggingface.co/' + repo, 'gated': bool(data.get('gated')), 'files': files}

    def status(self):
        with self.lock:
            self._expire()
            return {'transfer': copy.deepcopy(self.transfer), 'warning': self.warning}

    def _expire(self):
        if self.transfer and self.transfer['kind'] == 'upload' and self.transfer['status'] == 'transferring' and time.monotonic() - self.transfer['touched'] > 900:
            self._discard_part()
            self.transfer['status'] = 'expired'

    def _part(self):
        return self.folder / ('.nodelift-' + self.transfer['id'] + '.part')

    def _begin(self, name, size, kind, source):
        if not single_gguf(name) or Path(name).name != name or len(name) > 180 or not re.fullmatch(r'[A-Za-z0-9_. -]+', name):
            raise ValueError('Use a single GGUF filename without folders or special characters')
        if type(size) is not int or not 24 <= size <= MAX_MODEL: raise ValueError('Invalid model size')
        with self.lock:
            self._expire()
            if self.transfer and self.transfer['status'] in ('transferring', 'verifying'): raise ValueError('Finish or cancel the current model transfer')
            if shutil.disk_usage(self.folder).free < size + 1024**3: raise ValueError('Insufficient disk space; keep at least 1 GiB free')
            self.transfer = {'id': secrets.token_hex(16), 'name': name, 'bytes': size, 'received': 0, 'kind': kind,
                             'status': 'transferring', 'source': source, 'touched': time.monotonic()}
            self.cancelled.clear()
            try:
                with open(self._part(),'xb',opener=lambda p,f:os.open(p,f,0o600)): pass
            except OSError as error:
                self._fail(self.transfer['id'],'Model transfer could not be started')
                raise ValueError('Model transfer could not be started') from error
            return copy.deepcopy(self.transfer)

    def upload_start(self, values):
        return self._begin(values.get('name'), values.get('bytes'), 'upload', {'kind': 'upload'})

    def _check(self, identity):
        self._expire()
        if not self.transfer or identity != self.transfer['id'] or self.transfer['status'] != 'transferring':
            raise ValueError('Unknown or inactive model transfer')

    def upload_chunk(self, identity, offset, data):
        with self.lock:
            self._check(identity)
            if self.transfer['kind'] != 'upload': raise ValueError('Not a browser upload')
            if type(offset) is not int or offset != self.transfer['received']: raise ValueError('Model upload offset mismatch')
            if not data or len(data) > CHUNK or offset + len(data) > self.transfer['bytes']: raise ValueError('Invalid model upload chunk')
            try:
                if self._part().stat().st_size != offset: raise OSError('partial write')
                with self._part().open('ab') as stream:
                    stream.write(data);stream.flush();os.fsync(stream.fileno())
                if self._part().stat().st_size != offset+len(data): raise OSError('partial write')
            except OSError as error:
                self._fail(identity,'Model upload failed.')
                raise ValueError('Model upload failed.') from error
            self.transfer['received'] += len(data)
            self.transfer['touched'] = time.monotonic()
            return {'received': self.transfer['received']}

    def finish(self, identity):
        with self.lock:
            self._check(identity)
            if self.transfer['kind'] != 'upload': raise ValueError('Not a browser upload')
            if self.transfer['received'] != self.transfer['bytes']: raise ValueError('Model transfer is incomplete')
            self.transfer['status'] = 'verifying'
        self._launch(self._finalize,identity)
        return {'verifying': True}

    def cancel(self, identity):
        with self.lock:
            if not self.transfer or self.transfer['id'] != identity: raise ValueError('Unknown model transfer')
            if self.transfer['status'] not in ('transferring', 'verifying'): return {'cancelled': False}
            self.cancelled.set()
            if self.transfer['kind'] == 'upload' and self.transfer['status'] == 'transferring':
                self._discard_part()
                self.transfer['status'] = 'cancelled'
            return {'cancelled': True}

    def download(self, values):
        # Re-read pinned metadata; do not trust sizes, digests or URLs from the browser.
        revision = values.get('revision', '')
        if not isinstance(revision, str) or not re.fullmatch(r'[a-f0-9]{40}', revision): raise ValueError('Inspect the model before downloading')
        info = self.inspect(values.get('repo'), revision)
        if info['gated']: raise ValueError('Gated models require a manual download after accepting their terms')
        row = next((r for r in info['files'] if r['name'] == values.get('file')), None)
        if row is None: raise ValueError('Choose a complete GGUF with published SHA-256 and size')
        source = {'kind': 'huggingface', 'repo': info['repo'], 'revision': revision, 'file': row['name'], 'sha256': row['sha256']}
        transfer = self._begin(Path(row['name']).name, row['bytes'], 'huggingface', source)
        url = 'https://huggingface.co/' + info['repo'] + '/resolve/' + revision + '/' + quote(row['name'], safe='/')
        self._launch(self._download,transfer['id'],url)
        return transfer

    def _launch(self, target, identity, *args):
        try:threading.Thread(target=target,args=(identity,*args),daemon=True).start()
        except Exception as error:
            self._fail(identity,'Model transfer worker could not be started')
            raise ValueError('Model transfer worker could not be started') from error

    def _discard_part(self):
        try:
            self._part().unlink(missing_ok=True)
            self.transfer.pop('cleanup_pending',None)
        except OSError:self.transfer['cleanup_pending']=True

    def _download(self, identity, url):
        try:
            with hub_open(url) as response, self._part().open('ab') as stream:
                if response.status != 200: raise ValueError('Unexpected download response')
                while True:
                    if self.cancelled.is_set(): raise ValueError('Model transfer cancelled')
                    data = response.read1(CHUNK)
                    if not data: break
                    with self.lock:
                        if self.transfer['received'] + len(data) > self.transfer['bytes']: raise ValueError('Model download exceeds published size')
                        stream.write(data)
                        self.transfer['received'] += len(data)
                if self.transfer['received'] != self.transfer['bytes']: raise ValueError('Model download is incomplete')
            with self.lock: self.transfer['status'] = 'verifying'
            self._finalize(identity)
        except Exception:
            self._fail(identity, 'Hugging Face download failed; retry the transfer')

    def _fail(self, identity, message):
        with self.lock:
            if not self.transfer or self.transfer['id'] != identity: return
            self._discard_part()
            self.transfer['status'] = 'cancelled' if self.cancelled.is_set() else 'failed'
            if self.cancelled.is_set():
                self.transfer.pop('error', None)
            else:
                self.transfer['error'] = message

    def _finalize(self, identity):
        try:
            part = self._part()
            if part.stat().st_size != self.transfer['bytes']: raise ValueError('Model transfer is incomplete')
            digest = hashlib.sha256()
            with part.open('rb') as stream:
                while data := stream.read(CHUNK):
                    if self.cancelled.is_set(): raise ValueError('Model transfer cancelled')
                    digest.update(data)
            with self.lock:
                if self.cancelled.is_set(): raise ValueError('Model transfer cancelled')
                source = {**self.transfer['source'], 'name': self.transfer['name'], 'sha256': digest.hexdigest(), 'bytes': self.transfer['bytes']}
                expected = self.transfer['source'].get('sha256')
                if expected and expected != source['sha256']: raise ValueError('Model SHA-256 mismatch')
                # Validate before publishing a .gguf name into the native catalog.
                with part.open('rb') as stream: header = stream.read(24)
                if len(header) != 24: raise ValueError('Invalid GGUF header')
                magic, version, tensors, metadata = struct.unpack('<4sIQQ', header)
                if magic != b'GGUF' or version not in (2, 3) or not 0 < tensors < 10**7 or not 0 < metadata < 10**7: raise ValueError('Invalid GGUF header')
                destination = self.folder / (identity + '-' + self.transfer['name'])
                part.replace(destination)
                try: self._register(destination, source)
                except Exception:
                    destination.unlink(missing_ok=True)
                    raise
                self.transfer.update(status='completed', path=str(destination), sha256=source['sha256'])
        except Exception as error:
            self._fail(identity, str(error) if isinstance(error, ValueError) else 'Model verification failed')
