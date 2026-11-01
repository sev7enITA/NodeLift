"""Diagnostic gates must not confuse an installed executable with a qualified engine."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('doctor', Path(__file__).resolve().parents[1] / 'doctor.py')
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


class DoctorTests(unittest.TestCase):
    def test_missing_build_tools_are_reported_without_native_execution(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(doctor.shutil, 'which', return_value=None), \
                patch.object(doctor.Path, 'is_file', return_value=False):
            report = doctor.inspect(Path(folder))
        self.assertFalse(report['build_prerequisites_found'])
        self.assertIn('cmake', report['missing_required'])
        self.assertFalse(report['inference_qualified'])

    def test_optional_tools_do_not_block_host_build(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(doctor.shutil, 'which', side_effect=lambda name: None if name in ('node', 'adb', 'xcodegen') else '/tool'), patch.dict(os.environ, {}, clear=True):
            report = doctor.inspect(Path(folder))
        self.assertTrue(report['build_prerequisites_found'])
        self.assertFalse(report['inference_qualified'])

    def test_present_native_file_is_not_runtime_qualification(self):
        with tempfile.TemporaryDirectory() as folder:
            native = Path(folder)/'private-library';native.write_bytes(b'not a shared library')
            with patch.dict(os.environ, {'NODELIFT_LIBRARY': str(native)}):
                report = doctor.inspect(Path(folder))
            row = next(row for row in report['checks'] if row['name'] == 'native_library')
            self.assertEqual(row['state'], 'present_unverified')
            self.assertFalse(report['inference_qualified'])
            self.assertNotIn(folder, str(report))


if __name__ == '__main__':
    unittest.main()
