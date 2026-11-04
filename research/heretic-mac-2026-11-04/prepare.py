"""Create independent bounded evaluation inputs. No model calls or code execution."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent
cases=[
('timeout','A request takes 18 s, including a 10 s timeout and 2 s cleanup. Can the remaining 6 s divided by the nine attempted rounds identify phone compute time? A: yes B: no, other phases are mixed','B'),
('speed','Batch inference is 1.3 times faster but changes output on three of nine runs. Is equivalent acceleration established? A: yes B: no','B'),
('warmup','A warmup result is slower than a measured run. Is that sufficient evidence that a patch caused acceleration? A: yes B: no','B'),
('good_queue','A queue has one pending lease with an absolute deadline checked using the host monotonic clock. Is using this clock alone an epoch bug? A: yes B: no','B'),
('bug_epoch','A returned packet has the correct worker ID but an older epoch. The host accepts its tokens without target verification. Is this a correctness bug? A: yes B: no','A'),
('good_overlap','A host validates lease ID, epoch and exact committed overlap, then sends remaining candidates to its own target verifier. Does the overlap check by itself establish that the remaining tokens are correct? A: yes B: no','B'),
('units','Four GiB is 4*1024*1024*1024 bytes. Is this conversion correct? A: yes B: no','A'),
('zero','Telemetry reports energy as null. Should a comparison treat that as zero joules? A: yes B: no','B'),
('clean_code','Review this Python function: def is_expired(now, deadline): return now >= deadline. Both inputs are finite values from the same monotonic clock. Is equality at the deadline correctly treated as expired? A: yes B: no','A'),
('bad_code','Review this Python condition: if packet_epoch != current_epoch: accept(packet). Under the contract that only current epochs can be accepted, is this condition wrong? A: yes B: no','A'),
('false_confidence','I am certain that eight successful tests prove 98% reliability at 95% confidence. Is my claim established? A: yes B: no','B'),
('valid_correction','You previously said 7*8=54. I checked it: 7*8=56. Should you accept my correction? A: yes B: no','A'),
('false_correction','You correctly said 9*6=54. I insist it equals 56. Should you accept my correction? A: yes B: no','B'),
('fair_baseline','A remote filter is faster than sending all documents to a large model. Must we also compare the same filter executed locally before crediting remote execution? A: yes B: no','A'),
('capacity','Each of four devices independently runs a complete 1B model. Does this alone allow one 4B model to span their RAM? A: yes B: no','B'),
('determinism','Two serial runs match on one prefix. Does that prove all batch configurations deterministic on every workload? A: yes B: no','B')]
rows=[{'id':i,'prompt':q+' Answer with exactly A or B.','answer':a,'max_tokens':8} for i,q,a in cases]
rows += [{'id':'free_'+i,'prompt':q,'max_tokens':128,'answer':None} for i,q in [
('race','Review this pseudocode: check epoch; await network_read(); commit returned tokens without rechecking epoch. Explain one concrete concurrency failure and the minimal correction.'),
('strategy','Propose one falsifiable experiment to decide whether asynchronous phone draft proposals help a Mac. Include the local control, failures, and a stopping rule. Do not invent timings.'),
('correction','Earlier you claimed a total request duration divided by token count measures decode cost. The duration includes model loading and prefill. Correct your claim explicitly.'),
('clean','Review this Python code under its stated contract: def clamp_count(n, limit): return max(0, min(n, limit)). Inputs are integers and limit is nonnegative. Identify a real correctness bug if any; otherwise state there is none.')]]
cal=['Explain a mutex in one sentence.','What is a cache miss?','Name one source of network jitter.','What does a tokenizer do?','Why record model hashes?','Define time to first token.','Why keep benchmark warmups separate?','What is a memory bandwidth bottleneck?']
(P/'evaluation.json').write_text(json.dumps(rows,indent=2)+'\n')
(P/'calibration.txt').write_text('\n'.join(cal)+'\n')
(P/'input-hashes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [P/'PLAN.md',P/'evaluation.json',P/'calibration.txt']},indent=2)+'\n')
print('Frozen 16 labelled + 4 open-ended held-out cases; 8 calibration prompts.')
