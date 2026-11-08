"""Rebuild evidence artifacts from a finite training-only allowlist, offline."""
import json
import shutil
import subprocess
from pathlib import Path
from handoff import digest, object_digest, assemble_payload, INSTRUCTIONS

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
OLD = REPO / 'research/two-class-experience-pilot-v2r5-20261108_223418'


def save(name, value):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def reflection_schema(old):
    def obj(properties):
        return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}
    def arr(items, minimum=0, maximum=30):
        return {'type': 'array', 'items': items, 'minItems': minimum, 'maxItems': maximum}
    short = {'type': 'string', 'minLength': 1, 'maxLength': 80}
    text = {'type': 'string', 'minLength': 1, 'maxLength': 1200}
    ids = arr(short)
    rule = obj({'id': short, 'quote': text, 'support': arr(short, 1), 'conditions': arr(short, 1),
                'preserve': arr(short, 1), 'counterevidence': ids, 'counterevidence_resolution': text,
                'causal_status': {'type': 'string', 'enum': ['documented_relation', 'source_reasoning', 'hypothesis']}})
    unresolved = obj({'statement': text, 'impact': {'type': 'string', 'enum': ['applicability', 'policy', 'scope_limit']}})
    return obj({'text': {'type': 'string', 'minLength': 1, 'maxLength': 3600},
                'requires': old['properties']['requires'], 'excludes': old['properties']['excludes'],
                'rules': arr(rule, 1, 16), 'unresolved': arr(unresolved, 0, 16)})


