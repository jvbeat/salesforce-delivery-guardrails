#!/usr/bin/env python3
"""Mechanical guard for `sf` commands run by Claude Code (Bash hook).

A rule written in prose is not consulted at command time. This script checks the
Salesforce CLI pitfalls at the moment the agent is about to run the command.

PreToolUse: blocks deploy, retrieve, apex run/test, org assign, data (query, import,
delete...) and sobject describe without --target-org or -o. Anyone serving several
clients tends to have a global default org pointing at another client, and a command
without an explicit target lands there.

PostToolUse: after a deploy or a describe, returns the reminder that matches what
went up (a permission set is not assigned by deploying it, a Flow deploys as Draft,
a new field deploys without FLS, describe is filtered by the session user's FLS).
"""
import json
import re
import sys

NEEDS_TARGET = re.compile(r'\bsf\s+(project\s+(deploy|retrieve)|apex\s+(run|test)|org\s+assign|data\s+\w+|sobject\s+describe)\b')
HAS_TARGET = re.compile(r'(^|\s)(-o|--target-org)(\s|=)')


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if payload.get('tool_name') != 'Bash':
        return 0
    cmd = (payload.get('tool_input') or {}).get('command', '') or ''
    event = payload.get('hook_event_name', '')
    if not re.search(r'\bsf\s', cmd):
        return 0

    if event == 'PreToolUse':
        if NEEDS_TARGET.search(cmd) and not HAS_TARGET.search(cmd):
            print(json.dumps({'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': 'sf without --target-org: the command would land on the global default org, which may belong to another client. Run it again with -o <alias>.'}}))
        return 0

    if event == 'PostToolUse':
        reminders = []
        if re.search(r'sf\s+project\s+deploy', cmd):
            if re.search(r'permissionset|PermissionSet', cmd):
                reminders.append('Deploying a permission set does not assign it: run sf org assign permset -n <name> -o <alias>, or the deploying user will not see custom fields and the test suite will fail on permissions.')
            if re.search(r'\bflows?\b|\bFlow\b', cmd):
                reminders.append('A deployed Flow lands as Draft and the previous version stays active: activate it through FlowDefinition (activeVersionNumber).')
            if re.search(r'\bfields?\b|CustomField|objects/', cmd):
                reminders.append('A new field deploys without FLS: it exists, sits on the layout and does not show. Grant FLS in a permission set and assign it.')
            reminders.append('A failed deploy rolls back the whole batch: check what is in the org with a retrieve, not with the log.')
        if re.search(r'sf\s+sobject\s+describe', cmd):
            reminders.append("Describe answers with the session user's FLS: a field missing here is not proof it does not exist. Confirm through the Tooling API on FieldDefinition.")
        if reminders:
            print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse',
                              'additionalContext': 'sf guard: ' + ' '.join(reminders)}}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
