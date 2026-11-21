"""Qoder tool gate; model-turn counts come from CLI results, never synthetic hooks."""
import json
from pathlib import Path
import shlex
import sys

from guard_client import forward


def guard_event(value, workspace=Path('/workspace')):
    event = dict(value)
    if event.get('hook_event_name') != 'PreToolUse':
        raise ValueError('Unexpected Qoder hook event')
    original = dict(event.get('tool_input') or {})
    event['tool_input'] = dict(original, workdir=event.get('cwd', '/workspace'))
    name = event.get('tool_name')
    if name == 'Read':
        filename = original.get('file_path')
        if not isinstance(filename, str) or not filename:
            raise ValueError('Read requires a public workspace file path')
        root = workspace.resolve()
        file = (root/filename).resolve()
        relative = file.relative_to(root)
        if file.exists() and not file.is_file():
            raise ValueError('Read requires a regular public workspace file')
        event['qoder_original_tool'] = name
        event['qoder_original_input'] = original
        # Authorize the equivalent source read through the existing host ledger.
        # No updatedInput is returned: Qoder still executes its original Read.
        event['tool_name'] = 'Bash'
        event['tool_input']['command'] = 'cat -- '+shlex.quote('./'+relative.as_posix())
    elif name != 'Bash':
        raise ValueError('Tool is not enabled for this testing/training workspace')
    # A redundant absolute workspace prefix changes no read permissions.
    command = event['tool_input'].get('command')
    if isinstance(command, str) and command.startswith('cd /workspace && '):
        event['qoder_original_command'] = command
        event['tool_input']['command'] = command[len('cd /workspace && '):]
    return event


if __name__ == '__main__':
    original_event = None
    try:
        original_event = json.load(sys.stdin)
        event = guard_event(original_event)
        decision = forward(event)
        if decision.get('deny'):
            print('Tool denied by the training role policy', file=sys.stderr)
            sys.exit(2)
    except Exception as error:
        if isinstance(original_event,dict) and original_event.get('tool_name') in ('Read','Bash'):
            try:
                forward(dict(original_event,qoder_guard_denied=True))
            except Exception:
                pass  # The CLI still receives a blocking exit; missing ledger proof fails the stage.
        print('Training tool gate failed: '+str(error), file=sys.stderr)
        sys.exit(2)
    print('{}')
