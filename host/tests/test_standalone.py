import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / 'scripts/standalone-node.py'
spec = importlib.util.spec_from_file_location('standalone_node', SOURCE)
node = importlib.util.module_from_spec(spec)
spec.loader.exec_module(node)


class StandaloneTests(unittest.TestCase):
    def test_missing_bundled_benchmark_does_not_claim_readiness(self):
        with patch.object(node, 'bundled_benchmark', return_value=None):
            check = node.startup_check()
        self.assertEqual(check['bundled_llama_bench'], 'missing')
        self.assertFalse(check['automatic_upload'])
        self.assertFalse(check['runtime_download'])

    def test_benchmark_uses_bundled_program_when_available(self):
        check = {'bundled_llama_bench': 'ok', 'embedded_python': True}
        with patch.object(node, 'startup_check', return_value=check), \
             patch.object(node, 'bundled_benchmark', return_value=Path('/test/llama-bench')), \
             patch.object(node.probe, 'main', return_value=0) as run:
            self.assertEqual(node.main(['benchmark', '--model', 'm.gguf', '--output', 'r.json']), 0)
        self.assertEqual(run.call_args.args[0][:3], ['benchmark', '--executable', '/test/llama-bench'])

    def test_missing_runtime_blocks_automatic_benchmark_but_inventory_still_runs(self):
        check = {'bundled_llama_bench': 'missing', 'embedded_python': True}
        with patch.object(node, 'startup_check', return_value=check), \
             patch.object(node.probe, 'main', return_value=0) as run:
            self.assertEqual(node.main(['benchmark', '--model', 'm.gguf', '--output', 'r.json']), 1)
            self.assertEqual(node.main(['inventory', '--output', 'i.json']), 0)
        self.assertEqual(run.call_count, 1)

    def test_user_supplied_executable_is_not_replaced(self):
        with patch.object(node, 'startup_check', return_value={'bundled_llama_bench': 'missing'}), \
             patch.object(node.probe, 'main', return_value=0) as run:
            node.main(['benchmark', '--executable', '/custom/bench', '--model', 'm', '--output', 'r'])
        self.assertEqual(run.call_args.args[0][2], '/custom/bench')


if __name__ == '__main__':
    unittest.main()
