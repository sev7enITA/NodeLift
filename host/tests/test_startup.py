import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import unittest


class StartupTests(unittest.TestCase):
    def test_fresh_private_state_can_start_gateway(self):
        with tempfile.TemporaryDirectory() as folder:
            process=subprocess.Popen([sys.executable,'-m','nodelift.host','--address','127.0.0.1',
                                      '--port','0','--dashboard-port','0','--state',folder],
                                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout,selectors.EVENT_READ)
                    self.assertTrue(selector.select(timeout=10),'host did not become ready')
                    first=process.stdout.readline()
                    self.assertIn('experimental native inference',first)
                key=Path(folder)/'client-api-key'
                self.assertTrue(key.is_file())
                self.assertEqual(key.stat().st_mode & 0o777,0o600)
                self.assertGreaterEqual(len(key.read_text()),32)
            finally:
                process.terminate()
                try:process.communicate(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.communicate()
