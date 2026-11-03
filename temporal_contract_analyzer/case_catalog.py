"""Read candidate-visible bench task inputs without importing bench executors."""
import json
import os
from pathlib import Path

from .core import EvidenceError, ROOT, sha


def bench_root():
    return Path(os.environ.get('TCA_BENCH_ROOT', str(ROOT.parent/'temporal-contract-bench'))).expanduser().resolve()


def inside(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise EvidenceError('Invalid bench-relative input path')
    path = root/relative
    if path.is_symlink() or root not in path.resolve().parents:
        raise EvidenceError('Bench input escapes its registered directory')
    return path


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def local_models():
    home = Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex'))).expanduser()
    cache = home/'models_cache.json'
    try:
        data = read(cache)
        rows = data.get('models', [])
        if not isinstance(rows, list):
            rows = []
    except (OSError, ValueError, AttributeError):
        data, rows = {}, []
    choices, seen = [], set()
    for row in rows:
        if not isinstance(row, dict) or row.get('visibility') != 'list':
            continue
        name = row.get('slug')
        if not isinstance(name, str) or not name.strip() or len(name) > 200 or name in seen:
            continue
        seen.add(name)
        efforts = [r['effort'] for r in row.get('supported_reasoning_levels', [])
                   if isinstance(r, dict) and r.get('effort') in ('low','medium','high','xhigh','max','ultra')]
        default = row.get('default_reasoning_level')
        if default not in efforts:
            default = efforts[0] if efforts else None
        choices.append(dict(id=name, label=row.get('display_name') or name, efforts=efforts,
                            default_effort=default, earlier=name.startswith('gpt-5.')))
    choices.sort(key=lambda r:(not r['earlier'], r['id']))
    return dict(models=[r['id'] for r in choices], model_choices=choices, default_model='',
                model_source='local_codex_cache', models_fetched_at=data.get('fetched_at'))


def catalog():
    root = bench_root()
    index = root/'experiments/temporal-diagnostics-v1/corpus.json'
    if not index.is_file():
        raise EvidenceError('未找到 bench 案例列表：' + str(index))
    rows = read(index)['cases']
    exclusion_file = root/'studies/case-admission-exclusions-v1/registry.json'
    excluded = {r['case_id'] for r in read(exclusion_file)['cases']} if exclusion_file.is_file() else set()
    cases, ids = [], set()
    for row in rows:
        case_id = row['id']
        if case_id in ids:
            raise EvidenceError('Duplicate bench case ID')
        ids.add(case_id)
        manifest_path = inside(root, row['manifest'])
        manifest = read(manifest_path)
        if manifest['id'] != case_id:
            raise EvidenceError('Bench case ID/manifest mismatch')
        reason = ''
        if case_id in excluded:
            reason = 'bench 已排除的新实验案例'
        elif row['adapter'] not in ('legacy-js', 'python'):
            reason = '需要独立运行环境，暂未接入'
        elif 'latent-maintenance' not in row['conditions']:
            reason = '没有登记默认维护任务'
        elif not (manifest_path.parent/'base').is_dir():
            reason = '缺少 base 代码'
        cases.append(dict(id=case_id, title=manifest.get('title',case_id), language=row.get('language',''),
                          mechanism=row.get('mechanism',''), supported=not reason, unavailable_reason=reason))
    return dict(cases=cases, source=str(root), task_condition='latent-maintenance', **local_models())


def case_input(case_id):
    options = catalog()
    selected = next((c for c in options['cases'] if c['id']==case_id),None)
    if not selected or not selected['supported']:
        raise EvidenceError('案例不可运行：' + (selected['unavailable_reason'] if selected else str(case_id)))
    root = bench_root()
    rows = read(root/'experiments/temporal-diagnostics-v1/corpus.json')['cases']
    row = next(r for r in rows if r['id']==case_id)
    manifest_path = inside(root,row['manifest'])
    manifest = read(manifest_path)
    relative = manifest['prompt'] if row['adapter']=='python' else manifest['diagnostic_tasks']['maintenance']['core_prompt']
    prompt_path = inside(manifest_path.parent,relative)
    raw = prompt_path.read_bytes()
    candidate = inside(manifest_path.parent,'base')
    return dict(candidate=str(candidate),task=raw.decode('utf-8'),label=case_id,
                case_record=dict(id=case_id,manifest=row['manifest'],condition='latent-maintenance',
                                 authorization='ungranted',prompt_path=relative,prompt_sha256=sha(raw),
                                 prior_exposure=row.get('prior_exposure','unspecified'),adapter=row['adapter']))
