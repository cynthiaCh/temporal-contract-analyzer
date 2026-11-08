"""Python-only results/cost/integrity archival; no model API or scheduler."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

A = Path(__file__).resolve().parent


def read(p, default=None):
    return json.loads(p.read_text()) if p.exists() else default


def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    rows = read(A / 'actual-schedule.json', [])
    cohort = read(A / 'cohort.json', [])
    costs = {}
    for phase, name in [('extract', 'preanalysis'), ('reflect', 'reflection'), ('repair', 'maintenance')]:
        selected = [r for r in rows if r['phase'] == phase]
        usage = [read(A / 'runs' / r['slot'] / 'archive/usage.json', {}) for r in selected]
        observed = [x.get('observed_usage_subtotal') for x in usage if x.get('observed_usage_subtotal')]
        totals = {k: sum(x.get(k, 0) for x in observed) for k in set().union(*(x.keys() for x in observed))} if observed else None
        costs[name] = {'sessions': len(selected), 'requests_started': sum(r.get('native', {}).get('started', 0) for r in selected),
                       'requests_completed': sum(r.get('native', {}).get('completed', 0) for r in selected),
                       'session_seconds': sum(r.get('seconds') or 0 for r in selected),
                       'session_time_incomplete': any(r.get('seconds') is None for r in selected),
                       'observed_token_subtotal': totals,
                       'total_tokens': totals if selected and all(x.get('total_usage') is not None for x in usage) else None,
                       'usage_incomplete': any(x.get('total_usage') is None for x in usage), 'monetary_cost': None}
    costs['engineering'] = {'tokens': None, 'monetary_cost': None,
         'preparation_script_seconds': read(A / 'prepare-receipt.json', {}).get('seconds'),
         'offline_seconds': read(A / 'offline-validation.json', {}).get('seconds'),
         'note': 'Current executing assistant engineering usage unavailable; offline fixtures excluded from model sessions.'}
    development = {}
    for alias in ['D1', 'D2']:
        out = A / 'development' / alias
        development[alias] = {'state': read(out / 'state.json'), 'admission': read(out / 'admission.json'),
                               'preanalysis': read(A / 'derived' / alias / 'analysis.json'),
                               'revalidation_comparison': read(out / 'revalidation-comparison.json')}
    tests = {}
    completion = read(A / 'completion.json', {})
    planned = read(A / 'schedule.json', {}).get('slots', [])
    started_test = (A / 'test-started.json').exists()
    for alias in ['T1', 'T2']:
        test_rows = [r for r in rows if r['alias'] == alias and r.get('arm') in ['A', 'B']]
        original = read(A / 'calibration' / alias / 'original/stdout.json', {})
        manifest = read(A / 'materials' / alias / 'evaluation/effects.json', {})
        rules = manifest.get('variants', {}).get('ungranted', {})
        expected = {k: True for k in rules.get('required', [])}
        expected.update({k: False for k in rules.get('forbidden', [])})
        entries = []
        for rec in test_rows:
            base = A / 'runs' / rec['slot'] / 'archive'
            score = read(base / 'score/stdout.json', {})
            effects = score.get('observed_effects', {})
            regressions = [k for k, v in expected.items() if original.get('observed_effects', {}).get(k) == v and effects.get(k) != v]
            entries.append({'slot': rec['slot'], 'arm': rec['arm'], 'block': rec['block'], 'status': rec['status'],
                'infrastructure_valid': rec.get('infrastructure_valid'), 'verdict': score.get('verdict'),
                'effects': effects, 'regressions_vs_original': regressions, 'cost': read(base / 'usage.json'),
                'seconds': rec.get('seconds'), 'patch': str(base / 'patch.diff'), 'raw_score': str(base / 'score/stdout.json')})
        pairs = []
        for block in [1, 2]:
            a = next((r for r in entries if r['arm'] == 'A' and r['block'] == block), None)
            b = next((r for r in entries if r['arm'] == 'B' and r['block'] == block), None)
            if a and b:
                pairs.append({'block': block,
                    'B_improves_A': [k for k, v in expected.items() if a['effects'].get(k) != v and b['effects'].get(k) == v],
                    'B_regresses_A': [k for k, v in expected.items() if a['effects'].get(k) == v and b['effects'].get(k) != v]})
        route = read(A / 'testing' / alias / 'route.json')
        tests[alias] = {'preanalysis': read(A / 'derived' / alias / 'analysis.json'), 'route': route,
                       'prompt_correspondence': read(A / 'testing' / alias / 'prompt-correspondence.json'),
                       'runs': entries, 'paired_relations': pairs, 'expected': expected,
                       'unstarted_slots': [s['slot'] for s in planned if s['alias'] == alias and s['slot'] not in [r['slot'] for r in entries]]}
    aggregates = {}
    for subset in ['all', 'hit', 'fallback']:
        aliases = [alias for alias, t in tests.items() if subset == 'all' or (
            t['route'] is not None and (t['route']['condition'] == 'ROUTED') == (subset == 'hit'))]
        aggregate = {'cases': aliases}
        for arm in ['A', 'B']:
            entries = [r for alias in aliases for r in tests[alias]['runs'] if r['arm'] == arm]
            aggregate[arm] = {'passed': sum(r['verdict'] == 'PASS' for r in entries), 'started': len(entries),
                              'planned': 2 * len(aliases) if started_test else 0,
                              'missing': 2 * len(aliases) - len(entries) if started_test else 0}
        aggregates[subset] = aggregate
    summary = {'status': completion.get('status', 'STOPPED' if (A / 'stop.json').exists() else 'INCOMPLETE'),
        'stop': read(A / 'stop.json'), 'development': development, 'tests': tests,
        'frozen_library': read(A / 'frozen-library.json'), 'aggregate': aggregates, 'costs': costs,
        'sessions_started': len(rows), 'requests_started': sum(r.get('native', {}).get('started', 0) for r in rows),
        'limits': {'sessions': 20, 'requests': 408, 'concurrency': 1, 'seconds_per_session': 600},
        'source_design': 'two same-source cross-language pairs; permanently exposed; not independent generalization',
        'scope': 'two development paths; no claim that four categories are validated',
        'training_revalidation_in_test_denominator': False, 'sampling_seed_controls_model_sampling': False}
    save(A / 'summary.json', summary)
    save(A / 'behavior-vectors.json', {alias: t['runs'] for alias, t in tests.items()})
    lines = ['# Two-class experience pilot', '', 'Task 1：实现复用、离线预检与四例来源', '',
        '状态：' + summary['status'] + '。起始HEAD：' + read(A / 'initial-state.json')['HEAD'] + '。',
        '旧阻断目录已补齐；本批只新增研究目录。复用runner.session、请求guard、Python自动归档；未启动旧调度器。',
        'AST及源码分析→单次预分析Contract/主类/前提→保守路由→公共prompt→独立维护→外部原评分已接入。',
        '政策依据与执行Agent解释见policy-review.md；反馈差异由通用代码提取，不把旧query诊断改名为自动分析。',
        '四例使用精确版本绑定的44次既有校准。Node18.17.0与JS manifest Node16有版本差异；Python3.8.10匹配。',
        '离线检查见offline-validation.json，包含真实bwrap隔离、JS/Python正文证据、guard IPC、请求上限与自动归档。', '',
        '| alias | case | source unit |', '|---|---|---|']
    for c in cohort:
        lines.append(f"|{c['alias']}|{c['case']}|{c['independent_unit_id']}|")
    lines += ['', '两个同源跨语言对，已有暴露；T2的v2事后评分修订与既往求解暴露保留在manifest/exposure.json。',
              '旧E2不作为本批反思种子或经验成果。', '', 'Task 2：两例开发、经验冻结和两例测试', '']
    for alias, data in development.items():
        lines += [f'**{alias} 开发**', '', '```json', json.dumps(data['state'], ensure_ascii=False, indent=2),
                  '```', '入库审查：' + json.dumps(data['admission'], ensure_ascii=False), '']
        comparison = data['revalidation_comparison']
        if comparison:
            for n, row in enumerate(comparison['vs_each_AUTO'], 1):
                lines.append(f"回验相对AUTO-{n}：改善{[x['effect'] for x in row['improvements']]}；退步{[x['effect'] for x in row['regressions']]}。")
    lines += ['', '冻结库正文、版本和SHA256见frozen-library.json；经验未经人工润色。开发回验不计入测试。', '']
    for alias, data in tests.items():
        analysis = data['preanalysis'] or {}
        lines += [f'**{alias} 测试**', '', f"实际主类：{analysis.get('primary_class')}；副标签：{analysis.get('secondary_tags')}。",
                  '源证据：' + json.dumps(analysis.get('evidence'), ensure_ascii=False),
                  '路由：' + json.dumps(data['route'], ensure_ascii=False),
                  'A/B提示对应：' + json.dumps(data['prompt_correspondence'], ensure_ascii=False), '',
                  '| slot | verdict | requests | seconds | regressions vs original |', '|---|---|---|---|---|']
        for run in data['runs']:
            lines.append(f"|{run['slot']}|{run['verdict']}|{(run['cost'] or {}).get('requests_started')}|{run['seconds']}|{run['regressions_vs_original']}|")
        lines += ['', '完整行为向量（true/false为原评分观测，必须结合标准期望理解）：', '',
                  '| relation (expected) | A1 | A2 | B1 | B2 |', '|---|---|---|---|---|']
        for effect, expect in data['expected'].items():
            values = []
            for arm, block in [('A', 1), ('A', 2), ('B', 1), ('B', 2)]:
                row = next((r for r in data['runs'] if r['arm'] == arm and r['block'] == block), None)
                values.append(str(row['effects'].get(effect)) if row else 'missing')
            lines.append('| ' + effect + ' (' + str(expect) + ') | ' + ' | '.join(values) + ' |')
        lines += ['', '块内关系对照：' + json.dumps(data['paired_relations'], ensure_ascii=False),
                  '未启动槽位：' + json.dumps(data['unstarted_slots']), '']
    lines += ['Task 3：完整得失、成本、限制与下一步', '', '全体与命中/回退子集：', '', '```json',
              json.dumps(aggregates, ensure_ascii=False, indent=2), '```', '',
              '分角色成本（token/货币未知不补零；观测subtotal不是完整用量）：', '', '```json',
              json.dumps(costs, ensure_ascii=False, indent=2), '```', '',
              '每例只有两次A和两次B，不证明稳定效果、确定分类准确率或独立新来源泛化。',
              '同提示回退的随机差异不能归因为经验；开发回验仅用于入库检查。全过/全失败/未命中均保留。',
              'AST与字面源证据不证明语义；分类、事实核查来自一次预分析模型，政策与入库审查来自当前执行Agent。',
              '本轮只核对两类开发路径，不声称四类均验证。完整原评分、候选、补丁、公开交付与计量在runs各archive中。',
              '下一步应先审查本批原始轨迹和政策适用性；任何增加来源、修订经验或消融都需另立方案，本批不自动扩展。']
    if summary['stop']:
        lines += ['', '停止条件：' + json.dumps(summary['stop'], ensure_ascii=False)]
    (A / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    frozen = read(A / 'protocol.json', {}).get('files', {})
    frozen.update(read(A / 'experience-freeze.json', {}).get('files', {}))
    protected = read(A / 'protected-files.json', {})
    changed = [p for p, h in {**protected, **frozen}.items() if not Path(p).is_file() or sha(Path(p)) != h]
    integrity = {'changed_protected_or_frozen_files': changed, 'verified_files': len({**protected, **frozen}),
                 'sessions_within_limit': len(rows) <= 20, 'requests_within_limit': summary['requests_started'] <= 408,
                 'all_started_slots_preserved': all((A / 'runs' / r['slot']).exists() for r in rows),
                 'legacy_scheduler_started': False, 'production_registry_updated': False, 'git_commit_created': False}
    save(A / 'integrity-check.json', integrity)
    (A / 'COMMIT_MESSAGE.txt').write_text('research: add and execute fixed two-class experience pilot\n\n'
        'Reuse isolated sessions, request metering and Python-owned archives.\n'
        'Add source-bound classification, conservative frozen-experience routing and generic feedback.\n'
        'Archive fixed two-training/two-test development, admission decisions, complete outcomes and costs.\n'
        'Disclose same-source exposure and limitations; preserve original scoring and production registry.\n')
    save(A / 'code-summary.json', {p.name: sha(p) for p in A.glob('*.py')})
    files = {str(p.relative_to(A)): sha(p) for p in A.rglob('*')
             if p.is_file() and not p.is_symlink() and p.name != 'archive-manifest.json' and '__pycache__' not in p.parts}
    save(A / 'archive-manifest.json', {'algorithm': 'sha256', 'files': files, 'self_excluded': True})
    print(json.dumps({'status': summary['status'], 'sessions': len(rows), 'requests': summary['requests_started'],
                      'aggregate': aggregates, 'integrity': integrity}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
