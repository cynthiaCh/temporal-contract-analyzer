"""Read-only stdlib checks; no model, analyzer, oracle or experiment is executed."""
import collections
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def require(ok, message):
    if not ok:
        raise ValueError(message)

p = read(HERE / 'provenance.json')
questions = [json.loads(s) for s in (HERE / 'questions.jsonl').read_text().splitlines() if s.strip()]
required = {'id', 'title', 'contract_category', 'core_question', 'preconditions',
            'observable_clues', 'event_orders', 'source_evidence_to_seek', 'verification_methods',
            'non_applicability_and_preserved_behavior', 'common_wrong_repairs',
            'retrieval', 'evidence_status', 'applicability_scope'}
ids = [q['id'] for q in questions]
require(len(ids) == len(set(ids)), 'duplicate question ID')
require(set(ids) == set(p['questions']), 'question/provenance mismatch')
for q in questions:
    require(set(q) == required and all(q.values()), 'missing/unknown/empty fields: ' + q['id'])
    require(re.fullmatch(r'TCQ-\d{3}', q['id']), 'unstable ID form')
    require(len(q['event_orders']) >= 2, 'fewer than two orders')
    for order in q['event_orders']:
        require(len(order['sequence']) >= 2 and order['check'], 'incomplete event order')
    for repair in q['common_wrong_repairs']:
        require(repair['repair'] and repair['possible_regression'], 'incomplete repair risk')
    require(all(q['retrieval'].get(k) for k in ['zh_keywords', 'en_keywords', 'description']), 'retrieval fields')

# Only {path, sha256} objects are file references; paths resolve inside the repository.
references = {}
def walk(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            path = value['path']
            require(not Path(path).is_absolute() and '..' not in Path(path).parts, 'nonrelative evidence')
            require(path not in references or references[path] == value['sha256'], 'conflicting digest')
            references[path] = value['sha256']
        for child in value.values():
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)
walk(p)
for path, digest in references.items():
    file = ROOT / path
    require(file.is_file(), 'missing evidence: ' + path)
    require(hashlib.sha256(file.read_bytes()).hexdigest() == digest, 'changed evidence: ' + path)
for qid, proof in p['questions'].items():
    require(proof['mechanism'] and proof['limits'], 'incomplete evidence interpretation')
    require(len(proof['jobs']) >= 2, 'no contrast sample')
    for key in proof['jobs']:
        require(key in p['jobs'], 'missing linked job')
    for anchor in proof['source_anchors']:
        line = (ROOT / anchor['path']).read_text().splitlines()[anchor['line'] - 1]
        require(line == anchor['excerpt'], 'source anchor shifted')

# Bind both source and immutable scored candidate to archived inventories.
hidden_ids = set(p['split_policy']['affected_cases'])
for key, job in p['jobs'].items():
    m = read(ROOT / job['manifest']['path'])
    ev = read(ROOT / job['evaluation']['path'])
    raw = read(ROOT / job['raw_behavior']['path'])
    require(ev['calibration_verdict'] == job['calibration_verdict'] == 'PASS', 'uncalibrated evidence')
    require(raw['verdict'] == ev['jobs'][job['job']]['verdict'] == job['verdict'], 'verdict mismatch')
    for f in job['source_files']:
        marker = '/input/' if f['role'] == 'original-scored-input' else '/candidate/'
        name = f['path'].split(marker, 1)[1]
        inventory = m['input_files'] if f['role'] == 'original-scored-input' else ev['jobs'][job['job']]['candidate_files']
        require(inventory[name] == f['sha256'], 'snapshot not scored: ' + f['path'])
    hidden_ids.update(raw.get('missing_required_effects', []))
    hidden_ids.update(raw.get('observed_forbidden_effects', []))
    hidden_ids.update(raw.get('observed_effects', {}).keys())
    def collect(value):
        if isinstance(value, dict):
            # Assertions are research-only; generic trace object ids are not assertion identifiers.
            for a in value.get('assertions', []) if isinstance(value.get('assertions'), list) else []:
                if isinstance(a, dict) and isinstance(a.get('id'), str):
                    hidden_ids.add(a['id'])
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
    collect(raw)

