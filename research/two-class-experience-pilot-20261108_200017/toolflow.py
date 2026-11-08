"""Case-blind experience routing, shared prompts, and generic score differences."""
import hashlib
import json
from pathlib import PurePosixPath

PREDICATES = {
    'shared_lifetime': '修复对象的共享状态或工作可超出单个消费者寿命',
    'observer_lifetime': '多个消费者通过独立订阅/观察者身份共享同一工作',
    'attempt_resource': '每次执行尝试有独立取消资源或完成身份',
    'lazy_consumption': '读取取消能力会同步记录实际消费，且其归属可由当前证据核查',
    'async_resume': '暂停/重试工作可通过异步续行恢复',
    'deferred_batch': '修复对象将连续输入合并为可挂起的延迟工作',
    'boundary_persistence': '当前文档规定离开/提交边界返回前须结算已接纳的持久化义务',
    'entry_snapshot': '接纳的操作绑定入口选择/数据，后续重入不应改写其既成义务',
    'inline_reentry': '结算/通知会同步调用可重入导航/编辑的回调',
    'effect_lifetimes': '持久结果和当前界面反馈具有可区分的归属与有效期',
    'different_ownership_policy': '当前任务明确要求与共享状态及尝试分离相矛盾的所有权政策',
    'discard_boundary_policy': '当前任务明确允许丢弃目标的已接纳持久义务而非结算',
    'no_lazy_shared_mechanism': '当前证据明确表明修复对象没有共享状态与惰性消费机制',
}

POLICY = '原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def public_material(task, sources, ast, taxonomy):
    # No **metadata argument: case identity and evaluation data have no entry.
    return {'task': task, 'sources': sources, 'AST': ast, 'taxonomy': taxonomy,
            'predicates': PREDICATES}


def extraction_prompt(material):
    return '''你是候选可见材料的预分析员，只读 /workspace 的当前源码和文档。
一次完成候选自动Contract提取和机制主类分类，不修代码、不评分。
不得利用目录外身份、包名、案例ID、历史成绩或隐藏标准；相似词不是类别依据。
先实际读取源码正文和当前README/docs，AST只作线索；AST未命中不等于机制不存在。
主类按当前维护目标的机制选择T1/T2/T3/T4，可附副标签或unknown。
Contract只包含当前任务/文档有据义务；实现缺陷本身不否认机制存在。
对下面每个predicate逐一输出known/unknown/contradicted；known表示条件存在且有据，
contradicted表示有据明确不成立，unknown表示不足。排除政策不存在不能凭沉默推断。
所有known/contradicted事实附当前局部文件、1起始行号和逐字单行quote；unknown可空证据。
事实只针对维护对象；不要因相邻预览等另一对象有某政策就赋给维护对象。
不使用shell循环之外的执行/写入/测试工具，只允许候选读命令。
最终唯一外层字段report是一个JSON字符串，其解析后的对象严格为：
{"contract":"可独立交付的中文Contract正文；不含类别/路由信息", "primary_class":"T1|T2|T3|T4|unknown",
 "secondary_tags":[], "evidence":[{"file":"src/...","line":1,"quote":"逐字单行文本"}],
 "facts":[{"predicate":"固定key","state":"known|unknown|contradicted","evidence":[{"file":"...","line":1,"quote":"..."}]}]}
report总长不超过6000字符；Contract宜不超过1800字符，证据简短但确切。不另发分类调用。
候选公共材料（源码在/workspace，以下不含管理/评价身份）：
''' + canonical({k: v for k, v in material.items() if k != 'sources'})


def maintenance_prompt(task, contract, experience=None):
    common = task + '\n\n以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：\n' + contract
    common += '\n\n在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。\n' + POLICY
    return common if experience is None else common + '\n\n以下为冻结经验原文，按当前证据核查适用性：\n' + experience


def valid_evidence(evidence, sources):
    if not isinstance(evidence, list) or not evidence:
        return False
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {'file', 'line', 'quote'}:
            return False
        name, line, quote = item['file'], item['line'], item['quote']
        if not isinstance(name, str) or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
            return False
        lines = sources.get(name, '').splitlines()
        if type(line) is not int or not 1 <= line <= len(lines) or not quote or quote not in lines[line - 1]:
            return False
    return True


def validate_analysis(analysis, sources):
    if set(analysis) != {'contract', 'primary_class', 'secondary_tags', 'evidence', 'facts'}:
        return 'invalid_or_invisible_analysis_fields'
    if not isinstance(analysis['contract'], str) or not isinstance(analysis['facts'], list):
        return 'invalid_analysis_types'
    if analysis['primary_class'] not in ['T1', 'T2', 'T3', 'T4', 'unknown']:
        return 'invalid_primary_class'
    if analysis['primary_class'] != 'unknown' and not valid_evidence(analysis['evidence'], sources):
        return 'primary_class_without_source_evidence'
    seen = set()
    for fact in analysis['facts']:
        if set(fact) != {'predicate', 'state', 'evidence'} or fact['predicate'] not in PREDICATES:
            return 'invalid_fact_or_invisible_fields'
        if fact['predicate'] in seen:
            return 'duplicate_or_conflicting_fact'
        seen.add(fact['predicate'])
        if fact['state'] not in ['known', 'unknown', 'contradicted']:
            return 'invalid_fact_state'
        if fact['state'] != 'unknown' and not valid_evidence(fact['evidence'], sources):
            return 'fact_without_source_evidence'
    return None


