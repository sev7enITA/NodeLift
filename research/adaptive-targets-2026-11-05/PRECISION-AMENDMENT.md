# Additional precision lane after 14B screening

The original 14B screening completed 27 runs. Every speculative configuration matched two of three target-only outputs and differed on the code prompt. Faster elapsed time therefore does not qualify any configuration. Validation prompts have not been executed or used for tuning.

Add a separately labelled FP32 floating-parameter lane for the 14B model pair. Use MLX Module.set_dtype(float32), whose default predicate converts floating parameters but preserves packed integer quantized weights. This also changes activation/KV arithmetic and can increase memory/time; it is not an output-preserving claim relative to the original BF16/FP16 lane. Both target-only and candidate arms in this lane use the identical changed precision. Record actual dtypes and memory, and compare only within the lane.

Retain the original screening as a failed correctness gate. Do not spend the full validation budget qualifying that original 14B lane. If the separate FP32 screening has candidates with complete output equality, freeze its choices and validate them on the untouched validation prompts. The original 32B lane remains in scope after download and resource admission. This is a post-screening experiment, not an amendment to historical results.
