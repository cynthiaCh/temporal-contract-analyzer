"""Read real trajectory artifacts; absent artifacts remain explicitly unavailable."""
import difflib
import hashlib
from pathlib import Path

from runner import REPO, read

RECOVERY = REPO/'experiments/training-replays/tempoevo-gpt56-sol-medium-train70-error5-retry-20261118_221111'
TEST_RESULTS = REPO/'experiments/testing-runs/gpt56-library-size-ablation-20261118/results-61.json'


def archived_runs():
    result = []
    if (RECOVERY/'completion.json').is_file():
        result.append(dict(id='archive-training', title='Training replay · five recovered executions', mode='learning', status='recorded', recorded=True, count=5))
    if TEST_RESULTS.is_file():
        result.append(dict(id='archive-testing', title='Testing · GPT-5.6 · frozen 61-entry library', mode='testing', status='recorded', recorded=True, count=30))
    return result


def job_list(controller, ident):
    if ident == 'archive-training':
        return [dict(case_id=p.name, trajectory=p) for p in sorted((RECOVERY/'cases').iterdir()) if (p/'state.json').is_file()]
    if ident == 'archive-testing':
        return [dict(case_id=r['case_id'], score=r) for r in read(TEST_RESULTS)['cases']]
    root = controller.directory(ident)
    progress = root/'batch/progress.json'
    if not progress.is_file():
        return []
    return [dict(case_id=r['case_id'], trajectory=Path(r['root'])/'trajectory', preflight_status=r['status'], error=r.get('error')) for r in read(progress)]


def case_status(job):
    if 'score' in job:
        r = job['score']
        return dict(id=job['case_id'], status=r['status'], passed=r.get('gold_passed'), attempts=r.get('actions', 0))
    p = job['trajectory']/'state.json'
    if not p.is_file():
        return dict(id=job['case_id'], status=job.get('preflight_status', 'unavailable'), passed=None, attempts=0)
    state = read(p)
    result = state.get('final_acceptance') or state.get('gold_result') or {}
    stages = state.get('stages', [])
    finished = state.get('finalized', False) or state['status'] in {'cancelled', 'execution_invalid', 'preflight_failed'}
    current = next((s for s in reversed(stages) if s['status'] == 'started'), None)
    requests = sum(s.get('requests') or 0 for s in stages if s is not current)
    completed, started = 0, 0
    if current:
        for progress in (p.parent/'stages'/current['key']/'executions').glob('*/qoder-progress.json'):
            counts = read(progress)
            completed += counts['completed_turns']
            started += counts['completed_turns']
        for ledger in (p.parent/'stages'/current['key']/'executions').glob('*/native-stage/native/archive/meter/ledger.json'):
            try:
                counts = read(ledger)
            except (OSError, ValueError):
                continue  # The live collector may be writing this file.
            started += counts.get('started', 0)
            completed += counts.get('completed', 0)
        requests += completed
    return dict(id=job['case_id'], status=state['status'], passed=result.get('passed'), attempts=len(state['attempts']),
                finished=finished, error=state.get('error'),
                current_stage=current['key'] if current and not finished else None,
                completed_requests=requests, pending_requests=max(0, started-completed))


def run_detail(controller, ident):
    if ident.startswith('archive-'):
        meta = next((r for r in archived_runs() if r['id'] == ident), None)
        if not meta:
            raise ValueError('Archive not found')
        events = []
    else:
        root = controller.directory(ident)
        raw = read(root/'lab.json')
        meta = dict(id=ident, title=ident, recorded=False, **{k: raw[k] for k in ['status', 'created_at', 'config', 'model']}, error=raw.get('error'))
        meta.update({k: raw.get(k) for k in ('started_at', 'finished_at')})
        if meta['status'] in ('preparing', 'running', 'stopping') and controller.active != ident:
            meta.update(status='not_monitored', error='This batch belongs to an earlier workbench process. Check its processes and artifacts on the execution host; this workspace does not automatically resume it.')
        events = [__import__('json').loads(line) for line in (root/'events.jsonl').read_text().splitlines()] if (root/'events.jsonl').exists() else []
    jobs = job_list(controller, ident)
    cases = [case_status(j) for j in jobs]
    log_path = None if ident.startswith('archive-') else controller.directory(ident)/'prepare.log'
    return dict(meta=meta, cases=cases, events=events[-150:],
                preparation_log=log_path.read_text(errors='replace')[-20000:] if log_path and log_path.exists() else '',
                passed=sum(c['passed'] is True for c in cases), failed=sum(c['passed'] is False for c in cases),
                unscored=sum(c['passed'] is None for c in cases))


