"""Attribute and instrument the previous research generator without altering archived evidence."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;old=P.parent/'adaptive-targets-2026-11-05/adaptive_mlx.py'
source=old.read_text();code=source.replace('def adaptive_generate_step(', 'def accounted_generate_step(',1)
code=code.replace('    trace=None,','    trace=None,\n    telemetry=None,',1)
code=code.replace('    y = prompt.astype(mx.uint32)','    telemetry = telemetry if telemetry is not None else {}\n    y = prompt.astype(mx.uint32)',1)
code=code.replace('        draft_y = _prefill(draft_model, draft_cache, y)\n        y = _prefill(model, model_cache, y)',
'''        prefill_start = time.perf_counter()
        draft_y = _prefill(draft_model, draft_cache, y)
        mx.eval([c.state for c in draft_cache])
        draft_prefilled = time.perf_counter()
        y = _prefill(model, model_cache, y)
        mx.eval([c.state for c in model_cache])
        telemetry['draft_prefill_seconds'] = draft_prefilled-prefill_start
        telemetry['target_prefill_seconds'] = time.perf_counter()-draft_prefilled
        first_block = True''',1)
code=code.replace('                row["wall_seconds"] = time.perf_counter()-block_started\n                if policy: policy.observe(row)\n', '',1)
code=code.replace('                _rewind_cache(num_draft, n)\n        finally:',
'''                rewind_started = time.perf_counter()
                _rewind_cache(num_draft, n)
                row['rewind_seconds'] = time.perf_counter()-rewind_started
                row['wall_seconds'] = time.perf_counter()-block_started
                row['controller_charge_seconds'] = row['wall_seconds'] + (telemetry['draft_prefill_seconds'] if first_block else 0)
                first_block = False
                if policy: policy.observe(row)
        finally:''',1)
code=code.replace('        finally:\n            _rewind_cache(num_draft, n)',
'''        finally:
            cleanup_started = time.perf_counter()
            _rewind_cache(num_draft, n)
            telemetry['final_rewind_seconds'] = time.perf_counter()-cleanup_started
            if trace and 'wall_seconds' not in trace[-1]:
                trace[-1]['wall_seconds'] = time.perf_counter()-block_started
                trace[-1]['closed_before_policy_update'] = True''',1)
(P/'accounted_mlx.py').write_text(code)
(P/'accounting-origin.json').write_text(json.dumps({'source':'../adaptive-targets-2026-11-05/adaptive_mlx.py','source_sha256':hashlib.sha256(source.encode()).hexdigest(),'changes':['prefill phase trace','rewind and final-close trace','controller observes after rewind','initial draft-prefill charge available to controller'],'license':'MIT, Apple MLX-LM and NodeLift attribution retained'},indent=2)+'\n')
