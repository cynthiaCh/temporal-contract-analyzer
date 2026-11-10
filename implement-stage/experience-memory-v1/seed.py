"""Import three declared historical versions offline; never run experiments."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from temporal_contract_analyzer import experience_memory as memory
from temporal_contract_analyzer.core import sha


def main():
    store = ROOT/'experience-memory'
    if not store.exists():
        memory.initialize(store)
    english = ROOT/'research/experience-toolflow-english-20261109_213420'
    recent = ROOT/'research/review-confirmation-lowpass-train-test-20261109_225210'
    registry = english/'frozen-library.json'
    source_jobs = [
        dict(registry=registry, label='T1', id='subscription-retirement',
             review=english/'experience/T1/translation-review.json',
             extra=[english/'translation-lineage.json',
                 ROOT/'research/transfer-progress-crosslang-test-20261109_110859/experience/experience-object.json',
                 ROOT/'research/transfer-progress-crosslang-test-20261109_110859/experience/semantic-review.json'],
             notes=['English translation, not newly trained or effect-validated wording.']),
        dict(registry=registry, label='T4', id='paused-shared-work',
             review=english/'experience/T4/translation-review.json',
             extra=[english/'translation-lineage.json',
                 ROOT/'research/query-headroom-reuse-pilot-20261109_141850/development/experience-object.json',
                 ROOT/'research/query-headroom-reuse-pilot-20261109_141850/development/semantic-review.json',
                 ROOT/'research/query-headroom-reuse-pilot-20261109_141850/training/evidence-ledger.json'],
             notes=['English translation, not newly trained or effect-validated wording.']),
        dict(registry=recent/'frozen-library.json', label='T3', id='deferred-boundary-binding',
             review=recent/'development/semantic-review.json',
             extra=[recent/'development/experience-object.json', recent/'training/evidence-ledger.json',
                    recent/'development/admission.json', recent/'development/comparisons.json'],
             notes=['Existing source batch stopped before test maintenance; import does not resume it.',
                    'Original model rule metadata and unknowns are preserved in the source object.'])
    ]
    imported = []
    before = {}
    for job in source_jobs:
        paths = [job['registry'], job['review']]+job['extra']
        for path in paths:
            before[str(path.relative_to(ROOT))] = sha(path.read_bytes())
        registry_value = json.loads(job['registry'].read_text())
        matches = [entry for entry in registry_value if entry['primary_class'] == job['label']]
        if len(matches) != 1:
            raise ValueError('Ambiguous declared seed')
        payload = memory.legacy_payload(matches[0], job['id'], job['registry'], job['review'],
            job['extra'], admitted=True, notes=job['notes'])
        if job['label'] == 'T3':
            code = sha((recent/'development/experience-object.json').read_bytes())
            payload['audit']['rule_links'] += [dict(rule_id=f'R{i+1:02d}', source_sha256=code,
                pointer=f'/rules/{i}') for i in range(len(payload['rules']))]
            result_code = sha((recent/'development/comparisons.json').read_bytes())
            payload['audit']['outcome_refs'] = [dict(source_sha256=result_code, pointer='')]
        else:
            payload['review']['limitations'].append('English translation has no direct repair-effect validation.')
        proposed = memory.seal(payload)
        existing = [b for b in memory.records(store) if b['id'] == proposed['id'] and b['version'] == proposed['version']]
        if existing:
            assert existing == [proposed], 'Existing seed differs; never overwrite'
            bundle = existing[0]
        else:
            bundle = memory.add(store, payload, paths)
        assert memory.render(bundle) == matches[0]['text']
        assert bundle['body_sha256'] == matches[0]['text_sha256']
        assert bundle['requires'] == matches[0]['requires'] and bundle['excludes'] == matches[0]['excludes']
        imported.append(dict(id=bundle['id'], sha256=bundle['sha256'], body_sha256=bundle['body_sha256'],
                             source_entry_sha256=matches[0]['sha256'], rules=len(bundle['rules'])))
    assert all(sha((ROOT/p).read_bytes()) == code for p, code in before.items())
    report = dict(origin='deterministic_historical_import_not_new_model_output', model_calls=0,
                  original_sources_unchanged=True, sources=before, imports=imported,
                  snapshot=memory.snapshot(memory.records(store)))
    output = Path(__file__).with_name('IMPORT.json')
    if output.exists():
        assert json.loads(output.read_text()) == report
    else:
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(imported=len(imported), original_sources_unchanged=True)))


if __name__ == '__main__':
    main()