def originals(case_id, inventory, trajectory):
    bases = [trajectory/'original'] + [REPO/'cases'/split/case_id/'base' for split in ('train70', 'test30')]
    for base in bases:
        if not base.is_dir():
            continue
        files = {}
        for relative, digest in inventory.items():
            p = base/relative
            if Path(relative).is_absolute() or '..' in Path(relative).parts or not p.is_file() or p.stat().st_size > 250000:
                continue
            body = p.read_text(errors='replace')
            files[relative] = dict(text=body, matches_snapshot=hashlib.sha256(body.encode()).hexdigest() == digest)
        return files
    return {}


def case_detail(controller, ident, case_id):
    job = next((j for j in job_list(controller, ident) if j['case_id'] == case_id), None)
    if not job:
        raise ValueError('Case not found in this run')
    if 'score' in job:
        return dict(case=case_status(job), mode='testing', recorded=True, artifact_scope='Final-score archive only',
                    stages=[], attempts=[], contract=None, experience=[], candidate=None, originals={}, diffs={},
                    evaluation=job['score'], source=str(TEST_RESULTS.relative_to(REPO)), protocol=None)
    root = job['trajectory']
    if not (root/'protocol.json').exists():
        return dict(case=case_status(job), mode=None, recorded=ident.startswith('archive-'), artifact_scope='Preparation incomplete', stages=[], attempts=[], contract=None, experience=[], candidate=None, originals={}, diffs={}, evaluation=None, source=str(root), protocol=None)
    protocol, state = read(root/'protocol.json'), read(root/'state.json')
    summary = read(root/'summary.json') if (root/'summary.json').exists() else {}
    delivery = summary.get('delivery') or (read(root/'delivery.json') if (root/'delivery.json').exists() else {})
    selected = set(delivery.get('selected_sha256s', []))
    experiences = [e['bundle'] for e in protocol['memory_snapshot']['entries'] if e['bundle']['sha256'] in selected]
    original = originals(case_id, protocol['original_inventory'], root)
    diffs = {}
    for attempt in state['attempts']:
        edits = []
        for name, body in attempt.get('candidate_sources', {}).items():
            if name not in original or not original[name]['matches_snapshot']:
                continue
            if body != original[name]['text']:
                delta = ''.join(difflib.unified_diff(original[name]['text'].splitlines(True), body.splitlines(True), fromfile='original/'+name, tofile='attempt-'+str(attempt['number'])+'/'+name))
                edits.append(dict(file=name, diff=delta))
        diffs[str(attempt['number'])] = edits
    proposal = read(root/'candidate-pool/success.json') if (root/'candidate-pool/success.json').exists() else None
    execution_log = root.parent/'execution.log'
    try:
        source = str(root.relative_to(REPO))
    except ValueError:
        source = str(root)
    return dict(case=case_status(job), mode=protocol['mode'], recorded=ident.startswith('archive-'), artifact_scope='Retained trajectory artifacts',
                stages=state['stages'], attempts=[{k: a.get(k) for k in ['number', 'visible_passed', 'acceptance_passed', 'feedback']} for a in state['attempts']],
                contract=state.get('contract'), experience=experiences, delivered_text=delivery.get('experience_text'),
                candidate=None if not proposal else dict(experience=proposal['experience'], status=proposal.get('status'), effectiveness_verified=proposal.get('effectiveness_verified'), published=bool(proposal.get('published_sha256'))),
                originals=original, ast=read(root/'ast-evidence.json') if (root/'ast-evidence.json').exists() else None,
                execution_log=execution_log.read_text(errors='replace')[-20000:] if execution_log.exists() else '',
                diffs=diffs, evaluation=state.get('final_acceptance') or state.get('gold_result'),
                source=source,
                protocol=dict(task=protocol['task'], model=protocol['model'], mode=protocol['mode'], condition=protocol['condition'],
                              max_attempts=protocol['max_attempts'], retrieval_profile=protocol.get('retrieval_profile'),
                              approved_entries=len(protocol['memory_snapshot']['entries']), limits=protocol['limits'],
                              learning_policy=protocol['learning_policy'], bank_sha256=protocol['memory_snapshot_sha256']))
