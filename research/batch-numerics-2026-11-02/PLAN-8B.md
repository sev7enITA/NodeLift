# Additional 8B shape control

Added after the four 1.5B and two 0.5B shape runs, before any 8B shape run. The same generic prompts and offset/width selection will be used with the locally installed Llama 3.1 8B Q4_K_M, requested Metal offload and requested flash attention enabled. Generate a fixed target trace before the probe and preserve its model hash; do not compare raw counts as if the Qwen and Llama tokenizers produced the same windows or lengths. Keep the serial-repeat A/A control. This targeted addition tests whether the issue is visible in a second architecture at larger size; absence of flips in these few windows cannot prove parity.

A strict-serial native correctness run for this 8B target will be run separately with the same 31-check harness. This planned shape control and correctness run start only after the local 8B paired performance pilot has stopped, to avoid adding load during that pilot.