def main():
    provenance = []
    files = {}
    def copy(old, new, role, category='reused_unmodified'):
        src, dest = OLD / old, ROOT / new
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        h = digest(dest.read_bytes())
        provenance.append({'source': str(src.relative_to(REPO)), 'destination': new,
                           'sha256': h, 'handling': category})
        if role:
            files[new] = {'role': role, 'sha256': h}
    copy('materials/D1/task.md', 'inputs/task.md', 'training_task')
    copy('materials/D1/candidate/README.md', 'inputs/README.md', 'training_document')
    copy('materials/D1/candidate/src/session.js', 'inputs/original.js', 'training_source')
    copy('derived/D1/automatic-contract.md', 'inputs/automatic-contract.md', 'training_contract')
    copy('materials/D1/standards.json', 'inputs/standards.json', 'training_standard')
    copy('materials/D1/evaluation/recovery-rubric.json', 'inputs/rubric.json', 'training_standard')
    copy('calibration/D1/original/stdout.json', 'inputs/original-score.json', 'training_score')
    for n in (1, 2):
        base = f'reused-runs/D1-AUTO-v2r4-{n}/archive/'
        for src, dest, role in [('score/stdout.json', 'score.json', 'training_score'),
                                ('patch.diff', 'patch.diff', 'training_patch'),
                                ('raw-answer.txt', 'public-delivery.txt', 'training_public_delivery'),
                                ('final-candidate/src/session.js', 'final.js', 'training_source')]:
            copy(base + src, f'inputs/auto{n}/{dest}', role)
    # Audit evidence is intentionally outside the reflection allowlist.
    for name in ['experience-candidate.json', 'experience-original.md',
                 'candidate-semantic-review.json', 'reflection-input/feedback.json']:
        copy('development/' + name, 'audit/old/' + name, None)
    copy('structured.py', 'audit/original-structured.py', None)
    copy('feedback_v2.py', 'audit/original-feedback_v2.py', None)
    copy('reflection.schema.json', 'audit/original-reflection.schema.json', None)
    save('reflection.schema.json', reflection_schema(json.loads((OLD / 'reflection.schema.json').read_text())))
    validator = (OLD / 'structured.py').read_text().split('def validate', 1)[1].split('\ndef parse_response', 1)[0]
    (ROOT / 'schema_validator.py').write_text('"""Unmodified validate function extracted from provenance-pinned structured.py."""\n' + 'def validate' + validator)
    entries = []
    def lines(eid, kind, statement, file, start, end, related=()):
        quote = '\n'.join((ROOT / file).read_text().splitlines()[start-1:end])
        entries.append({'id': eid, 'kind': kind, 'statement': statement,
                        'author': 'execution_agent_source_review', 'related': list(related),
                        'anchors': [{'type': 'lines', 'file': file, 'start': start, 'end': end, 'quote': quote}]})
    def observation(eid, statement, file, path, value):
        entries.append({'id': eid, 'kind': 'observed_result', 'statement': statement,
                        'author': 'python_score_extraction', 'related': [],
                        'anchors': [{'type': 'json', 'file': file, 'pointer': path, 'value': value}]})
    lines('R-task', 'documented_requirement', 'The target concerns a fresh online-mode query created and removed offline; preserve supported behavior.', 'inputs/task.md', 1, 1)
    lines('F-ownership', 'source_fact', 'The getter sets the shared query consumption record but returns the current attempt controller. These are different storage owners.', 'inputs/original.js', 9, 9)
    lines('F-boundary', 'source_fact', 'Last-observer removal reads the shared consumption record; cancellation and retry suppression take different branches.', 'inputs/original.js', 12, 12)
    lines('F-events', 'source_fact', 'Cancellation settles the attempt, restores previous state and aborts its resource; active identity gates completion.', 'inputs/original.js', 7, 10)
    lines('F-creation', 'source_fact', 'A new query record has a consumption flag; creating another attempt does not directly reset that query flag. Actual invocation resets it.', 'inputs/original.js', 9, 11)
    lines('R-background', 'documented_requirement', 'Unconsumed active shared work may finish after view departure; consumed work is abortable; canceled late fulfillment must not become new-attempt data.', 'inputs/README.md', 12, 16)
    lines('R-entry', 'documented_requirement', 'Initial entry and paused continuation differ in timing and eligibility; actual lazy reads record consumption.', 'inputs/README.md', 6, 11)
    # Review interpretations are explicitly attributed; source implementation alone
    # is not an assertion of upstream intent or a newly invented business policy.
    lines('I-preservation', 'preservation_inference', 'Task preservation plus current separate record/resource ownership gives no authority to replace shared consumption with attempt-local consumption merely because the controller is attempt-local.', 'inputs/task.md', 1, 1, ['F-ownership', 'F-boundary', 'F-creation'])
    originals = json.loads((ROOT / 'inputs/original-score.json').read_text())
    for i, effect in enumerate(['cached-paused-background', 'cached-later-consumption']):
        for run in ['original', 'auto1', 'auto2']:
            file = 'inputs/original-score.json' if run == 'original' else f'inputs/{run}/score.json'
            score = json.loads((ROOT / file).read_text())
            observation(f'O-{run}-{i}', f'{run}: actual cached behavior vector and raw checks, not a cause.', file,
                        '/schedules/' + effect, score['schedules'][effect])
    for n in (1, 2):
        file = f'inputs/auto{n}/final.js'
        source_lines = (ROOT / file).read_text().splitlines()
        matches = [i for i, text in enumerate(source_lines, 1) if text.lstrip().startswith('unsubscribe(')]
        if len(matches) != 1:
            raise ValueError('Reviewed boundary source anchor changed; no automatic diagnosis.')
        for i in matches:
            lines(f'F-patch{n}', 'source_fact', 'Final source changes the departure decision to include not-yet-started work. This is not causal isolation of all changed hunks.', file, i, i)
    entries += [
        {'id': 'H-regression', 'kind': 'hypothesis', 'author': 'execution_agent_source_reasoning',
         'statement': 'The widened not-started retirement branch plausibly explains cached-work suppression; multiple changed hunks were not independently ablated.',
         'anchors': [], 'related': ['F-patch1', 'F-patch2', 'O-auto1-0', 'O-auto2-0']},
        {'id': 'U-reflector', 'kind': 'unknown', 'author': 'execution_agent',
         'statement': 'Why the reflector chose these rules is unknown; no model-internal causal evidence exists.', 'anchors': [], 'related': []}]
    constraints = [
        {'id': 'C-ownership', 'statement': 'Do not infer consumption-record ownership from resource ownership; justify any changed preservation policy against task and source.', 'evidence': ['R-task', 'F-ownership', 'F-boundary', 'I-preservation']},
        {'id': 'C-cached', 'statement': 'An unstarted/paused label alone does not justify retiring previously successful cached background work. Account for both observed cached counterexamples.', 'evidence': ['R-task', 'R-background', 'O-original-0', 'O-auto1-0', 'O-original-1', 'O-auto2-1']},
        {'id': 'C-events', 'statement': 'Keep eligibility, actual entry, retry suppression, physical abort, settlement and late completion distinct; retain documented timing.', 'evidence': ['F-events', 'F-boundary', 'R-entry', 'R-background']}]
    ledger = {'schema': 'evidence-ledger-1', 'scope': 'training_only; already exposed same-source pilot',
              'files': files, 'entries': entries, 'constraints': constraints,
              'causal_interventions': [], 'verified_causes': [],
              'mandatory_counterevidence': ['O-auto1-0', 'O-auto2-0', 'O-auto1-1', 'O-auto2-1'],
              'feedback_inputs': {'original': 'inputs/original-score.json',
                                  'repairs': ['inputs/auto1/score.json', 'inputs/auto2/score.json'],
                                  'standards': 'inputs/standards.json'}}
    save('evidence-ledger.json', ledger)
    from handoff import rebuild_feedback
    fb = rebuild_feedback(ROOT, ledger)
    save('feedback.json', fb)
    payload = assemble_payload(ROOT, ledger, fb)
    save('reflection-input.json', payload)
    (ROOT / 'reflection-prompt.md').write_text(INSTRUCTIONS + '\nTraining payload: reflection-input.json\nOutput schema: reflection.schema.json\n')
    # Actual legacy candidate replay: preserve original bytes and reject; no new
    # model candidate, no conversion into a synthetic successful candidate.
    old = json.loads((ROOT / 'audit/old/experience-candidate.json').read_text())
    replay = {'artifact': 'audit/old/experience-candidate.json', 'text_sha256': digest(old['text'].encode()),
              'reviewer': 'execution_agent', 'new_model_output': False, 'admitted': False,
              'structural_status': 'legacy_schema_missing_rule_support_metadata',
              'issues': [
                  {'quote': '消费记录应归属于产生该取消资源的执行尝试，且保存的旧上下文读取不得改写其他尝试的记录。',
                   'evidence': ['F-ownership', 'F-boundary', 'I-preservation'],
                   'judgment': 'Unsupported normative ownership rewrite; controller owner alone does not establish consumption owner.'},
                  {'quote': '已接纳但尚未实际开始的工作，应结算并阻止其以后因环境恢复而进入执行',
                   'evidence': ['R-task', 'O-original-0', 'O-original-1', 'O-auto1-0', 'O-auto2-1'],
                   'judgment': 'Unqualified prescription does not account for the recorded cached background counterexamples.'}],
              'causal_limit': 'The exact contribution of each patch hunk and the reason for reflector error remain unverified.'}
    assert all(issue['quote'] in old['text'] for issue in replay['issues'])
    save('audit/rejected-candidate-replay.json', replay)
    save('provenance.json', {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
                            'reused': provenance, 'modified': ['feedback.py (original-success accounting when candidate actual is unknown)'],
                            'regenerated': ['feedback.json', 'evidence-ledger.json', 'reflection-input.json', 'reflection-prompt.md', 'reflection.schema.json'],
                            'new_experience_generated': False, 'model_calls': 0})
    save('summary.json', {'status': 'offline_handoff_complete_pending_checks', 'model_sessions': 0, 'model_requests': 0,
                          'new_experience_candidates': 0, 'admitted_experiences': 0,
                          'behavioral_scores_generated': 0, 'replayed_training_scores': 2,
                          'ledger_sha256': object_digest(ledger),
                          'next_step': 'A future authorized bounded reflection must satisfy evidence review and development admission; no automatic execution.'})


if __name__ == '__main__':
    main()
