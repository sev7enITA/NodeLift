import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class FrozenPathTests(unittest.TestCase):
    def test_native_root_uses_frozen_resource_directory(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as folder:
            code = ('import sys; sys._MEIPASS=sys.argv[1]; '
                    'from nodelift.native import ROOT; print(ROOT)')
            env = dict(os.environ, PYTHONPATH=str(root/'host'))
            result = subprocess.run([sys.executable, '-c', code, folder], env=env,
                                    capture_output=True, text=True, check=True)
            self.assertEqual(Path(result.stdout.strip()), Path(folder))


if __name__ == '__main__':
    unittest.main()
