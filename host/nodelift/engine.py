"""Experimental greedy inference controller and leased outbound mobile drafting."""
import copy
import codecs
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import secrets
import threading
import time
from pathlib import Path

from .native import Native, ROOT, library_path
from .scheduling import AdaptiveDraftGate, PromptLookup
from .model_library import ModelLibrary
from .providers import Providers
from .leases import Mailbox
from .lookahead import LocalLookahead


def prefix_digest(tokens):
    return hashlib.sha256(json.dumps(tokens, separators=(',', ':')).encode()).hexdigest()


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('integer outside supported limits')
    return value


class Controller:
    def __init__(self, state):
        self.state = state
        self.lock = threading.RLock()
        self.mailbox = Mailbox()
        self.cancelled = threading.Event()
        self.busy = False
        self.runs = []
        self.library = ModelLibrary(state.folder)
        self.providers = Providers()
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
        catalog=[]; paths=self.library.paths(); seen=set()
        for root in roots:
            try: paths.extend(sorted(root.rglob('*.gguf'))[:500])
            except OSError: continue
        for p in paths:
            try:
                p=p.resolve(); size=p.stat().st_size
                if not p.is_file() or str(p) in seen: continue
            except OSError: continue
            seen.add(str(p));source=self.library.source(p)
            name=Path(source.get('name') or source.get('file') or p.name).stem
            catalog.append({'id':hashlib.sha256(str(p).encode()).hexdigest()[:16], 'path':str(p), 'name':name, 'bytes':size, 'source':source.get('kind','local')})
            if len(catalog)>=500: break
        self.catalog=catalog;self.catalog_deadline=time.monotonic()+5
        return catalog

    def status(self):
        with self.lock:
            runs=copy.deepcopy(self.runs[-30:][::-1])
            for run in runs:
                if run.get('epoch'):run['remote_trace']=self.mailbox.trace(run['epoch'])
            return {'available':library_path().exists(), 'busy':self.busy, 'models':self.models(),
                    'config':dict(self.config), 'runs':runs,
                    'backend':'llama.cpp locked native core · greedy experiment',
                    'sampler':'greedy', 'capacity_sharding':False, 'library':self.library.status(), 'providers':self.providers.status()}

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
        if mode not in ('host','local_draft','remote_draft','lookup'):raise ValueError('unsupported inference mode')
        verification_mode=values.get('verification_mode','serial')
        if verification_mode not in ('serial','experimental_batch'):raise ValueError('unsupported verification mode')
        pipeline=values.get('pipeline','serial')
        if pipeline not in ('serial','bounded_v1'):raise ValueError('unsupported pipeline')
        if pipeline!='serial' and mode not in ('local_draft','remote_draft'):raise ValueError('lookahead requires a draft mode')
        draft_policy=values.get('draft_policy','fixed')
        if draft_policy not in ('fixed','adaptive'):raise ValueError('unsupported draft policy')
        if pipeline!='serial' and draft_policy!='fixed':raise ValueError('bounded lookahead requires fixed policy')
        budget=integer(values.get('max_tokens',64),1,512);k=integer(values.get('draft_k',4),1,16)
        remote_timeout_ms=integer(values.get('remote_timeout_ms',30000),500,60000)
        backend=values.get('backend','native')
        if backend not in ('native','openrouter','local_api'):raise ValueError('Unsupported inference backend')
        if backend!='native':
            if mode!='host':raise ValueError('External backends do not support NodeLift drafting modes')
            self.providers.validate(backend,values.get('provider_model'))
        with self.lock:
            if self.busy:raise ValueError('engine is busy')
            if backend=='native' and not self.config['target_model']:raise ValueError('configure a target model first')
            if mode in ('local_draft','remote_draft') and not self.config['draft_model']:raise ValueError('configure a draft model first')
            node_id=values.get('node_id')
            if mode=='remote_draft':
                peer=next((n for n in self.state.snapshot()['nodes'] if n['id']==node_id),None)
                if not peer or not peer['online'] or not peer['capabilities'].get('engine_ready'):raise ValueError('select an online native draft node')
                if pipeline!='serial' and not peer['capabilities'].get('bounded_lookahead'):raise ValueError('companion does not support bounded lookahead')
            run={'id':secrets.token_hex(12),'epoch':secrets.token_hex(16),'created':time.time(),'status':'loading',
                 'backend':backend,'provider_model':values.get('provider_model') if backend!='native' else None,
                 'mode':mode,'prompt':prompt,'max_tokens':budget,'draft_k':k,'node_id':node_id,
                 'draft_policy':draft_policy,'verification_mode':verification_mode,'pipeline':pipeline,
                 'remote_timeout_ms':remote_timeout_ms,'text':'','metrics':{},'blocks':[]}
            if messages is not None:run['messages']=messages
            self.busy=True;self.cancelled.clear();self.runs.append(copy.deepcopy(run))
            if len(self.runs)>30:self.runs.pop(0)
            threading.Thread(target=self._execute if backend=='native' else self._execute_provider,args=(run,dict(self.config)),daemon=True).start()
            return {'run_id':run['id']}

    def stop(self, run_id=None):
        with self.lock:
            if run_id is not None and (not self.runs or self.runs[-1]['id']!=run_id):return {'stopping':False}
            if not self.busy:return {'stopping':False}
            self.cancelled.set()
            self.providers.cancel()
            for engine in (self.target,self.draft):
                if engine:engine.cancel()
        with self.mailbox.condition:self.mailbox.condition.notify_all()
        return {'stopping':self.busy}

    def configure_provider(self, values):
        with self.lock:
            if self.busy: raise ValueError('Stop the current run before changing provider access')
            return self.providers.configure(values)

    def _execute_provider(self, run, config):
        started=time.perf_counter(); first=None
        try:
            run['status']='running';self._publish(run)
            messages=run.get('messages') or [{'role':'user','content':run['prompt']}]
            with closing(self.providers.stream(run['backend'],run['provider_model'],messages,run['max_tokens'],self.cancelled)) as events:
                for event in events:
                    if self.cancelled.is_set():raise ValueError('Provider run cancelled')
                    if event['text'] and first is None:
                        first=time.perf_counter();run['metrics']['ttft_ms']=(first-started)*1000
                    if len((run['text']+event['text']).encode())>1024**2:raise ValueError('Provider text exceeds supported limits')
                    run['text']+=event['text']
                    if event['finish_reason']:run['finish_reason']=event['finish_reason']
                    if event['usage'] is not None:run['usage']=event['usage']
                    run['metrics']['elapsed_seconds']=time.perf_counter()-started
                    self._publish(run)
            if self.cancelled.is_set():raise ValueError('Provider run cancelled')
            run['status']='completed'
        except Exception as error:
            run['status']='cancelled' if self.cancelled.is_set() else 'failed'
            # Provider bodies and credentials never enter run records or exports.
            run['error']=str(error) if isinstance(error,ValueError) else 'Provider response could not be processed'
        finally:
            run['metrics']['request_total_ms']=(time.perf_counter()-started)*1000
            run['metrics']['elapsed_seconds']=time.perf_counter()-started
            run['measurement_scope']='cloud_provider' if run['backend']=='openrouter' else 'local_external_server'
            if run.get('usage'):run['metrics']['generated_tokens']=run['usage']['completion_tokens']
            self._publish(run)
            with self.lock:self.busy=False

    def _load(self, config, use_draft):
        identity={**config,'target_sha256':self._sha(config['target_model']),
                  'draft_sha256':self._sha(config['draft_model']) if config['draft_model'] else None}
        if self.loaded!=identity:
            with self.lock:
                if self.cancelled.is_set():raise RuntimeError('cancelled')
                for engine in (self.target,self.draft):
                    if engine:engine.close()
                self.target=Native();self.draft=None;self.loaded=None
            self.target_info=self.target.call('load',path=config['target_model'],n_ctx=config['n_ctx'],threads=config['threads'],gpu_layers=config['gpu_layers'])
            if self.cancelled.is_set():raise RuntimeError('cancelled')
            self.loaded=identity
        if use_draft and self.draft is None:
            with self.lock:
                if self.cancelled.is_set():raise RuntimeError('cancelled')
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
        run['metrics']['timing_schema_version']=3
        local_pipeline=None;remote_pool=None;first_remote=None;sequence=0
        pipeline=run.get('pipeline','serial')
        verification_mode=run.get('verification_mode','serial')
        gate=AdaptiveDraftGate() if run.get('draft_policy')=='adaptive' and run['mode']!='host' else None
        lookup=PromptLookup() if run['mode']=='lookup' else None
        decoder=codecs.getincrementaldecoder('utf-8')('replace')
        try:
            self._load(config,run['mode']=='local_draft' and not gate)
            if self.cancelled.is_set():raise RuntimeError('cancelled')
            ready=time.perf_counter();run['metrics']['load_ms']=(ready-submitted)*1000
            self.target.call('reset')
            prefix=self.target.call('tokenize',text=run['prompt'],chat=True,messages=run.get('messages'))['tokens']
            run['prompt_tokens']=len(prefix)
            if len(prefix)+run['max_tokens']+run['draft_k']+1>=config['n_ctx']:raise ValueError('prompt and output exceed context budget')
            fingerprint=self.target_info['tokenizer_fingerprint']
            draft_sha=self._sha(config['draft_model']) if run['mode'] in ('local_draft','remote_draft') else None
            run['identity']={'target_sha256':self._sha(config['target_model']),'draft_sha256':draft_sha,
                             'tokenizer_fingerprint':fingerprint,'config':config,'llama_commit':(ROOT/'native/llama.lock').read_text().strip()}
            run['identity']['verification_mode']=verification_mode
            run['identity']['pipeline']=pipeline
            run['identity']['target_runtime']=copy.deepcopy(self.target_info)
            run['identity']['local_draft_resident_at_start']=self.draft is not None
            if gate:run['identity']['draft_policy_version']=gate.version
            started=time.perf_counter();run['status']='running';self._publish(run)
            if self.cancelled.is_set():raise RuntimeError('cancelled')
            def payload_for(current,count,seq,op='draft'):
                return {'op':op,'epoch':run['epoch'],'prefix':list(current),'prefix_hash':prefix_digest(current),
                        'count':count,'sequence':seq,'pipeline':pipeline,'remaining':run['max_tokens']-len(generated),
                        'tokenizer_fingerprint':fingerprint,'model_sha256':draft_sha,'vocab_size':self.target_info['vocab_size']}
            if pipeline=='bounded_v1':
                if run['mode']=='local_draft':
                    self.draft.call('reset');local_pipeline=LocalLookahead(self.draft,self.cancelled)
                    local_pipeline.initialize(prefix,min(run['draft_k'],run['max_tokens']))
                elif run['mode']=='remote_draft':
                    remote_pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='nodelift-prefill-overlap')
                    first_remote=remote_pool.submit(self.mailbox.request,run['node_id'],payload_for(prefix,min(run['draft_k'],run['max_tokens']),0),self.cancelled,run['remote_timeout_ms']/1000)
            prefill_start=time.perf_counter()
            target_prefill=self.target.call('prefill',prefix=prefix)
            target_prefill_wall_ms=(time.perf_counter()-prefill_start)*1000
            target_prefill_native_ms=target_prefill.get('ms')
            run['metrics'].update(target_prefill_wall_ms=target_prefill_wall_ms,
                                  target_prefill_native_ms=target_prefill_native_ms,
                                  target_prefill_tokens_per_second=len(prefix)*1000/target_prefill_native_ms if target_prefill_native_ms and target_prefill_native_ms>0 else None,
                                  draft_initial_prefill_wall_ms=None,draft_initial_prefill_native_ms=None)
            if self.cancelled.is_set():raise RuntimeError('cancelled')
            if run['mode']=='local_draft' and self.draft is not None and local_pipeline is None:
                self.draft.call('reset')
                # Adaptive probes pay their own prefix prefill in the measured
                # draft round, after useful host calibration tokens are emitted.
                if not gate:
                    draft_prefill_start=time.perf_counter()
                    draft_prefill=self.draft.call('prefill',prefix=prefix)
                    run['metrics']['draft_initial_prefill_wall_ms']=(time.perf_counter()-draft_prefill_start)*1000
                    run['metrics']['draft_initial_prefill_native_ms']=draft_prefill.get('ms')
            decoding=time.perf_counter();mode=run['mode']
            run['metrics']['prefill_ms']=(decoding-started)*1000
            while len(generated)<run['max_tokens']:
                if self.cancelled.is_set():raise RuntimeError('cancelled')
                block_start=time.perf_counter();count=min(run['draft_k'],run['max_tokens']-len(generated));draft_ms=0
                verification_batch_width=0;response=None;draft_timing=None
                decision=gate.choose() if gate else None
                step_mode='host' if mode=='host' or (decision and decision.route=='host') else mode
                attempted_draft=step_mode!='host';effective_timeout_ms=None
                if step_mode=='host':
                    result=self.target.call('draft',prefix=prefix,count=1);result.update(accepted=0,proposed=0)
                else:
                    dstart=time.perf_counter()
                    if step_mode=='lookup':proposal=lookup.propose(prefix,count)
                    elif step_mode=='local_draft':
                        # A cold adaptive probe includes draft allocation/load
                        # and prefill. Short host-only completions avoid loading
                        # an unused draft model altogether.
                        try:
                            if self.draft is None:self._load(config,True)
                            if self.cancelled.is_set():raise RuntimeError('cancelled')
                            if local_pipeline:
                                local_reply=local_pipeline.request(prefix,count,run['max_tokens']-len(generated));proposal=local_reply['tokens']
                            else:
                                local_reply=self.draft.call('draft',prefix=prefix,count=count);proposal=local_reply['tokens']
                            draft_timing=local_reply.get('timing')
                        except Exception:
                            if self.cancelled.is_set() or not gate:raise
                            gate.disable('local_draft_failure');proposal=[]
                    else:
                        try:
                            payload=payload_for(prefix,count,sequence)
                            timeout=run['remote_timeout_ms']/1000
                            if gate:timeout=gate.remote_timeout(count,timeout)
                            effective_timeout_ms=timeout*1000
                            if first_remote is not None:
                                future=first_remote;first_remote=None;response=future.result()
                            else:response=self.mailbox.request(run['node_id'],payload,self.cancelled,timeout=timeout)
                            sequence+=1
                            if response.get('error'):raise RuntimeError(response['error'])
                            proposal=response['tokens']
                        except Exception as error:
                            if self.cancelled.is_set():raise
                            fallbacks+=1;mode=step_mode='host';proposal=[];run['fallback_reason']=str(error)[:300]
                            if gate:gate.disable('remote_probe_timeout' if isinstance(error,TimeoutError) else 'remote_failure')
                    draft_ms=(time.perf_counter()-dstart)*1000
                    if self.cancelled.is_set():raise RuntimeError('cancelled')
                    if run['mode']=='remote_draft':remote_wait_ms+=draft_ms
                    if proposal:
                        verification_batch_width=len(proposal)+1
                        result=self.target.call('verify',prefix=prefix,proposal=proposal,remaining=run['max_tokens']-len(generated),strict=verification_mode=='serial')
                        if response and response.get('lease_id'):self.mailbox.verified(run['node_id'],response['lease_id'],result.get('accepted',0))
                    else:
                        # Lookup misses and failed leases need no speculative
                        # batch. The ordinary target path synchronizes its KV.
                        step_mode='host'
                        result=self.target.call('draft',prefix=prefix,count=1);result.update(accepted=0,proposed=0)
                if self.cancelled.is_set():raise RuntimeError('cancelled')
                ids=result['tokens'];require_ids=bool(ids)
                if not require_ids:raise RuntimeError('engine produced no progress')
                decoded=self.target.call('text',tokens=ids)
                if self.cancelled.is_set():raise RuntimeError('cancelled')
                generated.extend(ids);prefix.extend(ids);accepted+=result.get('accepted',0);proposed+=result.get('proposed',0)
                run['text']+=decoder.decode(bytes.fromhex(decoded['bytes_hex']),final=False)
                now=time.perf_counter()
                if 'ttft_ms' not in run['metrics']:run['metrics']['ttft_ms']=(now-started)*1000
                if 'worker_first_token_ready_ms' not in run['metrics']:run['metrics']['worker_first_token_ready_ms']=(now-submitted)*1000
                if run['text'] and 'worker_first_text_ready_ms' not in run['metrics']:run['metrics']['worker_first_text_ready_ms']=(now-submitted)*1000
                run['blocks'].append({'generated':len(ids),'accepted':result.get('accepted',0),'proposed':result.get('proposed',0),
                                      'draft_ms':draft_ms,'block_ms':(now-block_start)*1000,'effective_mode':step_mode,
                                      'ready_offset_ms':(now-submitted)*1000,
                                      'uncommitted_proposals':result.get('proposed',0)-result.get('accepted',0),
                                      'verification_batch_width':verification_batch_width,
                                      'native_ms':result.get('ms'),'native_timing':result.get('timing'),'local_draft_timing':draft_timing,
                                      'verification_mode':result.get('verification_mode','target_only'),
                                      'remote_timing':response.get('timing') if response else None,
                                      'effective_timeout_ms':effective_timeout_ms,
                                      'decision':decision.to_dict() if decision else None})
                run['metrics'].update(generated_tokens=len(generated),accepted_tokens=accepted,proposed_tokens=proposed,
                                      elapsed_seconds=now-started,tokens_per_second=len(generated)/max(now-decoding,1e-9),
                                      decode_seconds=now-decoding,uncommitted_proposals=proposed-accepted,
                                      fallbacks=fallbacks,remote_wait_ms=remote_wait_ms)
                self._publish(run)
                round_ms=(time.perf_counter()-block_start)*1000
                run['blocks'][-1]['round_ms']=round_ms
                run['blocks'][-1]['published_offset_ms']=(time.perf_counter()-submitted)*1000
                if gate:
                    if attempted_draft and verification_batch_width:
                        gate.observe_draft(round_ms,len(ids),count)
                    elif not attempted_draft or (lookup is not None and not verification_batch_width):
                        gate.observe_host(round_ms,len(ids))
                    run['metrics']['draft_disabled_reason']=gate.disabled_reason
                if result.get('eos'):break
            run['text']+=decoder.decode(b'',final=True)
            run['finish_reason']='stop' if result.get('eos') else 'length'
            run['tokens']=generated;run['status']='completed';run['metrics']['request_total_ms']=(time.perf_counter()-submitted)*1000
        except Exception as error:
            run['status']='cancelled' if self.cancelled.is_set() else 'failed';run['error']=str(error)[:500];run['tokens']=generated
        finally:
            cleanup_start=time.perf_counter()
            if first_remote is not None and not first_remote.done():self.cancelled.set()
            if remote_pool:remote_pool.shutdown(wait=True,cancel_futures=True)
            if local_pipeline:
                try:run['lookahead_trace']=local_pipeline.close()
                except Exception:run['lookahead_cleanup_incomplete']=True
            if pipeline=='bounded_v1' and run['mode']=='remote_draft' and 'identity' in run:
                try:
                    self.mailbox.request(run['node_id'],payload_for(prefix,0,sequence,'finish'),threading.Event(),timeout=2)
                except Exception:run['lookahead_cleanup_incomplete']=True
            run['metrics']['cleanup_ms']=(time.perf_counter()-cleanup_start)*1000
            if run.get('epoch'):run['remote_trace']=self.mailbox.trace(run['epoch'])
            if 'identity' in run:run['identity']['local_draft_resident_at_finish']=self.draft is not None
            run['finished']=time.time()
            run['metrics']['request_total_ms']=(time.perf_counter()-submitted)*1000
            self._publish(run)
            # Prompt-bearing experiment results stay in the private host state.
            try:
                folder=self.state.folder/'inference';folder.mkdir(mode=0o700,exist_ok=True)
                path=folder/(run['id']+'.json');path.write_text(json.dumps(run,indent=2));path.chmod(0o600)
            finally:
                with self.lock:self.busy=False
