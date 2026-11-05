"""Create a narrowly modified, attributed copy of the installed MIT generator."""
from pathlib import Path
import ast,hashlib,importlib.util,json
P=Path(__file__).resolve().parent
spec=importlib.util.find_spec('mlx_lm');root=Path(spec.origin).parent;source=(root/'generate.py').read_text();tree=ast.parse(source);node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='speculative_generate_step');code='\n'.join(source.splitlines()[node.lineno-1:node.end_lineno])+'\n'
code=code.replace('def speculative_generate_step(', 'def adaptive_generate_step(',1).replace('    num_draft_tokens: int = 2,','    num_draft_tokens: int = 2,\n    policy=None,\n    trace=None,',1)
code=code.replace('                num_draft = min(max_tokens - ntoks, num_draft_tokens)','                num_draft = min(max_tokens - ntoks, policy.choose() if policy else num_draft_tokens)\n                block_started = time.perf_counter()')
code=code.replace('                draft_tokens = _draft_generate(draft_y, num_draft)','                draft_tokens = _draft_generate(draft_y, num_draft)\n                mx.eval(draft_tokens)\n                drafted_at = time.perf_counter()')
code=code.replace('                tokens = tokens.tolist()\n                n = 0','                tokens = tokens.tolist()\n                verified_at = time.perf_counter()\n                row = {"k": num_draft, "accepted": 0, "emitted": 0, "draft_seconds": drafted_at-block_started, "verify_seconds": verified_at-drafted_at}\n                if trace is not None: trace.append(row)\n                n = 0')
code=code.replace('                    yield tn, lpn, True','                    row["accepted"] += 1\n                    row["emitted"] += 1\n                    yield tn, lpn, True')
code=code.replace('                    yield tokens[n], logprobs[n], False','                    row["emitted"] += 1\n                    yield tokens[n], logprobs[n], False\n\n                row["wall_seconds"] = time.perf_counter()-block_started\n                if policy: policy.observe(row)')
header='''# Copyright © 2023 Apple Inc.
# NodeLift experimental modifications, 2026 Fabrizio Degni.
# SPDX-License-Identifier: MIT
# Derived from mlx-lm 0.32.2 speculative_generate_step. See MLX-LM-LICENSE.txt.
from typing import *
import functools,time
import mlx.core as mx
import mlx.nn as nn
from mlx_lm.generate import generation_stream,DEFAULT_QUANTIZED_KV_START,maybe_quantize_kv_cache
from mlx_lm.models.cache import make_prompt_cache,can_trim_prompt_cache,trim_prompt_cache
from mlx_lm.sample_utils import Sampler,LogitsProcessor,greedy_sampler
'''
(P/'adaptive_mlx.py').write_text(header+'\n'+code)
license_path=next(root.parent.glob('mlx_lm-*.dist-info/licenses/LICENSE'))
(P/'MLX-LM-LICENSE.txt').write_text(license_path.read_text())
(P/'upstream-source.json').write_text(json.dumps({'package':'mlx-lm','version':'0.32.2','generate_sha256':hashlib.sha256(source.encode()).hexdigest(),'original_function_sha256':hashlib.sha256('\n'.join(source.splitlines()[node.lineno-1:node.end_lineno]).encode()).hexdigest(),'changes':['per-block measured costs','bounded policy k selection','permanent per-request fallback','candidate and emitted-token accounting'],'license':'MIT'},indent=2)+'\n')
