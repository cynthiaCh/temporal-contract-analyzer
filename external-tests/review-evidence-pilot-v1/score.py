#!/usr/bin/env python3
"""Score bounded decisions and observable witnesses without model judging."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    gold = {row['task_id']: row for row in json.loads((HERE / 'GOLD.json').read_text())}
    records = []
    statuses = json.loads((HERE / 'run-01/STATUS.json').read_text())
    for status in statuses:
        folder = HERE / 'run-01' / f'r{status["replicate"]}-{status["arm"]}'
        valid_call = status['exit_code'] == 0 and not status['timeout'] and not status['unexpected_items']
        answers = json.loads((folder / 'answer.json').read_text()).get('answers', []) if status['answer_present'] else []
        for task, expected in gold.items():
            matching = [answer for answer in answers if answer.get('task_id') == task]
            row = dict(replicate=status['replicate'], arm=status['arm'], task_id=task,
                       project=expected['project'], direction=expected['direction'],
                       valid_call=valid_call, missing_or_duplicate=len(matching) != 1,
                       decisions_correct=False, observable_witness_correct=False,
                       relevant_witness=False, references_valid=False, complete_correct=False)
            if valid_call and len(matching) == 1:
                answer = matching[0]
                row['uncertain'] = any(answer[key] == 'uncertain' for key in ['introduces_violation', 'after_has_violation'])
                row['decisions_correct'] = all(answer[key] == ('yes' if expected[key] else 'no')
                                               for key in ['introduces_violation', 'after_has_violation'])
                scene = answer['scenario_id']
                if scene in expected['observations']:
                    observed = expected['observations'][scene]
                    row['observable_witness_correct'] = all(answer[f'{side}_{key}'] == observed[side][key]
                                                            for side in ['before', 'after'] for key in ['counts', 'outcomes'])
                    truth = expected['scenario_truth'][scene]
                    row['relevant_witness'] = ((not truth['before'] and truth['after']) if expected['introduces_violation']
                                               else truth['after'] if expected['after_has_violation'] else True)
                allowed = set(expected['valid_refs']) | set(expected['scenario_truth'])
                if status['arm'] == 'A':
                    allowed = {ref for ref in allowed if not ref.startswith('OBS-')}
                source_refs = answer['source_refs']
                evidence_refs = answer['evidence_refs']
                row['references_valid'] = (bool(source_refs) and bool(evidence_refs)
                                            and all(ref in allowed and ':L' in ref for ref in source_refs)
                                            and all(ref in allowed and ':L' not in ref for ref in evidence_refs))
                row['complete_correct'] = all(row[key] for key in ['decisions_correct', 'observable_witness_correct',
                                                                   'relevant_witness', 'references_valid'])
            records.append(row)
    metrics = ['decisions_correct', 'observable_witness_correct', 'relevant_witness', 'references_valid', 'complete_correct']
    summary = {arm: dict(task_responses=sum(row['arm'] == arm for row in records),
                         **{metric: sum(row['arm'] == arm and row[metric] for row in records) for metric in metrics})
               for arm in ['A', 'B', 'C']}
    result = dict(summary=summary, records=records,
                  limitations=['Three previously inspected projects, six correlated directional tasks, two repeats.',
                               'No human study; no generalization or causal understanding claim.',
                               'B includes extra runtime evidence; C adds only a redundant index.',
                               'Reference validity checks existence, not semantic sufficiency.'])
    (HERE / 'run-01/SCORES.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
