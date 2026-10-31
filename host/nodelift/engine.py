"""Experimental greedy inference controller and leased outbound mobile drafting."""
import copy
import codecs
import hashlib
import json
import secrets
import threading
import time
from pathlib import Path

from .native import Native, ROOT, library_path


def prefix_digest(tokens):
    return hashlib.sha256(json.dumps(tokens, separators=(',', ':')).encode()).hexdigest()


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('integer outside supported limits')
    return value


class Mailbox:
    def __init__(self):
        self.condition = threading.Condition()
        self.pending = {}

    def request(self, node, payload, cancel, timeout=30):
        message = {**payload, 'id': secrets.token_hex(16)}
        entry = {'message': message, 'expires': time.monotonic()+timeout, 'delivered': False, 'result': None}
        with self.condition:
            if node in self.pending: raise RuntimeError('node already has an inference lease')
            self.pending[node] = entry
            self.condition.notify_all()
            try:
                while entry['result'] is None:
                    if cancel.is_set(): raise RuntimeError('cancelled')
                    remaining = entry['expires']-time.monotonic()
                    if remaining <= 0: raise TimeoutError('remote draft deadline exceeded')
                    self.condition.wait(min(remaining, .2))
                return entry['result']
            finally:
                if self.pending.get(node) is entry: del self.pending[node]
                self.condition.notify_all()

    def poll(self, node, timeout=5):
        deadline = time.monotonic()+timeout
        with self.condition:
            while True:
                entry = self.pending.get(node)
                if entry and not entry['delivered'] and entry['expires'] > time.monotonic():
                    entry['delivered'] = True
                    return {'work': entry['message']}
                remaining = deadline-time.monotonic()
                if remaining <= 0: return {'work': None}
                self.condition.wait(remaining)

    def submit(self, node, result):
        with self.condition:
            entry = self.pending.get(node)
            if not entry or not entry['delivered'] or entry['expires'] <= time.monotonic() or entry['result'] is not None:
                raise ValueError('unknown, expired or replayed inference lease')
            expected = entry['message']
            for field in ('id', 'epoch', 'prefix_hash', 'tokenizer_fingerprint', 'model_sha256'):
                if result.get(field) != expected[field]: raise ValueError('stale or mismatched draft identity')
            ids = result.get('tokens', [])
            if not isinstance(ids, list) or len(ids) > expected['count'] or any(type(i) is not int or i<0 or i>=expected['vocab_size'] for i in ids):
                raise ValueError('invalid draft token IDs')
            if not ids and not result.get('error'): raise ValueError('empty successful draft')
            entry['result'] = {'tokens':ids, 'error':str(result.get('error',''))[:300]}
            self.condition.notify_all()
            return {'accepted':True}


