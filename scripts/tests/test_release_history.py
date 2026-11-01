"""Release gates must catch undocumented builds and stale cross-platform metadata."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('release_history', ROOT/'scripts/release-history.py')
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)


class ReleaseHistoryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        for name in ('apps/android/app/build.gradle.kts', 'apps/ios/project.yml', 'site/NodeLift/data/mobile-downloads.json', 'site/NodeLift/index.html'):
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((ROOT/name).read_text())
        self.data = json.loads((ROOT/'releases/history.json').read_text())

    def test_current_versions_and_generated_history_are_consistent(self):
        self.assertEqual(history.validate(self.data, self.root), [])
        for path, expected in history.outputs(self.data, ROOT).items():
            self.assertEqual(path.read_text(), expected, str(path))

    def test_android_or_ios_build_increment_requires_notes(self):
        build = self.data['releases'][0]['build']
        for name, old, new in (
            ('apps/android/app/build.gradle.kts', f'versionCode = {build}', f'versionCode = {build + 1}'),
            ('apps/ios/project.yml', f'CURRENT_PROJECT_VERSION: {build}', f'CURRENT_PROJECT_VERSION: {build + 1}'),
        ):
            with self.subTest(platform=name):
                path = self.root/name
                original = path.read_text()
                self.assertIn(old, original)
                path.write_text(original.replace(old, new))
                self.assertTrue(any('lacks matching latest history' in error for error in history.validate(self.data, self.root, build_only=True)))
                path.write_text(original)

    def test_stale_portal_blocks_release_but_not_prepublication_compile(self):
        path = self.root/'site/NodeLift/data/mobile-downloads.json'
        data = json.loads(path.read_text()); data['build'] -= 1
        path.write_text(json.dumps(data))
        self.assertTrue(any('Portal' in error for error in history.validate(self.data, self.root)))
        self.assertEqual(history.validate(self.data, self.root, build_only=True), [])
        self.data['releases'][0]['published_at'] = None
        self.assertEqual(history.validate(self.data, self.root, build_only=True), [])
        self.assertTrue(any('publication timestamp' in error for error in history.validate(self.data, self.root)))

    def test_duplicate_build_and_missing_limits_are_rejected(self):
        self.data['releases'][1]['build'] = self.data['releases'][0]['build']
        self.data['releases'][0]['limitations'] = ''
        errors = history.validate(self.data, self.root)
        self.assertTrue(any('Duplicate' in error for error in errors))
        self.assertTrue(any('missing limitations' in error for error in errors))

    def test_untrusted_markup_is_escaped_and_outside_sections_preserved(self):
        data = copy.deepcopy(self.data)
        data['releases'][0]['changes'] = ['<script>alert("x")</script> & details about stale invitations']
        rendered = history.render_html(data)
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)
        index = self.root/'site/NodeLift/index.html'
        index.write_text('before\n'+history.START+'REPLACE_ME_HISTORY_FIXTURE_987'+history.END+'\nafter')
        generated = history.outputs(data, self.root)[index]
        self.assertTrue(generated.startswith('before\n'))
        self.assertTrue(generated.endswith('\nafter'))
        self.assertNotIn('REPLACE_ME_HISTORY_FIXTURE_987', generated)
        self.assertIn('stale invitations', generated)
        index.write_text('missing markers')
        with self.assertRaises(ValueError): history.outputs(data, self.root)


if __name__ == '__main__':
    unittest.main()
