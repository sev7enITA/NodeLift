# Heretic on Apple Silicon: predeclared bounded pilot

Date: 4 November 2026. Scope: actual local feasibility and paired experiments, not a production qualification. No models or datasets will be uploaded. Existing NodeLift runtimes and mobile releases remain unchanged.

## Arms

1. Qwen3-4B-Instruct-2507 original versus two Heretic 2.0 ARA modifications: refusal suppression and the upstream anti-sycophancy configuration. Use the exact same pinned base artifact, tokenizer, chat template, dtype, backend and greedy generation for held-out evaluation. Run at most four search trials per variant, seed 42, batch one, rank eight, one outer L-BFGS step and five inner iterations. This is a small screening budget, not a reproduction of upstream quality claims.
2. Qwen3-0.6B original versus a custom teacher-agreement modification, with the original 4B model as teacher. Separate calibration prompts from evaluation. Verify vocabulary/token-ID compatibility before transferring token IDs. Measure agreement and discarded candidates; no distributed or end-to-end speculative speedup follows from teacher-forced agreement.
3. Inspect the availability of Lophius introspection and capture at least one local model diagnostic if compatible. Its PyTorch execution is distinct from the existing llama.cpp batch-divergence investigation.

## Controls and admission

Create and hash the held-out technical, clean-code, false-premise and legitimate-correction cases before modifying weights. Evaluate correctness separately from format compliance and refusal-keyword rate. Do not execute model-proposed code. Preserve raw responses and fixed answer keys. Record uncertainty descriptively for this small targeted sample; token-level observations are not independent workloads. Select the first upstream sorted Pareto trial using calibration scores only; disclose that ordering favors the first objective. For the custom draft scorer use only calibration teacher outputs.

Use native MPS initially without bitsandbytes quantization. Record unsupported operations or CPU fallback explicitly. Bound each processing stage to 30 minutes; preserve failed attempts and avoid repeated blind retries. Stop for nonfinite tensors, a model/runtime error or sustained system memory pressure. At least 8 GiB of disk must remain free. Sequential inference only, and confirm NodeLift is idle before starting. Pin package versions and model revisions, retain hashes and actual outputs. Physical CUDA, Windows, network offload, sustained energy and multi-device latency remain separate P16 tests.