class Controller:
    def __init__(self, state):
        self.state = state
        self.lock = threading.RLock()
        self.mailbox = Mailbox()
        self.cancelled = threading.Event()
        self.busy = False
        self.runs = []
        self.config = {'target_model':'', 'draft_model':'', 'n_ctx':2048, 'threads':8, 'gpu_layers':999}
        self.target = None
        self.draft = None
        self.loaded = None
        self.target_info = None
        self.draft_info = None
        self.hashes = {}
        self.catalog = []
        self.catalog_deadline = 0
        saved=self.state.folder/'engine-config.json'
        if saved.exists():
            try:self.configure(json.loads(saved.read_text()))
            except (ValueError,OSError,json.JSONDecodeError):pass

    def models(self, refresh=False):
        if not refresh and time.monotonic()<self.catalog_deadline:return self.catalog
        roots = [ROOT/'.models', Path.home()/'.lmstudio/models']
        catalog=[]
        for root in roots:
            try:
                for p in sorted(root.rglob('*.gguf')):
                    try: size=p.stat().st_size
                    except OSError:continue
                    catalog.append({'id':hashlib.sha256(str(p).encode()).hexdigest()[:16], 'path':str(p), 'name':p.stem, 'bytes':size})
                    if len(catalog)>=100:break
            except OSError:continue
            if len(catalog)>=100:break
        self.catalog=catalog;self.catalog_deadline=time.monotonic()+5
        return catalog

    def status(self):
        with self.lock:
            return {'available':library_path().exists(), 'busy':self.busy, 'models':self.models(),
                    'config':dict(self.config), 'runs':copy.deepcopy(self.runs[-30:][::-1]),
                    'backend':'llama.cpp locked native core · greedy experiment',
                    'sampler':'greedy', 'capacity_sharding':False}

    def configure(self, values):
        with self.lock:
            if self.busy: raise ValueError('stop the current run before changing models')
            candidates={m['path'] for m in self.models(refresh=True)}
            config={**self.config,**{k:v for k,v in values.items() if k in self.config}}
            for key in ('target_model','draft_model'):
                if config[key] and config[key] not in candidates: raise ValueError('choose a GGUF from the local catalog')
            integer(config['n_ctx'],256,8192);integer(config['threads'],1,16);integer(config['gpu_layers'],0,999)
            if not config['target_model']: raise ValueError('select a target model')
            self.config=config
            path=self.state.folder/'engine-config.json'
            temporary=path.with_suffix('.tmp')
            temporary.write_text(json.dumps(config));temporary.chmod(0o600);temporary.replace(path)
            return {'configured':True, 'config':config}

    def _sha(self, path):
        stat=Path(path).stat();key=(path,stat.st_size,stat.st_mtime_ns)
        if key not in self.hashes:
            with open(path,'rb') as stream:self.hashes[key]=hashlib.file_digest(stream,'sha256').hexdigest()
        return self.hashes[key]

    def model_offer(self):
        with self.lock:
            path=self.config['draft_model']
            if not path: raise ValueError('no draft selected on the host')
            return {'name':Path(path).name,'bytes':Path(path).stat().st_size,'sha256':self._sha(path),
                    'url_path':'/v1/engine/model','max_context':min(self.config['n_ctx'],4096)}

    def model_path(self):
        with self.lock:
            path=self.config['draft_model']
            if not path:raise ValueError('no draft selected')
            return Path(path)

    def start(self, values):
        prompt=values.get('prompt','')
        messages=values.get('messages')
        if messages is not None:
            if not isinstance(messages,list) or not 1<=len(messages)<=32:raise ValueError('messages must have 1..32 entries')
            for m in messages:
                if not isinstance(m,dict) or m.get('role') not in ('system','user','assistant') or not isinstance(m.get('content'),str):raise ValueError('only text system/user/assistant messages are supported')
            prompt='\n'.join(m['role']+': '+m['content'] for m in messages)
        if not isinstance(prompt,str) or not prompt.strip() or len(prompt.encode())>32768:raise ValueError('prompt required, maximum 32 KiB')
        mode=values.get('mode','host')
        if mode not in ('host','local_draft','remote_draft'):raise ValueError('unsupported inference mode')
        budget=integer(values.get('max_tokens',64),1,512);k=integer(values.get('draft_k',4),1,16)
        remote_timeout_ms=integer(values.get('remote_timeout_ms',30000),500,60000)
        with self.lock:
            if self.busy:raise ValueError('engine is busy')
            if not self.config['target_model']:raise ValueError('configure a target model first')
            if mode!='host' and not self.config['draft_model']:raise ValueError('configure a draft model first')
            node_id=values.get('node_id')
            if mode=='remote_draft':
                peer=next((n for n in self.state.snapshot()['nodes'] if n['id']==node_id),None)
                if not peer or not peer['online'] or not peer['capabilities'].get('engine_ready'):raise ValueError('select an online native draft node')
            run={'id':secrets.token_hex(12),'epoch':secrets.token_hex(16),'created':time.time(),'status':'loading',
                 'mode':mode,'prompt':prompt,'max_tokens':budget,'draft_k':k,'node_id':node_id,
                 'remote_timeout_ms':remote_timeout_ms,'text':'','metrics':{},'blocks':[]}
            if messages is not None:run['messages']=messages
            self.busy=True;self.cancelled.clear();self.runs.append(copy.deepcopy(run))
            if len(self.runs)>30:self.runs.pop(0)
            threading.Thread(target=self._execute,args=(run,dict(self.config)),daemon=True).start()
            return {'run_id':run['id']}

    def stop(self, run_id=None):
        with self.lock:
            if run_id is not None and (not self.runs or self.runs[-1]['id']!=run_id):return {'stopping':False}
            if not self.busy:return {'stopping':False}
            self.cancelled.set()
            for engine in (self.target,self.draft):
                if engine:engine.cancel()
        with self.mailbox.condition:self.mailbox.condition.notify_all()
        return {'stopping':self.busy}

    def _load(self, config, use_draft):
        identity={**config,'target_sha256':self._sha(config['target_model']),
                  'draft_sha256':self._sha(config['draft_model']) if config['draft_model'] else None}
        if self.loaded!=identity:
            for engine in (self.target,self.draft):
                if engine:engine.close()
            self.target=Native();self.draft=None;self.loaded=None
            self.target_info=self.target.call('load',path=config['target_model'],n_ctx=config['n_ctx'],threads=config['threads'],gpu_layers=config['gpu_layers'])
            self.loaded=identity
        if use_draft and self.draft is None:
            self.draft=Native()
            try:self.draft_info=self.draft.call('load',path=config['draft_model'],n_ctx=config['n_ctx'],threads=config['threads'],gpu_layers=config['gpu_layers'])
            except Exception:self.draft.close();self.draft=None;raise
        if use_draft and self.draft_info['tokenizer_fingerprint']!=self.target_info['tokenizer_fingerprint']:
            raise ValueError('target/draft token-ID semantics do not match')

    def _publish(self, run):
        # The worker owns its mutable record; readers see atomic snapshots.
        with self.lock:
            for i, current in enumerate(self.runs):
                if current['id']==run['id']:
                    self.runs[i]=copy.deepcopy(run)
                    return

    def _execute(self, run, config):
        submitted=time.perf_counter();generated=[];accepted=proposed=0;fallbacks=0;remote_wait_ms=0
        decoder=codecs.getincrementaldecoder('utf-8')('replace')
        try:
            self._load(config,run['mode']=='local_draft')
            if self.cancelled.is_set():raise RuntimeError('cancelled')
            ready=time.perf_counter();run['metrics']['load_ms']=(ready-submitted)*1000
            self.target.call('reset')
            prefix=self.target.call('tokenize',text=run['prompt'],chat=True,messages=run.get('messages'))['tokens']
            run['prompt_tokens']=len(prefix)
            if len(prefix)+run['max_tokens']+run['draft_k']+1>=config['n_ctx']:raise ValueError('prompt and output exceed context budget')
            fingerprint=self.target_info['tokenizer_fingerprint']
            draft_sha=self._sha(config['draft_model']) if run['mode']!='host' else None
            run['identity']={'target_sha256':self._sha(config['target_model']),'draft_sha256':draft_sha,
                             'tokenizer_fingerprint':fingerprint,'config':config,'llama_commit':(ROOT/'native/llama.lock').read_text().strip()}
            started=time.perf_counter();run['status']='running';self._publish(run)
            self.target.call('prefill',prefix=prefix)
            if run['mode']=='local_draft':self.draft.call('reset');self.draft.call('prefill',prefix=prefix)
            decoding=time.perf_counter();mode=run['mode']
            while len(generated)<run['max_tokens']:
                if self.cancelled.is_set():raise RuntimeError('cancelled')
                block_start=time.perf_counter();count=min(run['draft_k'],run['max_tokens']-len(generated));draft_ms=0
                verification_batch_width=0
                if mode=='host':
                    result=self.target.call('draft',prefix=prefix,count=1);result.update(accepted=0,proposed=0)
                else:
                    dstart=time.perf_counter()
                    if mode=='local_draft':proposal=self.draft.call('draft',prefix=prefix,count=count)['tokens']
                    else:
                        try:
                            payload={'op':'draft','epoch':run['epoch'],'prefix':prefix,'prefix_hash':prefix_digest(prefix),
                                     'count':count,'tokenizer_fingerprint':fingerprint,'model_sha256':draft_sha,
                                     'vocab_size':self.target_info['vocab_size']}
                            response=self.mailbox.request(run['node_id'],payload,self.cancelled,timeout=run['remote_timeout_ms']/1000)
                            if response.get('error'):raise RuntimeError(response['error'])
                            proposal=response['tokens']
                        except Exception as error:
                            if self.cancelled.is_set():raise
                            fallbacks+=1;mode='host';proposal=[];run['fallback_reason']=str(error)[:300]
                    draft_ms=(time.perf_counter()-dstart)*1000
                    if run['mode']=='remote_draft':remote_wait_ms+=draft_ms
                    verification_batch_width=len(proposal)+1
                    result=self.target.call('verify',prefix=prefix,proposal=proposal,remaining=run['max_tokens']-len(generated))
                ids=result['tokens'];require_ids=bool(ids)
                if not require_ids:raise RuntimeError('engine produced no progress')
                generated.extend(ids);prefix.extend(ids);accepted+=result.get('accepted',0);proposed+=result.get('proposed',0)
                decoded=self.target.call('text',tokens=ids)
                run['text']+=decoder.decode(bytes.fromhex(decoded['bytes_hex']),final=False)
                now=time.perf_counter()
                if 'ttft_ms' not in run['metrics']:run['metrics']['ttft_ms']=(now-started)*1000
                run['blocks'].append({'generated':len(ids),'accepted':result.get('accepted',0),'proposed':result.get('proposed',0),
                                      'draft_ms':draft_ms,'block_ms':(now-block_start)*1000,'effective_mode':mode,
                                      'verification_batch_width':verification_batch_width})
                run['metrics'].update(generated_tokens=len(generated),accepted_tokens=accepted,proposed_tokens=proposed,
                                      elapsed_seconds=now-started,tokens_per_second=len(generated)/max(now-decoding,1e-9),
                                      fallbacks=fallbacks,remote_wait_ms=remote_wait_ms)
                self._publish(run)
                if result.get('eos'):break
            run['text']+=decoder.decode(b'',final=True)
            run['finish_reason']='stop' if result.get('eos') else 'length'
            run['tokens']=generated;run['status']='completed';run['metrics']['request_total_ms']=(time.perf_counter()-submitted)*1000
        except Exception as error:
            run['status']='cancelled' if self.cancelled.is_set() else 'failed';run['error']=str(error)[:500];run['tokens']=generated
        finally:
            run['finished']=time.time()
            run['metrics']['request_total_ms']=(time.perf_counter()-submitted)*1000
            self._publish(run)
            # Prompt-bearing experiment results stay in the private host state.
            try:
                folder=self.state.folder/'inference';folder.mkdir(mode=0o700,exist_ok=True)
                path=folder/(run['id']+'.json');path.write_text(json.dumps(run,indent=2));path.chmod(0o600)
            finally:
                with self.lock:self.busy=False
