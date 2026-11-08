"""Post-stop reporting correction and raw-ledger diagnostics, no experiment work.

The frozen runner/controller/summarizer remain unchanged. Missing test scores
must not be reported as behavioral regressions. Raw failed-session archives
are never repaired, rescored or overwritten here.
"""
import hashlib
import json
from pathlib import Path
import time

A = Path(__file__).resolve().parent


def read(p, default=None):
    return json.loads(p.read_text()) if p.exists() else default


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert (A / 'stop.json').exists(), 'reporter only for this stopped batch'
    rows = read(A / 'actual-schedule.json')
    summary = read(A / 'summary.json')
    failed = A / 'runs/T1-block-1-A/archive'
    raw_before = {str(p.relative_to(failed)): sha(p) for p in failed.rglob('*') if p.is_file()}
    save(A / 'diagnostics/failed-archive-before.json', raw_before)
    diagnostic = {'slot': 'T1-block-1-A', 'underlying_failure':
        'Fourth request stream disconnected before completion: error sending request; CLI exit 1, turn.failed.',
        'post_request_status': 'failed', 'token_usage': None,
        'archiver_failure': "archive.collect summed e.get('token_usage', {}).get(...); actual token_usage was explicit null, raising NoneType.get",
        'immediate_stop_basis': 'archive integrity failure, not the single infrastructure event by itself',
        'preserved': ['events.jsonl', 'stderr.log', 'meter/ledger.json', 'patch.diff', 'final-candidate',
                      'final-manifest.json', 'model-outcome.json', 'receipt.json', 'partial-answer.txt'],
        'missing': ['collection.json', 'usage.json', 'score/stdout.json'],
        'original_candidate_unchanged': True, 'final_snapshot_preserved': True,
        'final_snapshot_scored': False, 'retry': False, 'remaining_maintenance_slots_unstarted': 7,
        'followup': 'In a separately frozen batch, handle explicit null usage on failed request and test the failure path before paid work. No fix or restart in this batch.'}
    save(A / 'diagnostics/stop-diagnosis.json', diagnostic)
    # Recover only observed counters/usage as a supplementary report, not a new
    # successful archive. Unknown usage remains null, never fabricated as zero.
    costs = {}
    role_names = {'extract': 'preanalysis', 'reflect': 'reflection', 'repair': 'maintenance'}
    for phase, name in role_names.items():
        selected = [r for r in rows if r['phase'] == phase]
        events, slots = [], []
        for rec in selected:
            ledger = read(A / 'runs' / rec['slot'] / 'archive/meter/ledger.json', {})
            posts = [x['event'] for x in ledger.get('events', []) if x['event'].get('hook_event_name') == 'PostModelRequest']
            events.extend(posts)
            slots.append({'slot': rec['slot'], 'requests_started': ledger.get('started'),
                'post_request_hooks': ledger.get('completed'),
                'successful_requests': sum(e.get('status') == 'completed' for e in posts),
                'failed_requests': sum(e.get('status') == 'failed' for e in posts),
                'usage_unknown_requests': sum(not isinstance(e.get('token_usage'), dict) for e in posts),
                'seconds': rec.get('seconds')})
        keys = ['input_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'output_tokens', 'reasoning_output_tokens', 'total_tokens']
        known = [e['token_usage'] for e in events if isinstance(e.get('token_usage'), dict)]
        observed = {k: sum(x[k] for x in known if k in x) if any(k in x for x in known) else None for k in keys}
        complete = all(isinstance(e.get('token_usage'), dict) for e in events) and all(s['requests_started'] == s['post_request_hooks'] for s in slots)
        totals = {k: observed[k] if complete and all(k in x for x in known) else None for k in keys}
        costs[name] = {'sessions': len(selected), 'requests_started': sum(s['requests_started'] or 0 for s in slots),
            'post_request_hooks': sum(s['post_request_hooks'] or 0 for s in slots),
            'successful_requests': sum(s['successful_requests'] for s in slots),
            'failed_requests': sum(s['failed_requests'] for s in slots),
            'usage_unknown_requests': sum(s['usage_unknown_requests'] for s in slots),
            'session_seconds': sum(s['seconds'] for s in slots if s['seconds'] is not None),
            'session_seconds_complete': all(s['seconds'] is not None for s in slots),
            'observed_token_subtotal': observed, 'total_tokens': totals, 'usage_incomplete': not complete,
            'monetary_cost': None, 'slots': slots,
            'note': 'Derived from raw hook ledgers; completed hook counts include failed responses. Reasoning tokens are a subset of output; cached tokens a subset of input.'}
    costs['engineering'] = summary['costs']['engineering']
    summary['test_costs'] = {}
    for alias in ['T1', 'T2']:
        groups = {'preanalysis': [r for r in rows if r['alias'] == alias and r['phase'] == 'extract']}
        for arm in ['A', 'B']:
            groups[arm] = [r for r in rows if r['alias'] == alias and r.get('arm') == arm]
        per_case = {}
        for name, selected in groups.items():
            posts = []
            for rec in selected:
                ledger = read(A / 'runs' / rec['slot'] / 'archive/meter/ledger.json')
                posts += [x['event'] for x in ledger['events'] if x['event'].get('hook_event_name') == 'PostModelRequest']
            known = [e['token_usage'] for e in posts if isinstance(e.get('token_usage'), dict)]
            per_case[name] = {'sessions': len(selected),
                'requests_started': sum(r['native']['started'] for r in selected),
                'session_seconds': sum(r['seconds'] for r in selected),
                'observed_total_token_subtotal': sum(x['total_tokens'] for x in known) if known else None,
                'total_tokens': sum(x['total_tokens'] for x in known) if selected and len(known) == len(posts) else None,
                'usage_incomplete': bool(selected) and len(known) != len(posts),
                'status': 'started' if selected else 'not_started_no_usage', 'monetary_cost': None}
        summary['test_costs'][alias] = per_case
    summary['costs'] = costs
    summary['status'] = 'STOPPED_DURING_FIRST_TEST_MAINTENANCE_ARCHIVE_ERROR'
    summary['stop_diagnosis'] = diagnostic
    summary['preanalysis_quality_reviews'] = {alias: read(A / 'derived' / alias / 'quality-review.json') for alias in ['D1', 'T1']}
    summary['test_effect_comparison_available'] = False
    summary['routing_semantic_limit'] = 'Router checked source-bound predicate facts, not consistency between Contract prose and current task/source. T1 matched despite a contradictory auxiliary Contract; do not claim complete semantic conflict detection.'
    summary['tests_planned_maintenance_sessions'] = 8
    summary['tests_started_maintenance_sessions'] = 1
    summary['tests_scored_maintenance_sessions'] = 0
    summary['test_denominator_policy'] = 'Keep all 8 planned slots; 1 started-unscored and 7 unstarted. No pass-rate numerator/denominator estimate from missing scores.'
    for alias, data in summary['tests'].items():
        for rec in data['runs']:
            if rec['verdict'] is None:
                rec['regressions_vs_original'] = None
                rec['effects'] = None
                rec['score_status'] = 'NOT_SCORED_ARCHIVE_ERROR'
                rec['cost'] = next(s for s in costs['maintenance']['slots'] if s['slot'] == rec['slot'])
        data['effect_comparison_available'] = False
    for subset, aggregate in summary['aggregate'].items():
        for arm in ['A', 'B']:
            entries = [r for alias in aggregate['cases'] for r in summary['tests'][alias]['runs'] if r['arm'] == arm]
            arm_data = aggregate[arm]
            arm_data['scored'] = sum(r['verdict'] is not None for r in entries)
            arm_data['started_unscored'] = sum(r['verdict'] is None for r in entries)
            arm_data['pass_rate'] = None
            arm_data['passes_observed'] = sum(r['verdict'] == 'PASS' for r in entries)
            arm_data['passed'] = None if arm_data['scored'] == 0 else arm_data['passes_observed']
            arm_data['missing_means'] = 'unstarted planned slots, not behavior failures'
    save(A / 'summary.json', summary)
    save(A / 'behavior-vectors.json', {alias: t['runs'] for alias, t in summary['tests'].items()})
    save(A / 'usage-reconciliation.json', costs)
    # A complete terminal schedule explicitly preserves all seven unstarted slots.
    actual = {r['slot']: r for r in rows}
    terminal = []
    for slot in read(A / 'schedule.json')['slots']:
        rec = actual.get(slot['slot'])
        terminal.append({**slot, 'launch_status': 'STARTED' if rec else 'NOT_STARTED_AFTER_STOP',
                         'score_status': rec.get('scoring_status') if rec else 'NOT_REQUESTED',
                         'behavior_vector': None, 'whole_task_pass': None})
    save(A / 'terminal-test-schedule.json', terminal)
    lines = ['# 2+2 分类经验工具试验：归档故障后停止', '',
        '**本轮没有可用的A/B效果比较。** 已完成两例开发、冻结及两个测试例分类路由；首个测试维护会话流断连后触发归档错误，立即停止。1个维护槽位已启动但未评分，其余7个未启动。不能把缺失项写成失败率。', '',
        'Task 1：实现复用、离线预检与四例来源', '',
        '起始HEAD为938076ab4f06a496348d15b7d8d6f11b5ae453c7，起始工作区干净。指定v1规范已补齐，旧设计的run_enabled=false不替代本次用户明确授权。所有新实现与实验留档位于本目录，旧实验、原案例、评分、生产经验库和全局配置未改；未安装依赖，未创建提交。',
        '复用既有runner.session、native CLI命令、host-owned guard计量及Python快照/补丁/日志归档；没有导入或启动旧调度器。新增toolflow.py和control.py，打通同次Contract提取/机制分类、源绑定事实、保守路由、共享prompt、通用评分差异、反思和冻结。',
        '零模型检查：31项归档/路由检查通过；四例AST全部解析；实际四例bwrap隔离、JS/Python正文读取、hook IPC、预算计数与自动归档均用假CLI通过。44份原始/参考/退化校准与本批base/task/oracle精确摘要对应并复用，未冒充新训练。Node18.17.0与JS manifest的Node16有差异，Python3.8.10匹配；未声称原Node16环境重现。', '',
        '| alias | case | source unit |', '|---|---|---|']
    for c in read(A / 'cohort.json'):
        lines.append(f"|{c['alias']}|{c['case']}|{c['independent_unit_id']}|")
    lines += ['', '两对均为同源跨语言，旧暴露永久保留；T2的事后评分v2与求解暴露见manifest/exposure.json。不是独立新来源泛化测试。原任务/README/docs/源码提供政策依据，policy-review.md明确哪些解释由当前执行Agent核查；没有伪造人工批准。通用反馈只抽取实际/标准差异，未包装旧query专用诊断。旧E2正文未提供给本批反思器。', '',
        'Task 2：两例开发、经验冻结和两例测试', '',
        '| 训练例 | AUTO整题 | 开发回验 | 经验处理 |', '|---|---|---|---|',
        '| D1 | 0/2；行为18/29、27/29 | 0/1；行为27/29 | 按有据关系改善入库T4候选，完整记录退步 |',
        '| D2 | 2/2 | 按规则不做 | T3本批不生成经验，保持空 |', '',
        'D1主类T4。预分析辅助Contract把“不得重连后以live signal启动”反向写成应恢复；它原样共享给两次AUTO和开发回验，未人工纠正。此处是Contract质量错误，不是输入版本漂移。',
        'D1唯一反思产生一份原样候选，未润色或生成第二份。候选有一句错误归因：声称第一次按执行归属修改修好了离线退出，实际AUTO-1仍失败。这是证据归因缺陷，已明确记录，不能因之后有改善而隐去。',
        'D1回验相对AUTO-1改善9项、无新增退步；相对AUTO-2改善缓存暂停后台与后续消费两项，同时退步prior-consumed-success和retained-context两项。仍未整题通过。入库依据是预先允许的关系改善，当前可见文档/源码支持其生命周期分离和条件性边界结算，没有确认的新增无据业务政策；不是因回验稳定成功而接纳。详见development/D1/admission.json及完整comparison。',
        '候选结构化excludes为空，但正文列有不适用政策，这是路由元数据不完整的局限。所需三项前提仅能支持机制适用，不证明全文语义必然正确。',
        'D2主类T3，两个AUTO均通过原评分，因此没有反思和回验槽位。不能为了两条经验而人为补齐。',
        '冻结库仅一条T4经验：正文SHA256 89aefe23f09ad539fe74e0257d44fb6da53028f5bcd7bf781abaa7ec27ee39b6；含适用元数据的entry SHA256 0629d9502c3f9fb7bff3a0ca5d6dcef78424ae48b319a64cdf905d893c482356。版本pilot-1，原文见frozen-library.json和development/D1/experience-original.md。', '',
        '| 测试例 | 实际主类 | 前提/路由 | A/B维护状态 |', '|---|---|---|---|',
        '| T1 | T4 | 共享寿命、异步恢复、惰性消费均known，源绑定核查后命中 | A1已启动但未评分；其余3槽未启动 |',
        '| T2 | T3 | 同类经验为空，回退AUTO；A/B提示字节相同 | 4槽均未启动 |', '',
        '分类仅使用原任务、当前候选相对源码/文档、AST、四类定义及通用前提；无case ID到类别查表。路由不接收case/cluster/历史成绩/评分器/参考补丁。具体证据、前提状态、摘要与回退理由见testing/*/route.json、derived/*/analysis.json。',
        '实现限制：路由只核对结构化前提的字面源证据，没有对Contract正文与原任务/源码进行语义一致性校验；T1虽有相反的辅助Contract，仍按三个known机制前提命中。这个观测不能被称为完整的语义冲突检测已通过。冻结后未改变路由或人工改投放。',
        'T1自动Contract也反向复述了原任务，并把消费归属写为单次执行；原文未改，A/B共享。已记录在derived/T1/quality-review.json。即使后续另批得到差异，也不能忽略辅助Contract错误的混杂。',
        '固定测试调度种子2026110804，只控制块内A/B顺序，不控制模型采样。顺序为T1 A1/B1/A2/B2，T2 B1/A1/B2/A2。经验库冻结后才进行两个测试预分析，随后开始首个维护。没有测试成绩回流学习，也没有测试成绩可用于调参。', '',
        '**停止链与缺失情况**', '',
        'T1/A1第4请求流断连，CLI exit=1、turn.failed。原始hook记录status=failed且token_usage=null；archive.collect错误地对显式null调用.get，引发AttributeError。快照、最终源码、补丁、原事件和账本已保存，collect阶段失败、归档状态ERROR；没有调用评分器。触发的是归档完整性立即停止规则，不是把单次网络异常当成连续两次异常。',
        '未修复冻结代码后续跑，未重试该槽，也未补跑其他槽。原失败档案保持原样；诊断和从原ledger提取的观测用量放在外部diagnostics与usage-reconciliation.json，不伪造成功归档。',
        '计划8槽仍全部保留：1槽已启动未评分，7槽未启动。行为向量、整题通过和退步均未知；不是0/8失败。没有任何完整测试A/B对，不能比较经验得失。训练回验不进测试分母。', '',
        '每个测试例的预分析与A/B成本（未启动没有用量观测；失败请求用量未知）：', '', '```json',
        json.dumps(summary['test_costs'], ensure_ascii=False, indent=2), '```', '',
        'Task 3：完整得失、成本、限制与下一步', '',
        '按全体、命中、回退分别列出计划/启动/评分/缺失：', '', '```json',
        json.dumps(summary['aggregate'], ensure_ascii=False, indent=2), '```', '',
        '分角色成本（token采用原hook；失败请求未知用量保持null，subtotal仅含已观测部分；货币与当前工程助手token未知）：', '', '```json',
        json.dumps({k: {field: value for field, value in v.items() if field != 'slots'} for k, v in costs.items()}, ensure_ascii=False, indent=2), '```', '',
        '共11个实验会话、58个底层请求启动：4个预分析、1个反思、6个维护。最后一个失败请求有终止hook但未知token，不能把58个hook都称为成功请求。没有额外预跑、模型评委、第二反思、重试或补跑。',
        '已观察到的开发收益是D1部分关系改善，损失是两项保留关系退步、反思归因错误，以及D1/T1辅助Contract方向错误。工程检查虽通过，未覆盖“API失败且usage显式null”的真实归档分支，这是本轮具体暴露的缺口。',
        '测试结果不足，不能宣称稳定效果、分类器准确率已确定、独立泛化或四类全部验证。T3没有本批经验；T2本应作为同提示回退子集保留，不能以后因无增益而剔除。',
        '下一步应在另立冻结版本前，增加null用量/失败流的离线归档检查，并审查Contract与原任务禁止方向的一致性；本批冻结代码不改、不续跑。若开展新批次，必须保留本批测试暴露，不重标为未见。',
        '推荐Git提交文本见COMMIT_MESSAGE.txt；未创建提交或更新生产经验库。']
    (A / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    # Integrity checks include raw failed archive and source/config freezes.
    frozen = read(A / 'protocol.json')['files']
    frozen.update(read(A / 'experience-freeze.json')['files'])
    protected = read(A / 'protected-files.json')
    changed = [p for p, h in {**protected, **frozen}.items() if not Path(p).is_file() or sha(Path(p)) != h]
    raw_after = {str(p.relative_to(failed)): sha(p) for p in failed.rglob('*') if p.is_file()}
    intervals = sorted((r['started_at'], r['started_at'] + r['seconds'], r['slot']) for r in rows)
    sequential = all(left[1] <= right[0] for left, right in zip(intervals, intervals[1:]))
    freeze_time = read(A / 'experience-freeze.json')['time']
    test_after_freeze = all(r['started_at'] > freeze_time for r in rows if r['alias'] in ['T1', 'T2'])
    role_model = {'extract': 'gpt-6-sol', 'reflect': 'gpt-5.6-terra', 'repair': 'gpt-5.6-terra'}
    model_mismatches, cap_errors = [], []
    for row in rows:
        ledger = read(A / 'runs' / row['slot'] / 'archive/meter/ledger.json')
        ev = [x['event'] for x in ledger['events'] if x['event'].get('hook_event_name') in ['PreModelRequest', 'PostModelRequest']]
        if any(e.get('model') != role_model[row['phase']] for e in ev):
            model_mismatches.append(row['slot'])
        if ledger['started'] > (24 if row['phase'] == 'repair' else 12):
            cap_errors.append(row['slot'])
    requests_started = sum(r.get('native', {}).get('started', 0) for r in rows)
    integrity = {'changed_protected_or_frozen_files': changed, 'verified_files': len({**protected, **frozen}),
        'raw_failed_archive_unchanged': raw_before == raw_after, 'model_sessions_concurrency_one': sequential,
        'all_test_calls_after_library_freeze': test_after_freeze, 'model_mismatches': model_mismatches,
        'per_session_cap_errors': cap_errors, 'sessions_started': len(rows), 'requests_started': requests_started,
        'sessions_within_20': len(rows) <= 20, 'requests_within_408': requests_started <= 408,
        'test_planned': 8, 'test_started': 1, 'test_scored': 0, 'test_unstarted': 7,
        'failed_test_not_labeled_behavior_failure': True, 'legacy_scheduler_started': False,
        'experiment_retry_or_rerun': False, 'production_registry_updated': False, 'git_commit_created': False}
    assert not changed and raw_before == raw_after and sequential and test_after_freeze
    assert not model_mismatches and not cap_errors
    save(A / 'integrity-check.json', integrity)
    (A / 'COMMIT_MESSAGE.txt').write_text('research: archive fixed 2+2 experience pilot and safe test stop\n\n'
        'Add source-bound preanalysis, conservative routing and generic training feedback.\n'
        'Reuse isolated sessions, request guards and Python-owned archives; verify 31 offline checks.\n'
        'Develop one T4 candidate; leave T3 empty after both AUTO baselines pass.\n'
        'Record both test routes, Contract direction errors and the first test stream/null-usage archive failure.\n'
        'Stop without retries; preserve the unscored slot, seven unstarted slots and incomplete usage.\n'
        'Keep original scoring, prior exposure and production experience registry unchanged.\n')
    save(A / 'code-summary.json', {p.name: sha(p) for p in A.glob('*.py')})
    files = {str(p.relative_to(A)): sha(p) for p in A.rglob('*')
             if p.is_file() and not p.is_symlink() and p.name != 'archive-manifest.json' and '__pycache__' not in p.parts}
    save(A / 'archive-manifest.json', {'algorithm': 'sha256', 'files': files, 'self_excluded': True,
                                      'status': summary['status'], 'failed_archive_not_repaired': True})
    print(json.dumps({'status': summary['status'], 'sessions': len(rows), 'requests': requests_started,
                      'test_scored': 0, 'integrity': integrity}, ensure_ascii=False))


if __name__ == '__main__':
    main()
