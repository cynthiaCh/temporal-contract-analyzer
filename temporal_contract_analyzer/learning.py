"""Feedback-derived candidate memory. Never a frozen source-analysis layer."""
import json
import re

from . import archive
from .core import EvidenceError, canonical, sha

RECIPES = {
    'effect-separation': {
        'title': '分别核查历史记录与当前显示的有效性条件',
        'question': '记录、审计、显示、通知是否属于同一生命周期？分别核查哪些已接纳工作应继续、哪些结果不再更新界面。不要把一个取消或新鲜度守卫直接套到所有副作用上；从当前源码与要求确认。',
    },
    'boundary-coverage': {
        'title': '补查暂停、重入、清理与后续访问的组合',
        'question': '在当前源码中分别检查操作开始、回调完成、关闭、切换、重开与重试时的状态归属。构造至少两个可行顺序，并检查修复有没有破坏需要保留的行为。失败反馈不是业务要求的替代证据。',
    },
}


def inventory_key(inventory):
    return sha(canonical(inventory).encode('utf-8'))


def list_lessons(store=None, case_id=None, input_inventory_sha256=None, task_sha256=None):
    items = []
    for path in (archive.store_path(store)/'lessons').glob('l-*.json'):
        try:
            item = json.loads(path.read_text(encoding='utf-8'))
            if (not isinstance(item,dict) or item.get('schema_version')!='temporal-failure-lesson-1'
                    or item.get('id')!=path.stem or item.get('status')!='candidate'
                    or any(not isinstance(item.get(k),str) for k in ('case_id','input_inventory_sha256','task_sha256','created_at'))
                    or not isinstance(item.get('source'),dict)
                    or any(not isinstance(item['source'].get(k),str) for k in ('experiment_id','evaluation_id','report_id'))
                    or not isinstance(item.get('recipes'),list) or not item['recipes']
                    or any(not isinstance(r,str) or r not in RECIPES for r in item['recipes'])):
                raise EvidenceError('Invalid candidate lesson schema')
        except (OSError,ValueError,TypeError,KeyError) as error:
            raise EvidenceError('无法读取候选经验 '+path.name+': '+str(error)) from error
        if case_id is not None and item['case_id'] != case_id:
            continue
        if input_inventory_sha256 is not None and item['input_inventory_sha256'] != input_inventory_sha256:
            continue
        if task_sha256 is not None and item.get('task_sha256') != task_sha256:
            continue
        items.append(item)
    return sorted(items, key=lambda item:(item['created_at'], item['id']), reverse=True)


def learn(workbench, experiment_id):
    folder = workbench.folder(experiment_id)
    manifest = json.loads((folder/'manifest.json').read_text())
    case_id = (manifest.get('case') or {}).get('id')
    if not case_id or manifest['status'] not in {'completed','failed','cancelled','timed_out','interrupted'}:
        raise EvidenceError('只能从已结束且已评分的案例实验生成候选经验')
    latest = workbench.latest_evaluation(experiment_id)
    if latest is None:
        raise EvidenceError('没有已保存的行为验证结果')
    evaluation = json.loads(latest.read_text())
    if evaluation.get('calibration_verdict') != 'PASS':
        raise EvidenceError('参考校准未通过；验证异常不作为语义失败经验')
    failures = []
    for job in manifest['jobs']:
        row = evaluation['jobs'].get(job['id'], {})
        if job['status'] != 'completed' or row.get('status') != 'failed':
            continue
        if not re.fullmatch(r'j-[0-9]+', job['id']):
            raise EvidenceError('Invalid archived job ID')
        outcome = json.loads((latest.parent/job['id']/'oracle/stdout.json').read_text())
        if outcome.get('verdict') != row.get('verdict') or outcome['verdict'] not in {'UNDERREACH','OVERREACH','UNDERREACH_AND_OVERREACH'}:
            raise EvidenceError('评分摘要与保存的验证结果不一致')
        from .case_evaluation import scenario_progress
        progress = scenario_progress(outcome)
        failures.append(dict(job_id=job['id'], condition=job['condition'], verdict=outcome['verdict'],
                             scenarios=[] if not progress else [dict(name=s['name'], failed_assertions=s['failed_assertions'])
                                 for s in progress['items'] if s['status']=='failed'],
                             missing_required_effects=outcome.get('missing_required_effects', []),
                             observed_forbidden_effects=outcome.get('observed_forbidden_effects', [])))
    if not failures:
        return dict(lessons=[], note='没有可学习的已评分语义失败；未生成经验')
    assertion_names = [name for f in failures for s in f['scenarios'] for name in s['failed_assertions']]
    recipes = ['effect-separation'] if any(re.search(r'audit|history|record', name, re.I) for name in assertion_names) else []
    recipes.append('boundary-coverage')
    lesson_id = 'l-'+sha((experiment_id+'\n'+evaluation['id']).encode())[:20]
    lesson = dict(schema_version='temporal-failure-lesson-1', id=lesson_id, status='candidate',
                  created_at=evaluation['completed_at'], case_id=case_id,
                  input_inventory_sha256=inventory_key(manifest['input_files']),
                  task_sha256=sha(manifest['task'].encode('utf-8')),
                  source=dict(experiment_id=experiment_id, evaluation_id=evaluation['id'], report_id=manifest['report_id']),
                  feedback=failures, recipes=recipes,
                  qualification='根据已评分失败生成的候选经验，尚未证明原因或泛化；仅用于同案例同输入的开发重试，不是独立验证。')
    target = archive.store_path(workbench.store)/'lessons'/(lesson_id+'.json')
    if target.exists():
        saved = json.loads(target.read_text())
        if saved != lesson:
            raise EvidenceError('已有经验内容不同；拒绝覆盖')
    else:
        archive.atomic_json(target, lesson)
    return dict(lessons=[lesson], note='已保存候选经验；原评分和扫描规则未修改')


