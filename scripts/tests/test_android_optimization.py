import runpy
from pathlib import Path
import unittest

module = runpy.run_path(str(Path(__file__).parents[1] / 'check-android-optimization.py'))
audit = module['audit']

class OptimizationAudit(unittest.TestCase):
    def commands(self, flags):
        return [{'file': '/fixture/' + unit, 'arguments': ['clang', *flags, '-c', unit]}
                for unit in module['REQUIRED']]

    def test_unoptimized_is_rejected(self):
        self.assertFalse(audit(self.commands(['-g']))['passed'])

    def test_optimized_debug_is_accepted(self):
        self.assertTrue(audit(self.commands(['-g', '-O3']))['passed'])

    def test_later_override_is_rejected(self):
        self.assertFalse(audit(self.commands(['-O3', '-O0']))['passed'])

    def test_missing_kernel_is_rejected(self):
        self.assertFalse(audit(self.commands(['-O3'])[:-1])['passed'])

    def test_fast_math_is_rejected(self):
        self.assertFalse(audit(self.commands(['-O3', '-ffast-math']))['passed'])

if __name__ == '__main__':
    unittest.main()
