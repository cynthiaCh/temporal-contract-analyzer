"""Freeze the existing D1 condition and an R03-only revision request, offline."""
import json
import sys
import time
from pathlib import Path
sys.dont_write_bytecode = True
A = Path(__file__).resolve().parent
sys.path.insert(0, str(A))
from archive import save, sha, inventory
from handoff import assemble_payload, verify_ledger, make_schema, render, object_digest
from evolution import revision_schema
from toolflow import PREDICATES, maintenance_prompt
import runner


def read(path):
    return json.loads(Path(path).read_text())


def main():
    assert not (A / 'prepared.json').exists()
    started = time.time()
    case = read(A / 'case.json')
    assert case['case'] == 'query-paused-initial-fetch-10266-vanilla'
    assert runner.backend.hashes(A / 'candidate') == case['candidate_files']
    assert sha(A / 'task.md') == case['task_sha256']
    assert runner.backend.hashes(Path(case['source_case']) / 'oracle') == case['oracle_files']
    common = maintenance_prompt((A / 'task.md').read_text(), (A / 'automatic-contract.md').read_text())
    assert common == (A / 'AUTO-prompt.md').read_text()
    for n in (1,2):
        root = A / f'baselines/auto{n}/archive'
        record, config = read(root / 'receipt.json'), read(root / 'input/config.json')
        assert record['scoring_admissible'] and record['score_result']['score_valid'] and record['scored_candidate_unchanged']
        assert inventory(root / 'input/original') == inventory(A / 'candidate')
        assert (root / 'input/actual-prompt.md').read_text() == common
        assert sha(root / 'score/stdout.json') == sha(A / f'inputs/auto{n}/score.json')
        assert read(root / 'score/receipt.json')['oracle_sha256'] == case['oracle_files']
        assert config['model']=='gpt-5.6-terra' and config['effort']=='low'
        assert config['requests_per_session']==24 and config['seconds_per_session']==600
    parent = read(A / 'parent/candidate-experience.json')
    ledger = read(A / 'evidence-ledger.json')
    verify_ledger(A, ledger)
    assert len(parent['rules']) == 5 and parent['rules'][2]['category'] == 'verification'
    assert render(parent) == (A / 'parent/candidate-experience.md').read_text()
    assert make_schema(ledger, PREDICATES) == read(A / 'parent/reflection.schema.json')
    save(A / 'candidate.schema.json', make_schema(ledger, PREDICATES))
    save(A / 'reflection.schema.json', revision_schema(ledger, PREDICATES))
    review = read(A / 'parent/semantic-review.json')
    payload = {'training': assemble_payload(A, ledger, read(A / 'feedback.json')),
       'parent_candidate': parent, 'mechanism_predicates': PREDICATES,
       'r03_rejection': next(r for r in review['rules'] if r['id']=='R03'),
       'training_policy_check': read(A / 'parent/training-policy-check.json'),
       'parent_other_rules_review_AI_assisted': [r for r in review['rules'] if r['id']!='R03'],
       'scope': 'Only replace the R03 rule object. Keep all other rule objects, mechanism fields and unresolved list byte-for-byte equivalent as parsed values.'}
    save(A / 'reflection-input.json', payload)
    prompt = '''Revise ONLY parent rule R03. Return exactly ONE rule object matching
the supplied existing rule schema: category, body, support, conditions, preserve,
counterevidence, explanation, causal_status. No wrapper, IDs, full experience,
quotes, other rules or extra alternatives. No tools, retry or human rewriting.
Keep category verification. Python will replace only the third parent rule and
render all five exact bodies; the other four rules and all mechanism fields
remain unchanged. Do not revise unresolved items in this bounded operation.

Correct the parent's stronger-than-supported verification boundary. The target
for the fresh uncached online-mode request removed offline is that reconnection
must not enter with a still-live signal. Both absence of entry and entry with an
already-aborted signal are allowed for that target; zero entry is not the sole
correct implementation policy. Neither option proves the complete repair is
correct: separately preserve lawful cached background refresh, later consumption,
entered unconsumed work, settlement/state handling, observers and other behavior.
Do not infer all observerless work must cancel, or that a multi-change patch has
isolated the cause. Preserve the current separate consumption-record and
attempt-controller ownership without inventing a migration/reset policy.

The parent did cite task/docs in conditions; do not falsely say it had none.
Its support field held only observations. Correct field placement using IDs
that actually support the revised meaning. support itself must include at least
one genuinely relevant documented requirement/source/preservation-inference ID;
conditions contains evidence IDs supporting applicability, preserve constraint
IDs, counterevidence actual ledger IDs. Explanations belong in explanation.
All enums are from the frozen ledger. Existing evidence is not automatically
entailment; be precise about event order, conditions, negation and uncertainty.

Body at most 480 characters, preferably Chinese; no case or grading IDs, code
field names, paths or copyable patches. Do not repeat the body elsewhere.
The full training payload includes source/task/docs, original and two selected
AUTO results, raw event checks, actual patches and source-grounded review. No
reference patch, old E2 or test result is supplied. Repair-agent public claims
are unverified. Prior review is AI-assisted, not independent human approval.
Complete payload:
''' + json.dumps(payload, ensure_ascii=False)
    (A / 'reflection-prompt.md').write_text(prompt)
    (A / 'reflection-task.md').write_text('Revise only R03 once using the frozen parent and D1 training evidence. No tools or other candidate.\n')
    (A / 'reflection-workspace').mkdir()
    save(A / 'reflection-workspace/payload.json', payload)
    protocol = read(A / 'parent/protocol.json')
    protocol.update(batch_kind='R03-only bounded parent evolution', parent_object_sha256=object_digest(parent),
                    allowed_modifications=['rules[2]'], no_unresolved_modification=True,
                    reflection_output='exactly one existing verification rule object',
                    composition_origin='Python copy parent and replace R03; not a full model-generated candidate')
    save(A / 'protocol.json', protocol)
    save(A / 'prepared.json', {'time':time.time(), 'offline_setup_seconds':time.time()-started, 'model_requests':0})
    print('Prepared R03-only request; parent full schema and baseline conditions unchanged', flush=True)


if __name__ == '__main__': main()
