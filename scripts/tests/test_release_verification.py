import importlib.util
import io
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release_verify', Path(__file__).resolve().parents[1]/'verify-release.py')
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class ReleaseVerificationTests(unittest.TestCase):
    def test_invalid_tag_is_rejected_before_network(self):
        with patch.object(verify.urllib.request, 'urlopen') as request:
            with self.assertRaises(ValueError):
                verify.verify('v0.2.3/../../unexpected')
            request.assert_not_called()

    def test_foreign_asset_is_not_fetched(self):
        asset = dict(name='model.apk', browser_download_url='https://example.com/model.apk', size=3)
        with patch.object(verify.urllib.request, 'urlopen') as request:
            with self.assertRaises(ValueError):
                verify.read_asset(asset, 'v0.2.3')
            request.assert_not_called()

    def test_corrupt_asset_fails_digest_gate(self):
        asset = dict(name='model.apk', browser_download_url='https://github.com/sev7enITA/NodeLift/releases/download/v0.2.3/model.apk', size=3, digest='sha256:'+'0'*64)
        with patch.object(verify.urllib.request, 'urlopen', return_value=io.BytesIO(b'bad')):
            with self.assertRaisesRegex(ValueError, 'digest'):
                verify.read_asset(asset, 'v0.2.3')

    def test_oversized_stream_is_rejected(self):
        asset = dict(name='model.apk', browser_download_url='https://github.com/sev7enITA/NodeLift/releases/download/v0.2.3/model.apk', size=2, digest='sha256:'+'0'*64)
        with patch.object(verify.urllib.request, 'urlopen', return_value=io.BytesIO(b'large')):
            with self.assertRaisesRegex(ValueError, 'exceeded declared size'):
                verify.read_asset(asset, 'v0.2.3')
