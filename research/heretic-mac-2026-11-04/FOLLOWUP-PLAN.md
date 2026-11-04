# Open-ended follow-up

The first pass hit its 128-token cap on all four open-ended cases for the original and refusal variant. The strategy prompt was interpreted as phone messaging rather than LLM inference. This is an input-context limitation. Preserve those responses; do not treat their incomplete conclusions as scored defects. Rerun the same four cases for all three variants with an identical NodeLift context, a 100-word instruction and 256-token cap. This informed follow-up is separate from the predeclared 16-answer primary score, and never selects an adapter.
