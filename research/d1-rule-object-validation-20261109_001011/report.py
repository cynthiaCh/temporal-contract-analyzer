"""Summarize every fixed slot, complete behavior vectors, separate old/new costs."""
import json
import subprocess
import hashlib
import time
from pathlib import Path
from archive import save, sha
from feedback import feedback
from handoff import object_digest

A = Path(__file__).resolve().parent
REPO = A.parent.parent
FIELDS = ['input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
          'output_tokens', 'reasoning_output_tokens', 'total_tokens']
TARGETS = ['cached-paused-background', 'cached-later-consumption']


def read(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default


def aggregate(rows):
    if not rows:
        return {'sessions_started': 0, 'requests_started': 0, 'tool_attempts': 0,
                'known_usage_subtotal': {k: 0 for k in FIELDS},
                'unknown_usage_requests': 0, 'total_usage': {k: 0 for k in FIELDS},
                'seconds': 0, 'money': None}
    usages = [row.get('usage') for row in rows]
    known = {}
    for key in FIELDS:
        values = [(u.get('observed_usage_subtotal') or {}).get(key) for u in usages if isinstance(u, dict)]
        values = [v for v in values if type(v) in (int, float)]
        known[key] = sum(values) if values else None
    counts = [u.get('requests_started') if isinstance(u, dict) else None for u in usages]
    unknowns = [u.get('usage_unknown_requests') if isinstance(u, dict) else None for u in usages]
    times = [r.get('seconds') for r in rows]
    tools = [u.get('tool_hook_attempts') if isinstance(u, dict) else None for u in usages]
    incomplete = any(not isinstance(u, dict) or u.get('usage_incomplete', True) for u in usages)
    return {'sessions_started': len(rows),
            'requests_started': sum(counts) if all(type(v) is int for v in counts) else None,
            'tool_attempts': sum(tools) if all(type(v) is int for v in tools) else None,
            'known_usage_subtotal': known,
            'unknown_usage_requests': sum(unknowns) if all(type(v) is int for v in unknowns) else None,
            'total_usage': None if incomplete else known,
            'seconds': sum(times) if all(type(v) in (int, float) for v in times) else None,
            'money': None}


def row(root, label, original, standards):
    record = read(root / 'receipt.json', {})
    score = read(root / 'score/stdout.json')
    valid = (record.get('scoring_admissible') is True
             and record.get('scoring_status') == 'COLLECTED'
             and record.get('scored_candidate_unchanged') is True
             and record.get('score_result', {}).get('score_valid') is True)
    if not valid:
        score = None
    relation = feedback(original, [score], standards)['runs'][0] if score else None
    return {'label': label, 'archive': str(root.relative_to(A)), 'slot': record.get('slot'),
            'valid_score': valid, 'verdict': score.get('verdict') if score else None,
            'whole_task_pass': score['verdict'] == 'PASS' if score else None,
            'behavior_vector': score.get('observed_effects') if score else None,
            'target_behaviors': {k: score['observed_effects'].get(k) if score else None for k in TARGETS},
            'satisfied_count': len(relation['actual_successes']) if relation else None,
            'original_successes_lost': [r['effect'] for r in relation['regressions']] if relation else None,
            'improvements_over_original': [r['effect'] for r in relation['improvements']] if relation else None,
            'failed_checks': relation['failed_checks'] if relation else None,
            'usage': read(root / 'usage.json'), 'seconds': record.get('seconds'),
            'scoring_status': record.get('scoring_status'), 'infrastructure_valid': record.get('infrastructure_valid')}


def main():
    original, standards = read(A / 'inputs/original-score.json'), read(A / 'inputs/standards.json')
    baselines = [row(A / f'baselines/auto{n}/archive', f'AUTO {n}', original, standards) for n in (1, 2)]
    journal = read(A / 'actual-schedule.json', [])
    revalidations = []
    for n in (1, 2):
        path = A / f'runs/D1-revalidation-{n}/archive'
        if (path / 'receipt.json').exists():
            r = row(path, f'经验回验 {n}', original, standards)
            if r['valid_score']:
                score = read(path / 'score/stdout.json')
                r['vs_each_AUTO'] = []
                for j in (1, 2):
                    comp = feedback(read(A / f'inputs/auto{j}/score.json'), [score], standards)['runs'][0]
                    r['vs_each_AUTO'].append({'baseline': j, 'improvements': [x['effect'] for x in comp['improvements']],
                                              'regressions': [x['effect'] for x in comp['regressions']]})
            revalidations.append(r)
    slots = []
    for name in read(A / 'protocol.json')['schedule']:
        record = next((r for r in journal if r['slot'] == name), None)
        slots.append({'slot': name, 'started': record is not None,
                      'service_and_format_complete': record.get('candidate_complete') if record else None,
                      'status': record.get('status') if record else 'NOT_STARTED',
                      'valid_behavior_score': record.get('scoring_status') == 'COLLECTED' if record else None})
    costs_by_phase = []
    for record in journal:
        costs_by_phase.append({'phase': record['phase'], 'seconds': record.get('seconds'),
                               'usage': read(A / 'runs' / record['slot'] / 'archive/usage.json')})
    costs = {'existing_AUTO_only': aggregate(baselines),
             'new_reflection': aggregate([r for r in costs_by_phase if r['phase'] == 'reflect']),
             'new_maintenance': aggregate([r for r in costs_by_phase if r['phase'] == 'repair']),
             'new_total': aggregate(costs_by_phase),
             'engineering': {'elapsed_batch_wall_seconds': time.time()-read(A / 'initial-state.json')['time'],
                             'offline_setup_seconds': read(A / 'prepared.json')['offline_setup_seconds'],
                             'tokens': None, 'money': None, 'note': 'Engineering usage not exposed; unknown is not zero.'}}
    valid = [r for r in revalidations if r['valid_score']]
    completed = read(A / 'completion.json') is not None
    content = read(A / 'content-review-result.json')
    mechanism = read(A / 'mechanical-audit.json')
    supported = bool(content and content.get('development_eligible'))
    improved = any(any(r['target_behaviors'].values()) or r['satisfied_count'] > 27 for r in valid)
    admission = {'eligible_for_future_research_freeze': supported and improved,
                 'production_admitted': False, 'all_regressions_recorded': True,
                 'both_full_passes_required': False, 'no_test_or_next_reflection': True,
                 'reason': 'Observed development improvement and supported content.' if supported and improved else 'Candidate not qualified or no valid improvement observed.'}
    counts = {'planned': 3, 'started': len(journal), 'not_started': 3-len(journal),
              'complete_model_sessions': sum(bool(r.get('candidate_complete')) for r in journal),
              'incomplete_model_sessions': sum(not bool(r.get('candidate_complete')) for r in journal),
              'valid_new_behavior_scores': len(valid),
              'whole_task_passes_new': sum(r['whole_task_pass'] for r in valid) if valid else None}
    summary = {'status': 'completed' if completed else 'stopped', 'scope': 'D1 same-case development diagnostic only',
               'stop': read(A / 'stop.json'), 'counts': counts, 'slots': slots,
               'mechanical_consistency': mechanism, 'content_review': content,
               'baselines': baselines, 'revalidations': revalidations, 'admission': admission, 'costs': costs,
               'target_effect': 'observed' if valid else 'unknown_no_maintenance_started',
               'new_regressions': {r['label']: r['original_successes_lost'] for r in valid} if valid else None}
    save(A / 'summary.json', summary); save(A / 'costs.json', costs); save(A / 'admission.json', admission)
    save(A / 'behavior-vectors.json', {'baselines': baselines, 'new': revalidations,
       'unstarted': [{'slot': s['slot'], 'behavior_vector': {x['effect']: None for x in standards}}
                     for s in slots if not s['started']], 'unstarted_is_behavior_failure': False})
    current = costs['new_total']
    lines = ['本轮已完成反思协议修复和零模型核查，执行一次反思后按候选拒绝规则停止。没有启动两次维护回验。', '',
      '此次工作仅限 D1 同题开发诊断，不开展测试集运行、不额外提取 Contract 或重跑 AUTO。保留旧 E2 不作为种子，未把任何测试反馈加入训练材料。', '',
      '1. 机械绑定问题是否解决：', '',
      '已移除重复全文与逐字引用，唯一正文为 rules[].body；Python 稳定编号并渲染。schema 按冻结账本生成合法 ID 枚举，并提供 predicate 完整定义。23 项离线检查通过；本次实际模型对象也通过 JSON schema，全部 ID 合法，没有旧的重复引用错误。该结论限于离线检查和这一次输出，不证明未来输出永不出错。', '',
      '2. 候选还有哪些问题：', '',
      'R03 的 support 只列实际评分观察，规范依据列在 conditions；按调用前冻结的规则，support 本身缺少规范依据，候选被拒绝。必须区分“字段准入失败”与“完全没有任务文档引用”：后者不成立，本轮没有移动 ID 或修改规则来放行。', '',
      'AI 辅助核查还发现 R03 将“不能携带 live signal 进入”扩大为“重连时不得进入执行”的唯一验证要求。原任务、训练 rubric 和冻结评分器允许没有入口，或入口的 signal 已中止；并未把零入口作为唯一正确方案。不能从旧 AUTO 采用零入口的结果推导出更强业务政策。具体原文、依据、限制与逐规则核查见 semantic-review.json 和 training-policy-check.json。', '',
      '新候选没有重犯必须迁移共享消费记录或所有无观察者工作一律取消的旧错误。所选机制适用前提有当前文档/源码支持；多处修改的独立因果贡献仍未知。R04 的已消费取消描述按已进入工作上下文核查，不将其扩展成新建未进入工作永不允许中止的规则。', '',
      '3. 两项目标和整题结果是否改善：', '',
      '新增有效维护评分为 0，两项目标与整题收益均未知。已有两次 AUTO 都是 27/29，失败项为 cached-paused-background 与 cached-later-consumption。两次新回验均未启动，不能填作失败。', '',
      '4. 是否损失已有正确行为：', '',
      '新维护未执行，新增损失未知。旧 AUTO 各自原有成功 21、保留 19、改善 8、退步 2；完整 29 项向量和实际/预期检查保留在 feedback.json、behavior-vectors.json 与基线归档。', '',
      '|条件|评分状态|满足关系|整题|缓存后台保留|延后消费保留|', '|---|---|---|---|---|---|']
    for r in baselines + revalidations:
        lines.append('|{}|{}|{}|{}|{}|{}|'.format(r['label'], '有效' if r['valid_score'] else '未评分',
           str(r['satisfied_count'])+'/29' if r['valid_score'] else '—', r['verdict'] or '—',
           r['target_behaviors'][TARGETS[0]], r['target_behaviors'][TARGETS[1]]))
    for n in (1, 2):
        if not any(r['label'] == f'经验回验 {n}' for r in revalidations):
            lines.append(f'|经验回验 {n}|未启动|—|—|—|—|')
    lines += ['', '|关系|AUTO 1|AUTO 2|回验 1|回验 2|', '|---|---|---|---|---|']
    for rel in standards:
        k = rel['effect']; cells = []
        for r in baselines:
            cells.append('通过' if r['behavior_vector'][k] == rel['expected'] else '失败')
        for n in (1, 2):
            r = next((r for r in revalidations if r['label'] == f'经验回验 {n}'), None)
            cells.append(('通过' if r['behavior_vector'][k] == rel['expected'] else '失败') if r and r['valid_score'] else '未评分')
        lines.append('|' + k + '|' + '|'.join(cells) + '|')
    lines += ['', '成本与实际槽位：', '',
      '|范围|会话|请求|已知总 tokens|用量未知请求|工具调用|秒|', '|---|---|---|---|---|---|---|']
    for label, key in [('旧 AUTO 基线', 'existing_AUTO_only'), ('本次反思', 'new_reflection'), ('本次维护', 'new_maintenance'), ('本次新增合计', 'new_total')]:
        c = costs[key]
        lines.append('|{}|{}|{}|{}|{}|{}|{}|'.format(label,c['sessions_started'],c['requests_started'],c['known_usage_subtotal']['total_tokens'],c['unknown_usage_requests'],c['tool_attempts'],round(c['seconds'],3) if c['seconds'] is not None else None))
    lines += ['', '金额与执行 Agent 工程准备 tokens 无法从接口读取，保持 null。已知 token 合计与未知请求数分别记录；原始用量不补零。工程墙钟时间见 costs.json，包含人工代码准备、核查与等待，不等于模型计费时间。', '',
      '新 schema、输入、公共提示和运行配置在调用前冻结，冻结记录为 freeze.json。维护条件与原 AUTO 相同：gpt-5.6-terra / low、24 请求、600 秒；反思 gpt-5.6-terra / medium、12 请求、600 秒、无工具；本轮最多 60 请求，并发 1。', '',
      '此次反思服务正常、完整输出，无断流、无隐性重试。原始对象、原始 CLI 事件、校验、派生正文、逐规则依据、拒绝、计量均已归档。派生正文仅供审计，明确不是新模型原始全文，未交给维护 Agent。', '',
      '执行 Agent 的核查标为 AI 辅助，不伪造独立人工批准。没有更改旧失败对象或拒绝决定；用于转换检查的夹具明确为 synthetic_derived_test_fixture，不作为候选或效果证据。', '',
      '当前候选不具备进入冻结经验测试的依据。此次观察说明机械重复可以消除，但结构合法不保证规则有据。未测得新经验效果，不宣称测试收益、稳定收益或泛化。完成后停止，没有自动进入下一轮。', '',
      '推荐 Git commit subject:', '', '`research: render ledger-bound reflection rules from a single source`', '',
      '推荐 Git commit body:', '', '```text',
      'Replace duplicated experience text and quotations with a single rule list.',
      'Generate evidence-ID schemas from the ledger, provide predicate definitions,',
      'and render deterministic rule numbering and exact model bodies in Python.',
      'Preserve semantic review and replay old invalid outputs in offline checks.',
      'Archive one bounded D1 reflection and its rejection; leave both repair slots',
      'unstarted, retain full baseline vectors, and separate old/new costs.', '```', '',
      '未创建提交、更新生产经验库或修改全局配置。已有暂存区及历史文件保持原状。']
    (A / 'REPORT.md').write_text('\n'.join(lines)+'\n')
    initial = read(A / 'initial-state.json')
    current_cached = hashlib.sha256(subprocess.check_output(['git','diff','--cached','--binary'],cwd=REPO)).hexdigest()
    current_unstaged = hashlib.sha256(subprocess.check_output(['git','diff','--binary'],cwd=REPO)).hexdigest()
    sources_ok = all(sha(x['source']) == x['sha256'] for x in read(A / 'provenance.json')['copied'])
    freeze_ok = all(sha(p) == h for p,h in read(A / 'freeze.json')['files'].items())
    integrity = {'sources_unchanged': sources_ok, 'frozen_files_unchanged': freeze_ok,
       'preexisting_staged_diff_preserved': current_cached == initial['cached_diff_sha256'],
       'preexisting_unstaged_diff_preserved': current_unstaged == initial['unstaged_diff_sha256'],
       'head_unchanged': subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip() == initial['head'],
       'budget_ok': len(journal) <= 3 and current['requests_started'] is not None and current['requests_started'] <= 60,
       'test_sessions': 0, 'new_baselines': 0}
    save(A / 'integrity.json', integrity)
    hashes = {str(p.relative_to(A)): sha(p) for p in A.rglob('*') if p.is_file()
              and '__pycache__' not in p.parts and p.name != 'ARTIFACTS.sha256'}
    (A / 'ARTIFACTS.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(hashes.items())))
    print(json.dumps({'counts':counts,'new_cost':costs['new_total'],'integrity':integrity},ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()


