"""Qoder tool gate; model-turn counts come from CLI results, never synthetic hooks."""
import json
import sys

from guard_client import forward


if __name__ == '__main__':
    try:
        event = json.load(sys.stdin)
        if event.get('hook_event_name') != 'PreToolUse':
            raise ValueError('Unexpected Qoder hook event')
        event['tool_input'] = dict(event.get('tool_input') or {}, workdir=event.get('cwd', '/workspace'))
        # A redundant absolute workspace prefix changes no read permissions.
        command = event['tool_input'].get('command')
        if isinstance(command, str) and command.startswith('cd /workspace && '):
            event['qoder_original_command'] = command
            event['tool_input']['command'] = command[len('cd /workspace && '):]
        decision = forward(event)
        if decision.get('deny'):
            print('Tool denied by the training role policy', file=sys.stderr)
            sys.exit(2)
    except Exception as error:
        print('Training tool gate failed: '+str(error), file=sys.stderr)
        sys.exit(2)
    print('{}')
