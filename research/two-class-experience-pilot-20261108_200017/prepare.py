"""No-model preparation; only local AST, input snapshots and pinned calibrations."""
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
A = Path(__file__).resolve().parent
R = A.parents[1]
B = R.parent / 'temporal-contract-bench-git'
sys.path.insert(0, str(R))
from temporal_contract_analyzer.core import scan
from toolflow import extraction_prompt, public_material, digest, PREDICATES, POLICY


def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def hashes(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


def compact_ast(ast):
    return {'status': ast['status'], 'summary': ast['summary'], 'limitations': ast['limitations'],
            'files': [{'path': f['path'], 'status': f['status'], 'functions': [
                {k: v for k, v in fn.items() if k in ['name', 'line', 'start', 'end', 'parameters']}
                for fn in f['functions']][:30], 'events': [
                    {k: v for k, v in event.items() if k in ['kind', 'line', 'callee', 'target', 'text', 'tags']}
                    for event in f['events'] if event.get('tags')][:45]} for f in ast['files']],
            'findings': ast['findings'][:12]}


def main():
    assert not (A / 'cohort.json').exists(), 'no overwrite'
    t = time.monotonic()
    ids = ['query-paused-initial-fetch-10266-vanilla', 'document-submit-snapshot-vanilla',
           'query-paused-initial-fetch-10266-python3', 'document-submit-snapshot-python3-eval-v2']
    prior = R / 'research/two-class-experience-pilot-20261108_171554'
    old = json.loads((prior / 'cohort.json').read_text())
    prior_by = {c['case']: c for c in old}
    node = B / 'results/student-case-expansion-runtime/node18/bin/node'
    runtime = {}
    for name, cmd in [('node', [str(node), '--version']), ('python', ['/usr/bin/python3', '--version']),
                      ('bwrap', ['bwrap', '--version'])]:
        z = subprocess.run(cmd, text=True, capture_output=True, timeout=10)
        assert z.returncode == 0, (name, z.stderr)
        runtime[name] = {'command': cmd, 'stdout': z.stdout.strip(), 'stderr': z.stderr}
    assert Path('/home/sribd/.codex/auth.json').is_file(), 'native CLI authentication unavailable'
    taxonomy = json.loads((A / 'spec/taxonomy.json').read_text())['classes']
    cases = []
    protected = {}
    for n, cid in enumerate(ids):
        alias = ['D1', 'D2', 'T1', 'T2'][n]
        matches = list((B / 'case-clusters').glob('*/arms/' + cid + '/case.json'))
        assert len(matches) == 1
        src = matches[0].parent
        m = json.loads(matches[0].read_text())
        dest = A / 'materials' / alias
        shutil.copytree(src / 'base', dest / 'candidate')
        shutil.copytree(src / 'oracle', dest / 'evaluation')
        shutil.copyfile(matches[0], dest / 'manifest.json')
        shutil.copyfile(src / m['diagnostic_tasks']['maintenance']['core_prompt'], dest / 'task.md')
        for f in src.rglob('*'):
            if f.is_file():
                protected[str(f)] = sha(f)
        for f in (dest / 'candidate').rglob('AGENTS.md'):
            raise ValueError('unexpected candidate instructions: ' + str(f))
        before = prior_by[cid]
        assert before['oracle_sha256'] == hashes(src / 'oracle'), 'oracle version drift'
        expected_candidate = {k[len('candidate/'):]: v for k, v in before['input_sha256'].items() if k.startswith('candidate/')}
        assert expected_candidate == hashes(src / 'base'), 'candidate calibration drift'
        assert before['input_sha256']['task.md'] == sha(dest / 'task.md'), 'task version drift'
        assert before['calibration_trustworthy']
        # Copy all old raw calibration receipts/snapshots, not old outcomes to actors.
        shutil.copytree(prior / 'calibration' / cid, A / 'calibration' / alias)
        for f in (A / 'calibration' / alias).glob('*/receipt.json'):
            rec = json.loads(f.read_text())
            assert rec['score_valid'] and rec['command'][0] == str(node)
            assert rec['candidate_before'] == hashes(f.parent / 'candidate')
        source_text = {str(f.relative_to(dest / 'candidate')): f.read_text()
                       for f in (dest / 'candidate').rglob('*') if f.is_file() and f.suffix in ['.js', '.py', '.md']}
        # Only task + relative candidate content enters scan and model material.
        ast = scan(dest / 'candidate', node=str(node))
        assert ast['summary']['parsed_files'] == ast['summary']['files'] > 0, ast['adapters']
        save(dest / 'ast.json', ast)
        save(dest / 'visible-source-lines.json', {f: list(enumerate(text.splitlines(), 1)) for f, text in source_text.items()})
        material = public_material((dest / 'task.md').read_text(), source_text, compact_ast(ast), taxonomy)
        prompt = extraction_prompt(material)
        assert all(x not in prompt for x in ids), 'case identity leaked into preanalysis'
        (dest / 'preanalysis-prompt.md').write_text(prompt)
        c = {'alias': alias, 'case': cid, 'source_case': str(src), 'node': str(node),
             'role': 'train' if n < 2 else 'test', 'independent_unit_id': m['independent_unit_id'],
             'framework': m['framework'], 'provenance': m['provenance'],
             'candidate_files': hashes(dest / 'candidate'), 'task_sha256': sha(dest / 'task.md'),
             'oracle_files': hashes(src / 'oracle'), 'calibration_source': str(prior / 'calibration' / cid),
             'calibration_count': len(before['calibration']), 'calibration_version_correspondence': True,
             'AST_summary': ast['summary'], 'AST_status': ast['status'],
             'exposure': 'same-source cross-language; prior archive/source inspections and existing experiments disclosed; no unseen claim'}
        # Evaluation-only descriptions. No query-specific root-cause generator.
        effects = json.loads((dest / 'evaluation/effects.json').read_text())
        rules = effects['variants']['ungranted']
        descriptions = {x['id']: x['description'] for x in effects['effects']}
        standards = [{'effect': k, 'expected': k in rules['required'], 'description': descriptions[k],
                      'policy_support': 'original task + candidate README/docs + existing source preservation; execution-agent reviewed',
                      'evaluator_interpretation_only': True}
                     for k in rules['required'] + rules['forbidden']]
        save(dest / 'standards.json', standards)
        cases.append(c)
    for name in subprocess.check_output(['git', 'ls-files', '-z'], cwd=R).decode().split('\0'):
        if name and (R / name).is_file():
            protected[str(R / name)] = sha(R / name)
    save(A / 'protected-files.json', protected)
    save(A / 'cohort.json', cases)
    save(A / 'runtime-check.json', runtime)
    save(A / 'exposure.json', {'previous_blocked_run': str(prior), 'new_HEAD': json.loads((A / 'initial-state.json').read_text())['HEAD'],
                             'all_cases_exposed_to_current_execution_agent': True,
                             'same_source_pairs': [[cases[0]['case'], cases[2]['case']], [cases[1]['case'], cases[3]['case']]],
                             'T2_posthoc_v2_disclosed': cases[3]['provenance']['abstraction_notes'],
                             'old_E2_not_given_to_learner': True})
    rng = random.Random(2026110804)
    slots = []
    for alias in ['T1', 'T2']:
        for block in [1, 2]:
            arms = ['A', 'B']
            rng.shuffle(arms)
            for arm in arms:
                slots.append({'slot': f'{alias}-block-{block}-{arm}', 'phase': 'repair',
                              'alias': alias, 'block': block, 'condition': 'AUTO' if arm == 'A' else 'ROUTED', 'arm': arm})
    save(A / 'schedule.json', {'seed': 2026110804, 'controls_sampling': False, 'slots': slots,
                              'algorithm': 'Python random.Random(seed), shuffle A/B within fixed case/repetition blocks'})
    save(A / 'preanalysis.schema.json', {'envelope': {'report': 'JSON string <=6000 chars'},
         'parsed_fields': ['contract', 'primary_class', 'secondary_tags', 'evidence', 'facts'],
         'classes': ['T1', 'T2', 'T3', 'T4', 'unknown'], 'states': ['known', 'unknown', 'contradicted'],
         'predicate_definitions': PREDICATES, 'validation': 'toolflow.validate_analysis; literal source evidence required'})
    save(A / 'prepare-receipt.json', {'seconds': time.monotonic() - t, 'model_calls': 0,
         'calibrations_reused': sum(c['calibration_count'] for c in cases), 'source_versions_exact': True,
         'all_four_AST_parsed': True, 'prior_calibration_is_not_training': True})
    (A / 'policy-review.md').write_text('''# Execution-agent policy and evaluation adapter review

This is an AI execution-agent review, not fabricated human approval. Original tasks, candidate README/docs and current source are the policy basis. Original ungranted effect descriptions and rubrics are evaluation-only structured data, not repair guidance. The full source-bound documents are numbered in materials/*/visible-source-lines.json.

Query task expressly prohibits a fresh offline-mounted/detached query from entering its consuming function with a live signal after reconnect, independently of reconnect-refetch policy. README preserves unconsumed active work, shared observers, per-attempt cancellation/completion, revert/settlement and late-result exclusion. In the existing JS invoke, lazy signal access writes the shared query consumption state but returns the attempt's controller; reset is at actual entry. subscribe constructs a new attempt without resetting the shared consumption flag. Preserving this existing distinction supports the prior-consumption and retained-context scoring relations; it is not inferred from unused per-attempt fields or from a reference patch. The Python port has the corresponding current-source distinction. Cached/success work differs from a fresh pending/paused attempt; cancellation must not blanket-cancel every orphan or all keys. Unspecified upstream equivalence remains unknown.

Document task requests 120ms trailing batching while preserving other behavior and excluding preview changes. README and T2 host-api specify departed accepted text readable before navigation returns, synchronous store callbacks which may navigate/edit, later-starting navigation priority, entry-bound immutable accepted receipts, and visit-bound notices. Therefore boundary settlement, retained accepted receipts and suppression of retired UI effects have visible support; preview keeps its own 40ms/discard/reuse policy. These policies are not added merely because the evaluator asserts them.

Original rubric/effect wording is retained in evaluation snapshots. Generic feedback computes boolean deltas and failed actual/expected assertions without manufacturing causes. Any additional causal interpretation is explicitly attributed and must cite actual code/patches. No human approval marker is required when current visible documentation/source suffices.

Runtime discrepancy: manifest JS declares Node16; actual existing calibration/runtime is Node18.17.0, disclosed rather than claiming exact Node16 reproduction. Python3.8.10 matches the manifests. Reused calibration covers all original/reference/noop/mutant variants with exact base/task/oracle digests, current receipts and complete raw vectors. No scoring rule has changed.
''')
    print('PREPARED', A, flush=True)


if __name__ == '__main__':
    main()
