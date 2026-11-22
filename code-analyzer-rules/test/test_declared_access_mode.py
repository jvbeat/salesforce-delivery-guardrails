"""Runs the declared access mode rules against the fixtures and checks every flagged line.

Requires the Salesforce CLI with the code-analyzer plugin and Java 11 or later. Without
the CLI the test is skipped, so the hook tests keep running on a plain Python install.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RULESET = os.path.normpath(os.path.join(HERE, '..', 'declared-access-mode.xml'))
FIXTURES = os.path.join(HERE, 'fixtures')
RULES = ('SoqlWithoutAccessMode', 'DatabaseCallWithoutAccessLevel')

EXPECTED = {
    ('SoqlFlagged.cls', 'SoqlWithoutAccessMode'): 3,
    ('DatabaseFlagged.cls', 'DatabaseCallWithoutAccessLevel'): 5,
}


@unittest.skipUnless(shutil.which('sf'), 'Salesforce CLI not installed')
class DeclaredAccessModeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        config = os.path.join(cls.tmp, 'code-analyzer.yml')
        # Absolute path: the plugin does not resolve custom_rulesets the same way in every
        # version, and a relative path that works locally failed in CI.
        with open(config, 'w', encoding='utf-8') as f:
            f.write('engines:\n'
                    '  flow:\n    disable_engine: true\n'
                    '  eslint:\n    disable_engine: true\n'
                    '  pmd:\n    custom_rulesets:\n'
                    f'      - "{RULESET}"\n')
        output = os.path.join(cls.tmp, 'result.json')
        subprocess.run(
            ['sf', 'code-analyzer', 'run', '--config-file', config,
             '--rule-selector', ','.join(f'pmd:{r}' for r in RULES),
             '--target', FIXTURES, '--output-file', output],
            check=False, capture_output=True, text=True)
        with open(output, encoding='utf-8') as f:
            cls.violations = json.load(f)['violations']

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_no_engine_error(self):
        errors = [v for v in self.violations if v['rule'] not in RULES]
        self.assertEqual(errors, [], 'the ruleset did not load cleanly')

    def test_shipped_severity_is_moderate(self):
        # PMD priority 3 is reported as severity 3 (Moderate). Priority 1 is the only
        # value that reaches High (severity 2); priority 2 is still Moderate.
        severities = {v['severity'] for v in self.violations if v['rule'] in RULES}
        self.assertEqual(severities, {3})

    def test_counts_per_fixture(self):
        found = Counter((os.path.basename(v['locations'][0]['file']), v['rule'])
                        for v in self.violations)
        self.assertEqual(dict(found), EXPECTED)


if __name__ == '__main__':
    unittest.main()
