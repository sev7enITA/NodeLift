# GLM 5.3 Max static review

1 November 2026. Browser model selector showed GLM-5.3 and Effort Max. Reviewed the initial two new backend modules, not the final fixes or the entire application. This is model-generated review, not execution evidence. See REVIEW-RESOLUTION.md for independent adjudication and fixes. No credentials or private runtime data were supplied.

Verdict: No P0 found. The trust boundaries hold up better than most code I review: credentials cannot be redirected, there are no hidden retry/billing loops, and memory/disk bounds are real. What I did find: 2 P1s (a transfer state machine that can wedge with no recovery path, and a silent-corruption path in the upload protocol), 4 P2s, and a set of P3 nits. Findings assume the stated controller invariants (loopback admin gate with exact Host/Origin, serialized generation, message/limit validation); where module safety silently depends on the controller, I flag it.

P1-1 — Transfer state machine can wedge permanently; cancel() is not a recovery path for most states

Location: ModelLibrary.download(), finish(), cancel(), _expire(), _fail()

Trigger conditions:

threading.Thread(...).start() raises (RuntimeError: can't start new thread under thread/ulimit/memory pressure). In download(), the start() call is outside any try block and runs after _begin() has already committed self.transfer = {'status': 'transferring'} and created the part file. Same in finish() — status is already 'verifying'.
Worker dies inside _fail(): its self._part().unlink(missing_ok=True) is unprotected; an OSError there (immutable bit, ACL, virtiofs quirk) kills the thread while the outer except Exception in _download re-enters _fail() and dies again.

Mechanism: Every exit from 'transferring'/'verifying' happens in the worker thread (_download, _finalize, _fail). cancel() transitions status only for kind == 'upload' and status == 'transferring'; for huggingface-kind or 'verifying' it merely sets the event and returns {'cancelled': True} — a no-op without a live worker. _expire() covers only kind == 'upload' and status == 'transferring'. Result: status stays 'transferring'/'verifying' forever, _begin() refuses every future transfer ("Finish or cancel the current model transfer"), and for hf-kind the orphaned part file (up to the declared size) is never unlinked — only _fail/_expire unlink.

Impact: Entire import/download subsystem unusable, plus a disk leak, until process restart. Reachable without any attacker — ordinary resource exhaustion suffices.

Fix direction: start the thread inside a try that rolls back via _fail(); make cancel() authoritative (transition status + unlink under the lock itself); add expiry for 'verifying' and hf-kind; guard _fail()'s unlink.

P1-2 — Partial disk write during upload_chunk permanently skews the part file → silently registered corrupt model

Location: upload_chunk() (append-mode write), _finalize() (acceptance path for uploads)

Trigger conditions: Any chunk whose flush puts >0 but <len bytes on disk before raising — ENOSPC/EDQUOT/EIO, realistic on overlayfs/virtiofs/NFS. Note the 1 GiB headroom in _begin() is advisory and raced: it is checked once, and concurrent disk consumers can erase it mid-transfer. Signal-interrupted writes can also short-write.

Mechanism trace:

File is opened 'ab' — every write lands at current EOF. received increments only after a fully successful write+close.
Partial write of chunk at offset O leaves file = O + k while received stays O.
Client resumes/retries at offset O (the offset == received check passes — disk state is invisible to it) → appends L bytes at EOF → file = O + k + L, received = O + L. The skew k` persists to completion because append mode never realigns.
finish() sees received == bytes ✓. _finalize() hashes the bytes + k file — but uploads carry no expected sha256 (source = {'kind': 'upload'}, so expected is None) and the 24-byte GGUF header is intact → the duplicated k-byte region mid-file is registered as completed with a truthful-but-meaningless computed hash, and handed to the native catalog.

Impact: Silently corrupt weights loaded by the pinned runtime — wrong outputs or a load failure far from the root cause. This is the one place the "corruption" dimension actually breaks.

Note what doesn't break: the offset protocol correctly rejects a duplicate append after a lost HTTP response (offset mismatch), and the download path fails cleanly on write errors because it has no retry-append semantics. The gap is specifically disk-level partial writes.

Fix direction: before each append, ftruncate(part, received) or verify st_size == received and fail otherwise; fsync before acknowledging a chunk; map the raw OSError (see P3) to ValueError.

P2-1 — Registry has no fsync and resets silently on any parse failure

_register() does tmp-write → os.replace with no flush()/fsync() of the file or the directory. Power loss in the window can persist the rename without the contents → zero-length registry. __init__ then hits json.loads failure → except: pass → records silently resets to {}: every model vanishes from paths() while up to hundreds of GiB of files orphan on disk, with no re-link API except manual import_path. The same silent reset masks genuine corruption/tampering with no signal. Fix: fsync file+dir before replace; keep a .bak; raise/alert on parse failure instead of pass.

P2-2 — providers.stream() deadline and cancelled-event checks only run between SSE lines; a trickling stream defeats the 300 s cap

readline(65537) can block across many recvs: each recv gets its own 60 s socket timeout, so an endpoint (local server or intermediary) that sends ≥1 byte per <60 s without a newline holds one readline for up to 65536 × gap — hours to weeks. The deadline check, the 8 MiB total cap, and cancelled.is_set() all sit between lines and never fire. Only Providers.cancel()'s socket shutdown (or a full 60 s stall) interrupts it. Since generation is serialized under the controller's lock, one pathological stream blocks all generation while "deadline exceeded" is advertised but unenforced. Fix: sock.settimeout(min(remaining_budget, 60)) per readline, or a select loop with an absolute deadline.

P2-3 — self.active lifetime is tied to generator finalization → configure-lockout via an abandoned generator

The finally that clears self.active and closes the connection runs only when the generator is closed, exhausted, or GC'd. If the controller stops consuming early (client disconnect) and retains or fails to close() the generator — e.g., a run snapshot that keeps it referenced — finally never runs: configure() permanently refuses ("Stop the provider run before changing access") and cancel() targets a zombie socket. The module neither enforces single-flight nor watches for this; the invariant lives entirely in controller code you haven't shown. (A second overlapping stream() would also silently overwrite self.active — the is connection guard prevents mis-clearing but not the ambiguity.)

P2-4 — Network-controlled JSON shapes escape the ValueError contract (uncaught AttributeError/KeyError)

Concrete instances, all reachable from peer-controlled data:

providers.stream(): value.get('error'), choices[0] / change.get(...), usage.get(...) when a data: payload is a list/scalar, or choices is a dict → AttributeError/KeyError. The except tuple is only (OSError, HTTPException, UnicodeError, JSONDecodeError).
providers.models(): (row.get('architecture') or {}).get(...) when architecture is a list; row.get when rows elements are scalars → AttributeError (not in that tuple either).
model_library.search(): r.get('id') when rows is a dict (iterates keys) or contains scalars.
model_library.inspect(): data.get(...) / row.get(...) on non-dict shapes from the HF API.

Impact depends on the controller's error mapping; at best these become unclassified 500/traceback paths on the admin surface, at worst they wedge handler-level error handling that only catches ValueError. Fix: isinstance guards on every network-decoded shape and broaden the tuples.

P3 (one-liners)
inspect()'s revision regex permits ./..; quote(revision, safe='') keeps dots, so /revision/../… can alias the default branch server-side. Content stays pinned by the returned sha — provenance mislabel only.
open('w'/'xb') then chmod 0600 leaves a microsecond window at default perms (0644 & ~umask) for the registry tmp and part files — use os.open(..., 0o600).
Re-downloading the same repo file gets a fresh random identity — up to 512 GiB duplicated, no sha256 dedup, and no orphan-relink API after registry loss.
SSE dispatch happens only on blank lines: a spec-permitted stream ending immediately after data: [DONE] (EOF dispatch) is rejected as "ended before completion" — minimal local servers can hit this.
json.JSONDecodeError in stream() is rewrapped as "connection interrupted" (misdiagnosis); _download()'s generic message masks HubRedirect policy rejections.
upload_chunk()/upload_start() can surface raw OSError (open/write failures) instead of the module's ValueError convention; same for TypeError if data arrives as str.
model-library.tmp isn't cleaned at init; two ModelLibrary instances on one folder would interleave tmp writes — enforce/document single-instance.
import_path() has no MAX_MODEL bound and no later re-validation — a symlink swap after registration goes unnoticed (admin-gated, low severity).
No Range/resume: a mid-transfer failure of a 512 GiB download restarts from zero.
stream() relies entirely on the controller for messages/max_tokens validation — no in-module bound on request body size.
Probed and holds (so the negative results are meaningful)
Credentials: the OpenRouter key goes only to openrouter.ai over cert-verified TLS on a fixed HTTPSConnection; http.client never auto-follows redirects, so the Authorization header cannot be bounced to a third-party Location. It is stripped for the public /models call. status() exposes booleans only. local_api is pinned to literal 127.0.0.1/localhost, scheme http, exact /v1 path, no userinfo/query/fragment, ports ≠ 9867/9868 (no self-connection). Hub downloads attach no credentials at all, so nothing leaks across CDN redirects. Key validation rejects non-printable/oversized values (no header CRLF injection).
Silent billing retries: none. Exactly one connection.request() per run, no retry loops, no fallback (allow_fallbacks: False, data_collection: 'deny'), failures raise. Residual and inherent, not a bug: a cancel issued after the request is sent, or a disconnect after server-side completion, still consumes one generation.
Memory bounds: hub JSON ≤ 8 MiB; catalogs ≤ 8 MiB and 5000 rows; SSE ≤ 64 KiB/line and 8 MiB total; upload chunks ≤ 1 MiB bounded by declared size; downloads bounded by declared size; finalize hashes in 1 MiB reads. The only unbounded read is the registry read_text() of a self-written file.
Races: all transfer-state and registry mutations sit under one RLock (the _register-inside-_finalize reentrancy is safe because it's an RLock); no network I/O is performed while holding the providers lock; models()'s port-snapshot guard correctly prevents catalog clobbering across a concurrent configure(); cancel() vs _finalize()'s publish is properly serialized (the cancelled re-check happens under the same lock as the rename), so there is no cancel-vs-publish race.
Corruption (download path): re-reads pinned metadata rather than trusting the browser, re-verifies sha256 + header before publishing, and rolls back the destination if the registry write fails. The upload path is the gap (P1-2).
GGUF handling: import-time 24-byte header parse only; no model code is executed here, and this review makes no claim about whether any model loads or behaves at runtime — that remains the pinned runtime's decision.

Scope caveats: controller code unseen — P2-3, P2-4 and the body-size note mark exactly where these modules delegate safety to it. Single-process, single-instance operation is assumed throughout.

The two P1s are both fixable in well under a day: move the thread-start inside a rollback try plus an authoritative cancel(), and ftruncate-to-received before each append. Happy to review the patched versions or export this as a tracked file if you want it alongside the repo.
