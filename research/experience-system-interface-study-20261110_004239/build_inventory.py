"""Read-only historical projections. No experiment modules are imported."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CURRENT = 'research/review-confirmation-lowpass-train-test-20261109_225210/'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


# JSON pointers select actual data; they never rewrite model claims or policies.
SPECS = [
    ('ast', CURRENT+'materials/D/ast.json', ['']),
    ('analysis', CURRENT+'derived/D/analysis.json', ['/contract', '/primary_class', '/facts']),
    ('feedback', CURRENT+'training/feedback.json', ['/schema', '/runs/0/relations/0', '/runs/0/improvements', '/runs/0/regressions', '/runs/0/unknown', '/causal_status']),
    ('ledger', CURRENT+'training/evidence-ledger.json', ['/schema', '/entries/0', '/constraints/0', '/verified_causes']),
    ('reflection-rule', CURRENT+'development/raw-rule-revision.json', ['/rules/0', '/unresolved']),
    ('composed-experience', CURRENT+'development/experience-object.json', ['/version', '/requires', '/excludes', '/applicability', '/rules/0']),
    ('semantic-review', CURRENT+'development/semantic-review.json', ['/reviewer', '/AI_assisted', '/independent_human_approval', '/confirmed_unsupported_policy', '/limitations']),
    ('registry', CURRENT+'frozen-library.json', ['/0/version', '/0/primary_class', '/0/requires', '/0/excludes', '/0/text_sha256', '/0/sha256']),
    ('usage', CURRENT+'runs/session-02/archive/usage.json', ['']),
    ('runner-receipt', CURRENT+'runs/session-02/archive/receipt.json', ['']),
    ('stop', CURRENT+'stop.json', ['']),
    ('route-fallback', 'research/direct-experience-routing-test-20261109_162302/testing/route.json', ['']),
    ('route-hit', 'research/query-contract-qualifier-test-v2-20261109_151246/testing/route.json', ['']),
]


def pointer(value, path):
    for key in path.split('/')[1:] if path else []:
        key = key.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def main():
    manifest = []
    for name, source, pointers in SPECS:
        path = ROOT/source
        data = json.loads(path.read_text())
        selected = {p: pointer(data, p) for p in pointers}
        output = 'samples/'+name+'.json'
        write(output, dict(status='program_derived_projection_of_historical_actual',
                           source=source, source_sha256=sha(path),
                           selection='exact JSON pointer values; no semantic rewriting',
                           values=selected))
        saved = json.loads((OUT/output).read_text())
        assert saved['values'] == {p: pointer(data, p) for p in pointers}
        manifest.append(dict(source=source, sha256=sha(path), sample=output, pointers=pointers))

    additional = [
        CURRENT+'development/experience.md', CURRENT+'development/AUTO-prompt.md',
        CURRENT+'development/revalidation-prompt.md', CURRENT+'training/reflection-prompt.md',
        CURRENT+'materials/D/preanalysis-prompt.md', CURRENT+'runs/session-02/archive/input/actual-prompt.md',
        CURRENT+'runs/session-02/archive/patch.diff', CURRENT+'runs/session-02/archive/agent-messages.json',
        CURRENT+'runs/session-02/archive/score/result.json',
        CURRENT+'training/inputs/task.md', CURRENT+'reflection.schema.json',
        CURRENT+'study.py', CURRENT+'toolflow.py',
        'temporal_contract_analyzer/rag.py', 'temporal_contract_analyzer/taxonomy.py',
        'temporal_contract_analyzer/experience_routing.py', 'temporal_contract_analyzer/experience_workbench.py',
        'temporal_contract_analyzer/reminders.py',
    ]
    # The score filename is recorded from the archive, not guessed or recomputed.
    score_dir = ROOT/(CURRENT+'runs/session-02/archive/score')
    additional = [p for p in additional if not p.endswith('/score/result.json')]
    additional += [str(p.relative_to(ROOT)) for p in sorted(score_dir.rglob('*')) if p.is_file()]
    for source in additional:
        path = ROOT/source
        assert path.is_file(), source
        manifest.append(dict(source=source, sha256=sha(path), bytes=path.stat().st_size,
                             sample=None, selection='reference only; not copied or re-executed'))

    # Recheck every source after projection. Historical inputs must remain unchanged.
    assert all(sha(ROOT/row['source']) == row['sha256'] for row in manifest)
    write('sources.json', dict(kind='observed_source_manifest', files=manifest))
    write('integrity.json', dict(projection_checks=len(SPECS), source_checks=len(manifest),
                                all_passed=True, model_calls=0, scoring_calls=0,
                                historical_files_written=0, production_files_written=0))
    print(json.dumps(dict(projections=len(SPECS), sources=len(manifest), all_passed=True)))


if __name__ == '__main__':
    main()