def review_material(report_id, lessons, store=None, max_chars=6000):
    """Use learned inspection priorities to select current source, not oracle data."""
    from .context import merge_ranges
    if type(max_chars) is not int or not 1 <= max_chars <= 6000:
        raise EvidenceError('学习上下文预算必须为 1–6000 个代码字符')
    report = json.loads(archive.artifact(report_id, 'report.json', store))
    sources = archive.read_sources(report_id, store)
    recipes = sorted({recipe for lesson in lessons for recipe in lesson['recipes']})
    if any(recipe not in RECIPES for recipe in recipes):
        raise EvidenceError('Unknown candidate lesson recipe')
    evidence = {eid for finding in report['findings'] for eid in finding['evidence']}
    selected_files = {file['path'] for file in report['files'] for event in file['events'] if event['id'] in evidence}
    candidates = []
    for file in report['files']:
        text = sources[file['path']]
        lines = text.splitlines(keepends=True)
        record = [i for i,line in enumerate(lines,1) if re.search(r'\b(?:record\w*|audit\w*|history\w*|persist\w*|save\w*)\b',line,re.I)]
        display = [i for i,line in enumerate(lines,1) if re.search(r'\b(?:receive\w*|show\w*|display\w*|render\w*|publish\w*|notify\w*)\b',line,re.I)]
        if 'effect-separation' in recipes and record and display:
            hits = sorted(set(record+display))
            priority = (0 if file['path'] not in selected_files else 1, 0, file['path'])
        else:
            hits = sorted({e['line'] for e in file['events'] if e['id'] in evidence})
            priority = (1, 1, file['path'])
        for line in hits:
            # Prefer enclosing top-level functions so callback arguments and
            # their distinct effects are visible together. This is a source
            # search candidate, not recovered callback dataflow.
            functions = [f for f in file['functions'] if f['line']<=line<=f['end_line'] and f.get('parent')=='<module>']
            function = min(functions,key=lambda f:f['end_line']-f['line']) if functions else None
            start,end = (function['line'],function['end_line']) if function else (max(1,line-2),min(len(lines),line+2))
            candidates.append((priority,dict(file=file['path'],start_line=start,end_line=end,kind='lesson-context',
                reasons=[dict(kind='learned-inspection',recipe='effect-separation' if record and display and 'effect-separation' in recipes else 'boundary-coverage')])) )
    snippets, omitted = [], []
    for _,candidate in sorted(candidates,key=lambda pair:(pair[0],pair[1]['start_line'],pair[1]['end_line'])):
        proposed = merge_ranges(snippets+[candidate],sources)
        if sum(len(s['code']) for s in proposed)>max_chars:
            gap=dict(file=candidate['file'],start_line=candidate['start_line'],end_line=candidate['end_line'],reason='budget-limit')
            if gap not in omitted:omitted.append(gap)
        else:
            snippets = proposed
    packet = dict(schema_version='temporal-learned-review-1', report_id=report_id,
                  input_sha256=report['input_sha256'], lesson_ids=[lesson['id'] for lesson in lessons],
                  recipes=recipes, snippets=snippets, omitted=omitted,
                  code_chars=sum(len(s['code']) for s in snippets), max_code_chars=max_chars,
                  qualification='反馈辅助的开发重试；候选检索策略尚未证明有效；不属于独立或盲测条件。')
    lines = ['# Feedback-informed development review', '', packet['qualification'], '',
             'Candidate lesson IDs: '+', '.join(packet['lesson_ids']),
             'Source snapshot: '+packet['input_sha256'], '',
             'These questions were selected from prior failed development runs. They are hypotheses, not requirements. '
             'Use only the current candidate source and visible task to decide which behavior must be preserved.', '']
    for recipe in recipes:
        lines += ['## '+RECIPES[recipe]['title'], '', RECIPES[recipe]['question'], '']
    lines += ['## Current source inspection candidates', '',
              'Selected by identifier-family search and source ranges, not proven caller/argument dataflow. '
              'Unselected files and dynamic relationships remain unchecked.', '']
    for snippet in snippets:
        fence = '`'*max(3,max((len(s) for s in re.findall(r'`+',snippet['code'])),default=0)+1)
        lines += ['### '+snippet['file']+':'+str(snippet['start_line'])+'–'+str(snippet['end_line']), '',
                  fence, snippet['code'].rstrip('\r\n'), fence, '']
    if omitted:lines += ['Some source ranges exceeded the code-character budget; review further source as needed.', '']
    if not snippets:lines += ['No source search candidates fit this recipe/budget; inspect the repository directly.', '']
    return packet, '\n'.join(lines)
