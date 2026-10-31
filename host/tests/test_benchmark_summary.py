"""Performance ratios must compare actual identical outputs, including failures."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('optimization_benchmark',Path(__file__).resolve().parents[2]/'scripts/benchmark-optimization.py')
benchmark=importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class BenchmarkSummaryTests(unittest.TestCase):
    def test_mismatches_and_failures_stay_in_denominator_without_speedup(self):
        rows=[]
        for variant in benchmark.VARIANTS:
            rows.append({'variant':variant,'prompt_id':0,'repetition':0,'status':'completed',
                         'tokens':[1,2], 'metrics':{'elapsed_seconds':2,'ttft_ms':10}})
        next(r for r in rows if r['variant']=='baseline_draft')['tokens']=[1,3]
        next(r for r in rows if r['variant']=='optimized_draft')['tokens']=[1,3]
        failure=next(r for r in rows if r['variant']=='lookup')
        failure.update(status='failed',metrics={})
        summary=benchmark.summarize(rows)['all']
        self.assertEqual(summary['adaptive_draft']['speedup_pair_count_vs_baseline_draft'],0)
        self.assertIsNone(summary['adaptive_draft']['median_speedup_vs_baseline_draft'])
        self.assertEqual(summary['optimized_draft']['exact_pairs'],0)
        self.assertEqual(summary['optimized_draft']['speedup_pair_count_vs_baseline_draft'],1)
        self.assertEqual(summary['lookup']['runs'],1)
        self.assertEqual(summary['lookup']['completed'],0)
        self.assertFalse(summary['lookup']['all_tokens_equal'])
        self.assertIsNone(summary['lookup']['median_ttft_ms'])
