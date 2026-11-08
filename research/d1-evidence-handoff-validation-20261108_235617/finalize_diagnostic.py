"""Summarize every fixed slot, complete behavior vectors, separate old/new costs."""
import json
import subprocess
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
    original = read(A / 'inputs/original-score.json')
    standards = read(A / 'inputs/standards.json')
    baselines = [row(A / f'baselines/auto{n}/archive', f'AUTO {n}', original, standards) for n in (1, 2)]
    journal = read(A / 'actual-schedule.json', [])
    new = []
    for n in (1, 2):
        root = A / f'runs/D1-revalidation-{n}/archive'
        if (root / 'receipt.json').exists():
            r = row(root, f'经验回验 {n}', original, standards)
            if r['valid_score']:
                score = read(root / 'score/stdout.json')
                r['vs_each_AUTO'] = []
                for j in (1, 2):
                    comparison = feedback(read(A / f'inputs/auto{j}/score.json'), [score], standards)['runs'][0]
                    r['vs_each_AUTO'].append({'baseline': j,
                        'improvements': [x['effect'] for x in comparison['improvements']],
                        'regressions': [x['effect'] for x in comparison['regressions']],
                        'retained_successes': [x['effect'] for x in comparison['retained_original_successes']]})
            new.append(r)
    all_slots = []
    for slot in read(A / 'protocol.json')['schedule']:
        rec = next((r for r in journal if r['slot'] == slot), None)
        all_slots.append({'slot': slot, 'started': rec is not None,
                          'session_valid': rec.get('candidate_complete') if rec else None,
                          'behavior_score_valid': rec.get('scoring_status') == 'COLLECTED' if rec else None,
                          'phase': 'reflect' if slot == 'D1-reflection' else 'repair',
                          'status': rec.get('status') if rec else 'NOT_STARTED'})
    current_cost_rows = []
    for rec in journal:
        root = A / 'runs' / rec['slot'] / 'archive'
        current_cost_rows.append({'phase': rec['phase'], 'usage': read(root / 'usage.json'), 'seconds': rec.get('seconds')})
    costs = {'existing_AUTO_only': aggregate(baselines),
             'new_reflection': aggregate([r for r in current_cost_rows if r['phase'] == 'reflect']),
             'new_maintenance': aggregate([r for r in current_cost_rows if r['phase'] == 'repair']),
             'new_total': aggregate(current_cost_rows),
             'engineering': {'elapsed_batch_wall_seconds': time.time() - read(A / 'initial-state.json')['time'],
                             'offline_setup_seconds': read(A / 'prepared.json')['offline_setup_seconds'],
                             'tokens': None, 'money': None, 'note': 'Execution-agent engineering usage not exposed; not zero.'}}
    review = read(A / 'semantic-review.json')
    rejection = read(A / 'candidate-rejection.json')
    completed = bool(read(A / 'completion.json'))
    valid_new = [r for r in new if r['valid_score']]
    content_ok = read(A / 'content-review-result.json', {}).get('semantic_status') == 'supported_by_execution_agent'
    target_improvements = any(any(r['target_behaviors'].values()) for r in valid_new)
    repair_improvement = any(r['satisfied_count'] > 27 for r in valid_new)
    eligible = content_ok and (target_improvements or repair_improvement)
    admission = {'candidate_eligible_for_future_research_freeze': eligible, 'production_admitted': False,
                 'content_review_AI_assisted': True, 'development_completed': completed,
                 'evidence_of_target_improvement': target_improvements, 'overall_repair_improved': repair_improvement,
                 'all_regressions': {r['label']: r.get('original_successes_lost') for r in new},
                 'no_both_pass_requirement': True,
                 'reason': 'Content reviewed and observed target/overall improvement; regressions retained for assessment.' if eligible else 'No qualifying content-supported development improvement established.',
                 'next_test_authorized_or_started': False}
    save(A / 'admission.json', admission)
    summary = {'status': 'completed' if completed else 'stopped',
        'scope': 'D1 same-case development diagnostic, no test/generalization claims',
        'stop': read(A / 'stop.json'), 'baselines': baselines, 'revalidations': new,
        'slots': all_slots, 'counts': {'planned': 3, 'started': len(journal),
          'valid_sessions': sum(bool(r.get('candidate_complete')) for r in journal),
          'invalid_sessions': sum(not bool(r.get('candidate_complete')) for r in journal),
          'not_started': 3 - len(journal), 'valid_new_behavior_scores': len(valid_new),
          'whole_task_passes_new': sum(r['whole_task_pass'] for r in valid_new) if valid_new else None,
          'content_rejected_reflections': int(rejection is not None)},
        'content_review': review, 'structural_rejection': rejection, 'admission': admission, 'costs': costs,
        'completion_vs_content': {'valid_model_completions': sum(bool(r.get('candidate_complete')) for r in journal),
                                 'reflection_candidate_accepted': content_ok,
                                 'note': 'Successful service/JSON completion does not mean usable experience.'}}
    save(A / 'summary.json', summary)
    save(A / 'behavior-vectors.json', {'baseline': baselines, 'new': new, 'unstarted_is_not_failure': True})
    save(A / 'costs.json', costs)
    lines = ['本次 D1 证据交接修复后的最小开发验证已' + ('完成。' if completed else '按停止规则结束。'), '',
       '本轮固定使用原 D1，不增加 AUTO 基线、提取、分类、评委或测试会话。比较基线按实际开始时间选择，见 baseline-selection.json。', '',
       '反思使用 gpt-5.6-terra / medium，维护使用 gpt-5.6-terra / low；分别最多 12/24 请求、600 秒，并发 1。源代码、任务、自动 Contract、工具、公共提示及原 29 项评分器均已离线核验并冻结。维护唯一有意新增的材料是未经润色的候选经验正文。', '',
       '本轮逐条核查为执行 Agent 的 AI 辅助核查，不是独立人工批准。已保存原始 CLI 事件、完整/部分模型消息、请求/工具事件、错误、工作区、补丁、原评分与计量。原始服务 wire body 若 CLI 未暴露则明确记为不可用，未伪造。', '',
       '|条件|有效评分|整题|满足关系|缓存后台保留|延后读取保留|相对原始版本损失|',
       '|---|---|---|---|---|---|---|']
    for r in baselines + new:
        targets = [str(r['target_behaviors'][k]) if r['valid_score'] else '未评分' for k in TARGETS]
        lines.append('|{}|{}|{}|{}|{}|{}|{}|'.format(r['label'], r['valid_score'], r['verdict'] or '未评分',
            str(r['satisfied_count']) + '/29' if r['valid_score'] else '—', targets[0], targets[1],
            ', '.join(r['original_successes_lost']) if r['original_successes_lost'] else ('无' if r['valid_score'] else '未知')))
    for n in (1, 2):
        if not any(r['label'] == f'经验回验 {n}' for r in new):
            lines.append(f'|经验回验 {n}|未启动|—|—|—|—|—|')
    lines += ['', '全部 29 项行为向量：', '', '|关系|' + '|'.join(r['label'] for r in baselines + new) + '|',
              '|---|' + '|'.join('---' for _ in baselines + new) + '|']
    for standard in standards:
        key = standard['effect']
        lines.append('|' + key + '|' + '|'.join(('通过' if r['behavior_vector'][key] == standard['expected'] else '失败') if r['valid_score'] else '未评分' for r in baselines + new) + '|')
    lines += ['', '结果与停止：', '', json.dumps(summary['counts'], ensure_ascii=False), '',
              '停止记录：' + json.dumps(summary['stop'], ensure_ascii=False), '',
              '候选内容核查：见 semantic-review.json、structural-review.json / candidate-rejection.json；候选原文和逐规则证据分别保存。', '',
              '后续冻结资格：' + admission['reason'], '',
              '成本（旧基线与本次新增分开）：', '', '```json', json.dumps(costs, ensure_ascii=False, indent=2), '```', '',
              '未知用量保持 null；未启动槽位不计行为失败。训练原有成功、改善和全部退步未因目标项改善而省略。', '',
              '本轮四项结论：', '',
              '1. 候选是否仍含无据政策或错误事实：AI 辅助核查未确认新正文重犯旧的“一律结算未开始工作”与“必须迁移消费记录”两项错误，正文也没有宣称旧补丁已整题修好。但候选仍无效：三条 rules.quote 全部不在候选正文中，而是引用任务或文档；conditions 和部分 preserve 是文字说明而不是协议要求的证据/约束 ID。requires 中 boundary_persistence、discard_boundary_policy、entry_snapshot 未获得其定义要求的 D1 依据。完整逐条结论见 semantic-review.json 和 candidate-audit.json。', '',
              '2. 两项目标是否改善：新回验有效评分为 ' + str(len(valid_new)) + '。没有新有效评分时，改善未知，不能把旧基线结果当作新经验收益。', '',
              '3. 是否引入其他损失：未执行维护时无法判断新修复的行为损失；旧两次 AUTO 已知损失分别完整列出。', '',
              '4. 是否值得进入后续冻结经验测试：' + ('符合本轮探索性候选条件，但仍需独立授权，不能宣称稳定收益。' if eligible else '当前不具备进入冻结经验测试的依据。') , '',
              '工程与解释边界：输出协议的 JSON 类型和长度检查通过，完整原始响应为 8,131 bytes，正文为 2,992 字符，未截断也未补全。失败发生在逐条证据交接核查，服务本身正常。当前 schema 对证据 ID 仅约束为字符串，动态绑定依赖本地核查；反思输入未包含所有适用前提名称的完整定义。后者可能影响解释，但不能据此断言模型产生错误的原因。没有在观察输出后修改 prompt、schema 或候选来放行。', '',
              '模型把“多处修改没有隔离因果”标为 policy，把“尚未有完整已验证修复”标为 applicability。这些标签本身不证明核心业务冲突；执行 Agent 将其解释为因果验证与开发范围限制。此次拒绝以真实的文本/证据绑定错误为依据，不以这些标签机械判错。', '',
              '本轮只有同题开发观察；即使结果改善，也不能单凭该轮证明交接修复有稳定因果收益、独立测试收益或同源跨语言迁移。没有测试案例被运行；后续测试不自动启动。', '',
              '推荐 commit subject: research: archive rejected D1 evidence-handoff reflection', '',
              '推荐 commit body:', '', '```text',
              'Verify and reuse the latest two condition-matched D1 AUTO baselines.',
              'Run one bounded reflection with grounded feedback and rejected-clause critique.',
              'Preserve raw output and record AI-assisted rule-by-rule evidence review.',
              'Stop after invalid text/evidence bindings; leave both repair slots unstarted.',
              'Archive baseline behavior vectors, raw candidate, rejection evidence and',
              'separate old/new costs without retries, test runs or production updates.', '```', '',
              '未创建 Git 提交，未更新生产经验库，未修改历史实验或全局配置。']
    (A / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    provenance = read(A / 'provenance.json')
    sources_unchanged = all(sha(p['source']) == p['sha256'] for p in provenance['copied'])
    frozen = read(A / 'freeze.json')
    frozen_unchanged = all(sha(p) == h for p, h in frozen['files'].items())
    tracked_diff = subprocess.check_output(['git', 'diff', 'HEAD', '--name-only'], cwd=REPO, text=True)
    save(A / 'integrity.json', {'sources_unchanged': sources_unchanged, 'frozen_files_unchanged': frozen_unchanged,
         'tracked_diff': tracked_diff, 'initial_head': read(A / 'initial-state.json')['head'],
         'current_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
         'budget_ok': len(journal) <= 3 and (costs['new_total']['requests_started'] or 0) <= 60,
         'test_sessions': 0, 'new_baselines': 0, 'engineering_usage_unknown': True})
    hashes = {str(p.relative_to(A)): sha(p) for p in A.rglob('*') if p.is_file()
              and '__pycache__' not in p.parts and p.name != 'ARTIFACTS.sha256'}
    (A / 'ARTIFACTS.sha256').write_text(''.join(h + '  ' + p + '\n' for p, h in sorted(hashes.items())))
    print(json.dumps({'status': summary['status'], 'counts': summary['counts'], 'costs': costs,
                       'integrity': {'sources': sources_unchanged, 'freeze': frozen_unchanged}}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
