"""Tests for sf-guard.py: they run the hook the way Claude Code does, with the event on stdin."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).with_name('sf-guard.py')


def run(event, command):
    payload = {'hook_event_name': event, 'tool_name': 'Bash', 'tool_input': {'command': command}}
    out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                         capture_output=True, text=True, check=True).stdout.strip()
    return json.loads(out)['hookSpecificOutput'] if out else None


class PreToolUse(unittest.TestCase):
    def test_blocks_deploy_without_target(self):
        result = run('PreToolUse', 'sf project deploy start --source-dir force-app')
        self.assertEqual(result['permissionDecision'], 'deny')

    def test_blocks_data_query_without_target(self):
        result = run('PreToolUse', 'sf data query --query "SELECT Id FROM Account"')
        self.assertEqual(result['permissionDecision'], 'deny')

    def test_allows_deploy_with_short_flag(self):
        self.assertIsNone(run('PreToolUse', 'sf project deploy start --source-dir force-app -o uat'))

    def test_allows_deploy_with_long_flag_and_equals(self):
        self.assertIsNone(run('PreToolUse', 'sf project deploy start --target-org=uat'))

    def test_ignores_commands_that_do_not_touch_an_org(self):
        self.assertIsNone(run('PreToolUse', 'sf plugins install code-analyzer'))

    def test_ignores_non_sf_commands(self):
        self.assertIsNone(run('PreToolUse', 'git status'))


class PostToolUse(unittest.TestCase):
    def test_reminds_assignment_after_permission_set_deploy(self):
        result = run('PostToolUse', 'sf project deploy start -m PermissionSet:Sales -o uat')
        self.assertIn('sf org assign permset', result['additionalContext'])

    def test_reminds_activation_after_flow_deploy(self):
        result = run('PostToolUse', 'sf project deploy start -m Flow:Welcome -o uat')
        self.assertIn('Draft', result['additionalContext'])

    def test_reminds_fls_after_describe(self):
        result = run('PostToolUse', 'sf sobject describe --sobject Account -o uat')
        self.assertIn('FieldDefinition', result['additionalContext'])


if __name__ == '__main__':
    unittest.main()
