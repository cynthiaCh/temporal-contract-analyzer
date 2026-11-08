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
    baselines = [row(A / f'baselines/auto{n}/archive', f'AUTO {n}', original, standards) for n in (1,2)]
    journal = read(A / 'actual-schedule.json', [])
    new = []
    for n in (1,2):
        root = A / f'runs/D1-revalidation-{n}/archive'
        if (root / 'receipt.json').exists():
            result = row(root, f'回验 {n}', original, standards)
            if result['valid_score']:
                score = read(root / 'score/stdout.json')
                result['vs_each_AUTO'] = []
                for j in (1,2):
                    comp = feedback(read(A / f'inputs/auto{j}/score.json'), [score], standards)['runs'][0]
                    result['vs_each_AUTO'].append({'baseline':j,'improvements':[x['effect'] for x in comp['improvements']],
                                                   'regressions':[x['effect'] for x in comp['regressions']],
                                                   'retained_success_count':len(comp['retained_original_successes'])})
            new.append(result)
    slots = []
    for name in read(A / 'protocol.json')['schedule']:
        r = next((r for r in journal if r['slot']==name), None)
        slots.append({'slot':name,'started':r is not None,'status':r.get('status') if r else 'NOT_STARTED',
                      'service_and_format_complete':r.get('candidate_complete') if r else None,
                      'valid_behavior_score':r.get('scoring_status')=='COLLECTED' if r else None})
    current_rows = [{'phase':r['phase'],'seconds':r.get('seconds'),
                     'usage':read(A / 'runs' / r['slot'] / 'archive/usage.json')} for r in journal]
    costs = {'existing_AUTO_only':aggregate(baselines),
             'new_reflection':aggregate([r for r in current_rows if r['phase']=='reflect']),
             'new_maintenance':aggregate([r for r in current_rows if r['phase']=='repair']),
             'new_total':aggregate(current_rows),
             'engineering':{'elapsed_batch_wall_seconds':time.time()-read(A / 'initial-state.json')['time'],
                            'offline_setup_seconds':read(A / 'prepared.json')['offline_setup_seconds'],
                            'tokens':None,'money':None,'note':'Engineering usage is not exposed; unknown is not zero.'}}
    valid = [r for r in new if r['valid_score']]
    content = read(A / 'content-review-result.json', {})
    content_ok = content.get('development_eligible', False)
    improvement = any(any(r['target_behaviors'].values()) or r['satisfied_count']>27 for r in valid)
    admission = {'eligible_for_future_research_freeze':content_ok and improvement,
                 'production_admitted':False,'both_full_passes_required':False,
                 'all_regressions_recorded':True,'no_test_or_next_reflection':True,
                 'reason':'Content supported and observed target/overall development improvement.' if content_ok and improvement else 'No qualifying supported development improvement established.'}
    counts = {'planned':3,'started':len(journal),'not_started':3-len(journal),
              'complete_model_sessions':sum(bool(r.get('candidate_complete')) for r in journal),
              'incomplete_model_sessions':sum(not bool(r.get('candidate_complete')) for r in journal),
              'valid_new_behavior_scores':len(valid),
              'whole_task_passes_new':sum(r['whole_task_pass'] for r in valid) if valid else None}
    summary = {'status':'completed' if (A / 'completion.json').exists() else 'stopped',
      'scope':'D1 same-case, R03-only bounded experience evolution; no test or transfer claim',
      'stop':read(A / 'stop.json'),'counts':counts,'slots':slots,
      'r03_content_review':content,'unchanged':read(A / 'unchanged-check.json'),
      'lineage':read(A / 'lineage.json'),'baselines':baselines,'revalidations':new,
      'admission':admission,'costs':costs,
      'new_effects_known':bool(valid),'new_regressions':{r['label']:r['original_successes_lost'] for r in valid} if valid else None}
    save(A / 'summary.json',summary); save(A / 'costs.json',costs); save(A / 'admission.json',admission)
    save(A / 'behavior-vectors.json',{'baselines':baselines,'new':new,
        'unstarted':[{'slot':s['slot'],'behavior_vector':{x['effect']:None for x in standards}} for s in slots if not s['started']],
        'unstarted_is_behavior_failure':False})
    lines = ['本轮 R03 局部经验演化与 D1 开发回验已'+('完成。' if (A / 'completion.json').exists() else '按停止规则结束。'), '',
      '固定父候选：research/d1-rule-object-validation-20261109_001011/。仅允许替换 R03 规则对象，原 R01/R02/R04/R05 的正文和元数据、机制适用字段、未决说明均保持不变。未重新生成完整经验、改写其他条款或引入旧 E2。', '',
      '反思输出为一个沿用现有字段与合法 ID 枚举的 verification 规则对象。Python 复制父对象并仅替换第三项，确定性编号与渲染；完整新候选和正文都是程序派生产物，原始模型输出仅为 r03-raw.txt 中的 R03。lineage.json、candidate-differences.json、experience.diff、derivation.json 保存父版本、精确差异和摘要。', '',
      '离线核查复用现有运行器、隔离、计量及 schema；检查父评审与结构核查接口兼容、支持依据不静默放宽、修改范围受限、部分输出拒绝，以及固定基线的输入/权限/评分版本一致。结果见 offline-checks.log、freeze.json 和 condition-audit.json。', '',
      '内容核查为执行 Agent 的 AI 辅助核查，不是独立人工批准。其他四条及机制前提的评审复用父批已有 AI 核查；对 R03 的新正文与引用逐项核对。R04 的已消费取消仍按已进入工作上下文解释，网络模式例外保持父批边界。未把复用评审包装为独立复核。', '',
      '1. R03 是否纠正过度收紧与字段放置：'+('通过 AI 辅助核查，具体原文与依据见 semantic-review.json。' if content_ok else '尚未通过；见候选拒绝与 semantic-review.json，原始输出未修补。'), '',
      '2. 其余规则是否保持不变：'+('程序已确认四条完整规则对象、机制适用字段及未决说明完全不变。' if read(A / 'unchanged-check.json') else '尚未形成合格合成候选，保持父材料不变。'), '',
      '3. 两项目标与整题结果：有效新评分 '+str(len(valid))+' 份；完整结果如下。没有评分的槽位保持未知，不计为行为失败。', '',
      '4. 新行为损失：所有相对原始版本和两份 AUTO 的损失均列于 summary.json、behavior-vectors.json 与下表，不能因目标改善而省略。未启动维护时损失未知。', '',
      '|条件|评分|满足关系|整题|缓存后台保留|延后消费保留|相对原始版本损失|',
      '|---|---|---|---|---|---|---|']
    for r in baselines+new:
        lines.append('|{}|{}|{}|{}|{}|{}|{}|'.format(r['label'],'有效' if r['valid_score'] else '未评分',
          str(r['satisfied_count'])+'/29' if r['valid_score'] else '—',r['verdict'] or '—',
          r['target_behaviors'][TARGETS[0]],r['target_behaviors'][TARGETS[1]],
          ', '.join(r['original_successes_lost']) if r['original_successes_lost'] else ('无' if r['valid_score'] else '未知')))
    for n in (1,2):
        if not any(r['label']==f'回验 {n}' for r in new):lines.append(f'|回验 {n}|未启动|—|—|—|—|—|')
    lines += ['', '全部 29 项：', '', '|关系|AUTO 1|AUTO 2|回验 1|回验 2|','|---|---|---|---|---|']
    for rel in standards:
        key=rel['effect']; cells=[]
        for r in baselines:cells.append('通过' if r['behavior_vector'][key]==rel['expected'] else '失败')
        for n in (1,2):
            r=next((r for r in new if r['label']==f'回验 {n}'),None)
            cells.append(('通过' if r['behavior_vector'][key]==rel['expected'] else '失败') if r and r['valid_score'] else '未评分')
        lines.append('|'+key+'|'+'|'.join(cells)+'|')
    lines += ['', '相对每份 AUTO 的完整得失：', '']
    for r in new:lines.append(r['label']+': '+json.dumps(r.get('vs_each_AUTO'),ensure_ascii=False))
    lines += ['', '成本（旧基线与新增分开）：', '', '|范围|会话|请求|已知 tokens|未知用量请求|工具|秒|','|---|---|---|---|---|---|---|']
    for label,key in [('旧 AUTO','existing_AUTO_only'),('新反思','new_reflection'),('新维护','new_maintenance'),('本次新增合计','new_total')]:
        c=costs[key];lines.append('|{}|{}|{}|{}|{}|{}|{}|'.format(label,c['sessions_started'],c['requests_started'],c['known_usage_subtotal']['total_tokens'],c['unknown_usage_requests'],c['tool_attempts'],round(c['seconds'],3) if c['seconds'] is not None else None))
    lines += ['', '工程准备 tokens 和金额无法从接口读取，保持 null；工程时间与完整分项见 costs.json。未知请求用量不补零。父批反思成本未混入本次新增成本或基线成本。', '',
      '模型固定为反思 gpt-5.6-terra / medium、维护 gpt-5.6-terra / low；分别 12/24 请求，每会话 600 秒，并发 1，总请求上限 60。每次维护从相同原始候选独立开始，只追加冻结派生正文，不交付训练评分、账本、标准答案或参考补丁；仅有效完整候选按原 29 项规则评分一次。', '',
      '实际槽位与停止：'+json.dumps({'counts':counts,'stop':read(A / 'stop.json')},ensure_ascii=False), '',
      '候选后续冻结资格：'+admission['reason']+' 当前未更新任何生产经验库，也未开展测试集运行。', '',
      '本轮只作同题开发诊断：不能凭两次开发回验宣称稳定效果、独立测试收益、同源迁移或泛化。未进行下一轮反思、额外评委、分类、提取、连接预跑、重试或补跑。完成后停止。', '',
      '推荐 Git commit subject:', '', '`research: evaluate a bounded R03-only experience revision on D1`', '',
      '推荐 Git commit body:', '', '```text',
      'Revise only R03 with one bounded reflection using frozen D1 evidence.',
      'Keep the parent protocol and all other rules and mechanism fields intact.',
      'Archive raw revision, deterministic synthesis, exact scope checks and',
      'AI-assisted evidence review before up to two isolated repair sessions.',
      'Record every behavior, regression, known cost and unknown/unstarted slot',
      'without test runs, retries, baseline reruns or production registry updates.', '```', '',
      '未创建提交，未修改父批或其他历史记录，未修改全局配置。']
    (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
    initial=read(A/'initial-state.json')
    sources_ok=all(sha(x['source'])==x['sha256'] for x in read(A/'provenance.json')['copied'])
    frozen_ok=all(sha(p)==h for p,h in read(A/'freeze.json')['files'].items())
    integrity={'sources_unchanged':sources_ok,'frozen_files_unchanged':frozen_ok,
      'preexisting_staged_diff_preserved':hashlib.sha256(subprocess.check_output(['git','diff','--cached','--binary'],cwd=REPO)).hexdigest()==initial['cached_diff_sha256'],
      'preexisting_unstaged_diff_preserved':hashlib.sha256(subprocess.check_output(['git','diff','--binary'],cwd=REPO)).hexdigest()==initial['unstaged_diff_sha256'],
      'head_unchanged':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==initial['head'],
      'budget_ok':len(journal)<=3 and costs['new_total']['requests_started'] is not None and costs['new_total']['requests_started']<=60,
      'test_sessions':0,'new_AUTO_baselines':0}
    save(A/'integrity.json',integrity)
    hashes={str(p.relative_to(A)):sha(p) for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='ARTIFACTS.sha256'}
    (A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(hashes.items())))
    print(json.dumps({'status':summary['status'],'counts':counts,'costs':costs,'integrity':integrity},ensure_ascii=False),flush=True)


if __name__ == '__main__':main()