# Recheck membership classification against execution and raw evaluation, not narrative reports.
counts = collections.Counter()
slots = set()
execution_details = []
fullrepo_no_clock = 0
for batch, scope in p['scope'].items():
    actual = collections.Counter()
    for run in scope['runs']:
        identity = (run['experiment'], run['job'])
        require(identity not in slots, 'duplicate/reused historical control counted as new call')
        slots.add(identity)
        mpath = ROOT / run['manifest']['path']
        folder = mpath.parent
        m = read(mpath)
        if 'jobs' not in m:
            result = read(folder / 'result.json')
            fullrepo_no_clock += 1
            require(result['process'] == 'completed' and result['score']['verdict'] == 'PASS', 'fullrepo unverified')
            category = 'behavior-pass'
        else:
            j = next(j for j in m['jobs'] if j['id'] == run['job'])
            if j['status'] != 'completed':
                result = read(folder / 'jobs' / run['job'] / 'result.json')
                require(not result['turn_completed'] and result['exit_code'] != 0, 'execution classification')
                category = 'execution-failure'
                execution_details.append({'experiment': run['experiment'], 'job': run['job'], 'reason': run.get('execution_errors')})
            else:
                evaluations = list((folder / 'evaluations').glob('*/summary.json'))
                require(evaluations, 'no trusted evaluation')
                evpath = max(evaluations, key=lambda f: read(f).get('completed_at', ''))
                ev = read(evpath)
                row = ev['jobs'][run['job']]
                rawpath = evpath.parent / run['job'] / 'oracle/stdout.json'
                if ev.get('calibration_verdict') != 'PASS' or not rawpath.is_file():
                    category = 'validation-unverified'
                else:
                    raw = read(rawpath)
                    execution = read(rawpath.parent / 'execution.json')
                    calibration = read(evpath.parent / 'calibration/stdout.json')
                    require(calibration['verdict'] == 'PASS', 'raw calibration disagrees')
                    require(raw['verdict'] == row['verdict'], 'raw verdict disagrees')
                    # The archived probes intentionally exit 1 for a structured semantic failure.
                    if ((raw['verdict'] == 'PASS' and execution.get('exit_code') != 0)
                            or (raw['verdict'] != 'PASS' and execution.get('exit_code') != 1)
                            or raw['verdict'] not in {'PASS', 'UNDERREACH', 'OVERREACH', 'UNDERREACH_AND_OVERREACH'}):
                        category = 'validation-unverified'
                    else:
                        category = 'behavior-pass' if raw['verdict'] == 'PASS' else 'behavior-failure'
        require(category == run['classification'], 'classification changed: ' + run['experiment'])
        actual[category] += 1
    require(dict(actual) == scope['classifications'], 'scope count mismatch')
    require(sum(actual.values()) == scope['new_calls'], 'membership count mismatch')
    counts.update(actual)

# Full Agent file scan. This is a lexical check, not semantic non-leakage certification.
agent = (HERE / 'questions.jsonl').read_text().lower()
for pattern in [r'\boracle\b', r'\breference\b', r'\bexpected\b', r'e-[0-9a-f]{12,}', r'j-\d{3}', r'/home/', r'results/', r'case-clusters/', r'\b(?:underreach|overreach)\b']:
    require(not re.search(pattern, agent), 'research-only token in Agent text: ' + pattern)
scanned = 0
for identifier in hidden_ids:
    if len(identifier) >= 8 and ('-' in identifier or '.' in identifier):
        require(identifier.lower() not in agent, 'hidden/case identifier leaked: ' + identifier)
        scanned += 1
require(p['split_policy']['label'] == 'development-source' and p['split_policy']['independent_generalization_test_allowed'] is False, 'missing exposure boundary')
print(json.dumps(dict(status='PASS', questions=len(questions), deep_read_jobs=len(p['jobs']),
                      evidence_files_sha256_checked=len(references),
                      archived_call_slots_checked=len(slots), classifications=dict(counts),
                      validation_unverified=counts['validation-unverified'],
                      execution_failures=execution_details,
                      fullrepo_calls_without_job_timestamps=fullrepo_no_clock,
                      case_and_hidden_identifiers_scanned=scanned,
                      limitations=['Lexical leakage check is not a semantic guarantee.',
                                   'No new model or behavioral experiment; archived evidence only.',
                                   'No claim of improved repair effectiveness.']), ensure_ascii=False, indent=2))
