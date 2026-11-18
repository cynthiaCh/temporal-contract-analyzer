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


def case_root(record):
    source = record.get('source', 'bench')
    if source not in ('bench', 'local'):
        raise EvidenceError('Unknown case source')
    return ROOT if source == 'local' else bench_root()


def registered_cases():
    bench = bench_root()
    entries = []
    for source, root, index in (
            ('bench', bench, bench/'experiments/temporal-diagnostics-v1/corpus.json'),
            ('bench', bench, ROOT/'experiments/training-cases.json'),
            ('bench', bench, ROOT/'experiments/testing-cases.json'),
            ('local', ROOT, ROOT/'experiments/local-cases.json')):
        if index.is_file():
            rows=read(index)['cases']
            if index==ROOT/'experiments/testing-cases.json':
                rows=[r for r in rows if r['id'] not in {entry[2]['id'] for entry in entries}]
            entries.extend((source, root, row) for row in rows
                if index not in (ROOT/'experiments/training-cases.json',ROOT/'experiments/testing-cases.json') or (root/row['manifest']).is_file())
    # The central benchmark roster owns the current paths of migrated arms.
    # Older development registries remain authoritative for their existing IDs.
    central = bench/'benchmark/swe-tempoc.json'
    known = {row['id'] for _, _, row in entries}
    if central.is_file():
        for row in read(central)['cases']:
            if row['case_id'] in known:
                continue
            path = inside(bench, row['manifest'])
            if not path.is_file():
                continue
            manifest = read(path)
            runtime = manifest.get('framework', {}).get('runtime')
            python = manifest.get('language') == 'python'
            adapter = 'python' if python else 'legacy-js' if runtime in {
                'vanilla-js','jquery','react18','vue2','vue3','java','python3','php','ruby','go'} else 'upstream'
            conditions = ['latent-maintenance'] if python or manifest.get('diagnostic_tasks', {}).get('maintenance', {}).get('core_prompt') else []
            entries.append(('bench', bench, dict(id=row['case_id'], manifest=row['manifest'],
                adapter=adapter, conditions=conditions, language=runtime or manifest.get('language',''),
                mechanism=manifest.get('mechanism',''), prior_exposure='exposed_benchmark_registry')))
            known.add(row['case_id'])
    if not entries:
        raise EvidenceError('未找到可运行的案例列表')
    return entries


def catalog():
    root = bench_root()
    exclusion_file = root/'studies/case-admission-exclusions-v1/registry.json'
    excluded = {r['case_id'] for r in read(exclusion_file)['cases']} if exclusion_file.is_file() else set()
    cases, ids = [], set()
    for source, source_root, row in registered_cases():
        case_id = row['id']
        if case_id in ids:
            raise EvidenceError('Duplicate bench case ID')
        ids.add(case_id)
        manifest_path = inside(source_root, row['manifest'])
        manifest = read(manifest_path)
        if manifest['id'] != case_id:
            raise EvidenceError('Bench case ID/manifest mismatch')
        reason = ''
        if source == 'bench' and case_id in excluded:
            reason = 'bench 已排除的新实验案例'
        elif row['adapter'] not in ('legacy-js', 'python'):
            reason = '需要独立运行环境，暂未接入'
        elif 'latent-maintenance' not in row['conditions']:
            reason = '没有登记默认维护任务'
        elif not (manifest_path.parent/'base').is_dir():
            reason = '缺少 base 代码'
        cases.append(dict(id=case_id, title=manifest.get('title',case_id), language=row.get('language',''),
                          mechanism=row.get('mechanism',''), source=source,
                          supported=not reason, unavailable_reason=reason))
    return dict(cases=cases, source=str(root), task_condition='latent-maintenance')


def case_input(case_id):
    options = catalog()
    selected = next((c for c in options['cases'] if c['id']==case_id),None)
    if not selected or not selected['supported']:
        raise EvidenceError('案例不可运行：' + (selected['unavailable_reason'] if selected else str(case_id)))
    source, root, row = next(entry for entry in registered_cases() if entry[2]['id']==case_id)
    manifest_path = inside(root,row['manifest'])
    manifest = read(manifest_path)
    relative = manifest['prompt'] if row['adapter']=='python' else manifest['diagnostic_tasks']['maintenance']['core_prompt']
    prompt_path = inside(manifest_path.parent,relative)
    raw = prompt_path.read_bytes()
    candidate = inside(manifest_path.parent,'base')
    return dict(candidate=str(candidate),task=raw.decode('utf-8'),label=case_id,
                case_record=dict(id=case_id,manifest=row['manifest'],source=source,condition='latent-maintenance',
                                 authorization='ungranted',prompt_path=relative,prompt_sha256=sha(raw),
                                 prior_exposure=row.get('prior_exposure','unspecified'),adapter=row['adapter']))
