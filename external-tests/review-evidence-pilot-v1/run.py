#!/usr/bin/env python3
"""Fixed prompt-only measurements; never execute subject code through the model."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
INSTRUCTION = '''Review the six independent before/after code-change tasks below.
Use only the supplied text. Do not use tools, external knowledge, or execute code.
Judge each task only over its stated contract and finite permitted scenarios.
Answer two different questions: does the change introduce a violation absent before,
and does the after version have any violation (including a pre-existing residual one)?
No means no violation in the supplied finite domain, never universal safety.
Provide exactly one answer per task using the output schema. For your witness choose
a scenario that demonstrates a newly introduced violation if one exists; otherwise
choose a residual after violation if one exists; otherwise choose a relevant supplied
scenario. Supply exact before/after callback counts and operation outcomes for it.
Counts are ordered by listener registration or a single callback. Event outcome
arrays are empty; promise calls use 'returned', not 'fulfilled'.
Cite source lines as before:L123 or after:L123. Evidence references may be REQ-1,
SMOKE, S1/S2, or OBS-S1-before/OBS-S1-after etc only when supplied. Distinguish
inferred source behavior from observed execution. Explain the causal order briefly.
If insufficient information, choose uncertain. Output only the required JSON.
'''


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run(spec):
    replicate, arm = spec
    folder = HERE / 'run-01' / f'r{replicate}-{arm}'
    folder.mkdir(parents=True, exist_ok=False)
    order = json.loads((HERE / 'TASK_ORDER.json').read_text())
    if replicate == 2:
        order.reverse()
    prompt = INSTRUCTION + '\n\n'.join((HERE / 'tasks' / task / f'{arm}.txt').read_text() for task in order)
    (folder / 'prompt.txt').write_text(prompt)
    command = json.loads((HERE / 'smoke-03-command.json').read_text())
    command[command.index('--output-schema') + 1] = str(HERE / 'OUTPUT_SCHEMA.json')
    command[command.index('--output-last-message') + 1] = str(folder / 'answer.json')
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='callback-review-') as work:
        command[command.index('-C') + 1] = work
        dump(folder / 'command.json', command)
        with (folder / 'events.jsonl').open('w') as out, (folder / 'stderr.txt').open('w') as err:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                       text=True, start_new_session=True)
            try:
                process.communicate(prompt, timeout=240)
                timeout = False
            except subprocess.TimeoutExpired:
                timeout = True
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=15)
    events = [json.loads(line) for line in (folder / 'events.jsonl').read_text().splitlines() if line.strip()]
    allowed = {'agent_message', 'reasoning', 'error'}
    unexpected = [event for event in events if event.get('item', {}).get('type') not in allowed
                  and event.get('type', '').startswith('item.')]
    usage = [event['usage'] for event in events if event.get('type') == 'turn.completed']
    status = dict(replicate=replicate, arm=arm, exit_code=process.returncode, timeout=timeout,
                  elapsed_seconds=round(time.monotonic() - start, 3),
                  unexpected_items=unexpected, usage=usage,
                  answer_present=(folder / 'answer.json').exists(),
                  requested_model='gpt-6.1-sol', requested_reasoning_effort='low')
    dump(folder / 'status.json', status)
    print(json.dumps(status), flush=True)
    return status


if __name__ == '__main__':
    # Two concurrent independent completions; no model is given tools or a coding task.
    specs = [(replicate, arm) for replicate in [1, 2] for arm in ['A', 'B', 'C']]
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(run, specs))
    dump(HERE / 'run-01' / 'STATUS.json', statuses)