def freeze_entry(candidate, primary):
    if set(candidate) != {'text', 'requires', 'excludes'}:
        raise ValueError('reflection candidate schema')
    if not candidate['text'].strip() or not candidate['requires']:
        raise ValueError('empty text or applicability')
    for key in ['requires', 'excludes']:
        if not isinstance(candidate[key], list) or any(x not in PREDICATES for x in candidate[key]):
            raise ValueError('unknown applicability predicate')
    if set(candidate['requires']) & set(candidate['excludes']):
        raise ValueError('applicability conflict')
    entry = {**candidate, 'version': 'pilot-1', 'primary_class': primary,
             'text_sha256': digest(candidate['text'])}
    entry['sha256'] = digest(canonical(entry))
    return entry


def route(analysis, sources, library):
    # Only data used below is accepted. No case/cluster/history/oracle arguments.
    def fallback(reason, checks=None):
        return {'condition': 'AUTO', 'reason': reason, 'selected': None,
                'checks': checks or [], 'primary_class': analysis.get('primary_class', 'unknown')}
    invalid = validate_analysis(analysis, sources)
    if invalid:
        return fallback(invalid)
    if analysis['primary_class'] == 'unknown':
        return fallback('unknown_class')
    if not library:
        return fallback('empty_library')
    allowed = {'text', 'requires', 'excludes', 'version', 'primary_class', 'text_sha256', 'sha256'}
    if any(set(e) != allowed for e in library):
        return fallback('invisible_or_invalid_registry_fields')
    entries = [e for e in library if e['primary_class'] == analysis['primary_class']]
    if not entries:
        return fallback('no_experience_for_class')
    facts = {x['predicate']: x for x in analysis['facts']}
    eligible, checks = [], []
    for entry in entries:
        check = {'sha256': entry['sha256'], 'premises': [], 'exclusions': []}
        copy = {k: v for k, v in entry.items() if k != 'sha256'}
        if entry['sha256'] != digest(canonical(copy)) or entry['text_sha256'] != digest(entry['text']):
            return fallback('digest_tampering', checks + [check])
        if not entry['requires']:
            return fallback('empty_applicability')
        for kind, field, expected in [('premises', 'requires', 'known'), ('exclusions', 'excludes', 'contradicted')]:
            for key in entry[field]:
                fact = facts.get(key, {'state': 'unknown', 'evidence': []})
                check[kind].append({'predicate': key, 'state': fact['state'], 'evidence': fact['evidence'],
                                    'satisfied': fact['state'] == expected})
        check['eligible'] = all(x['satisfied'] for x in check['premises'] + check['exclusions'])
        checks.append(check)
        if check['eligible']:
            eligible.append(entry)
    if len(eligible) > 1:
        return fallback('unresolved_multiple_experience_conflict', checks)
    if not eligible:
        return fallback('insufficient_or_contradictory_premises', checks)
    chosen = eligible[0]
    return {'condition': 'ROUTED', 'primary_class': analysis['primary_class'], 'reason': 'source_bound_premises',
            'selected': {'version': chosen['version'], 'sha256': chosen['sha256'],
                         'text_sha256': chosen['text_sha256']}, 'checks': checks}


def feedback(original, repairs, standards):
    """No diagnosis from assertion names; only structured actual/expected deltas."""
    out = {'standards': standards, 'original_effects': original['observed_effects'], 'runs': [],
           'explanations': [], 'unknown_causes': 'No causal diagnosis inferred from score labels. Read actual patches/source evidence.'}
    for score in repairs:
        row = {'verdict': score['verdict'], 'differences': [], 'existing_successes': [], 'improvements': [], 'regressions': []}
        for relation in standards:
            key, expected = relation['effect'], relation['expected']
            before, actual = original['observed_effects'].get(key), score['observed_effects'].get(key)
            item = {'relation': relation['description'], 'effect': key, 'expected': expected,
                    'original': before, 'actual': actual}
            if type(actual) is not bool or type(before) is not bool:
                row.setdefault('unknown_observations', []).append(item)
                continue
            if actual != expected:
                row['differences'].append(item)
            if before == expected:
                row['existing_successes'].append(item)
            if before != expected and actual == expected:
                row['improvements'].append(item)
            if before == expected and actual != expected:
                row['regressions'].append(item)
        row['assertion_differences'] = [
            {'schedule': name, 'assertion': a, 'runtimeError': schedule.get('runtimeError')}
            for name, schedule in score['schedules'].items() for a in schedule.get('assertions', [])
            if not a.get('passed', False)]
        out['runs'].append(row)
    return out


def reflection_prompt(payload):
    return '''只根据以下本批训练反馈反思一次，不能使用工具。生成一个可迁移经验候选，
不得读取或借用旧经验。材料含原始候选、原任务文档标准、两份实际修复/评分及公开交付。
参考实现/参考补丁不在输入。保留已经成功的关系，区分实际差异、退步与未知原因，
不要从断言名称臆造政策或根因。标准解释的执行Agent来源已记录。
经验必须包含适用前提、事件关系、验证动作、保留行为、不适用情况。
经验正文不得含案例ID、评分断言名、文件路径、程序专用字段/函数名或可复制补丁。
用一般时序机制和普通中文描述，不引用训练案例名字，不承诺未观察的效果。
适用性requires/excludes只用固定predicate key；至少一个requires；仅当有依据时设置
排除predicate。excludes只有被当前证据明确否定才可路由，未知会回退；不要把相邻
对象政策误用于维护对象。不要要求候选已经修好才适用。
最终唯一外层字段report为JSON字符串，解析后严格为
{"text":"完整经验原文", "requires":["predicate key"], "excludes":[]}。
report不超过6000字符。只生成一个候选，不另给修订版。
固定predicate词典：''' + canonical(PREDICATES) + '\n本批训练材料：\n' + canonical(payload)
