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
    return """只读 /workspace 当前源码和README/docs，一次输出候选自动Contract、机制主类、前提和语义自查。
最终响应严格遵循CLI提供的顶层结构化schema；直接输出JSON对象，不使用report包装、不把JSON编码为字符串、不用Markdown。
先实际读取源码正文，AST仅为线索；未命中不等于机制不存在。只允许候选读命令，不修代码、不测试、不联网。可用pwd、ls、rg、cat、nl、head、tail、wc、echo、printf和sed -n的数字行号p；可用2>/dev/null及|| true忽略缺失文档。不要使用find、python、执行脚本、cd或一般文件重定向。
只用原任务、当前源码/文档和以下公共材料，不按目录、包名、case/cluster身份、历史成绩或评分器选类别。
语义核查：
1. Repair/Fix之后可能描述待修的错误现象，不能把它改写成应保留的要求。区分reported_defect、requirement、source_fact和preservation_inference。
2. 原任务要求保留的行为要按当前证据的条件、否定和事件先后表述；不能扩大取消或完成义务。
3. 每个source_fact明确记录的实际读写对象/寿命(record_owner)，并给出源码owner_expression。记录归属与物理资源归属分别查证。不能因另一个对象有同名或未使用字段，就要求迁移正在使用的记录。不能只凭“对应某次执行”推断记录存放在哪里。
4. 区分历史持久结果和当前显示资格、取消请求和结算完成。Contract与source_fact必须相容；存在核心冲突则列在consistency，不能假装已核查。
每个predicate输出一次known/unknown/contradicted。known/contradicted需一条当前证据；unknown可空。
TASK是原任务虚拟编号文本，line从1开始。file用局部相对路径，quote必须是逐字连续的单行短片段，最长80字符；遇到压缩长行只引相关子串，绝不能复制整行。每个事实/claim只用一条证据。
Contract最多1400字符，claims最多4条，evidence最多3条；未知归属诚实填unknown。
不额外调用分类模型；不输出源码补丁或任务标准答案。
公共材料：
""" + canonical({k:v for k,v in material.items() if k!='sources'})


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
    if not isinstance(analysis,dict):return 'non_object_analysis'
    extra={k:analysis[k] for k in ['claims','consistency'] if k in analysis}
    analysis={k:v for k,v in analysis.items() if k not in extra}
    if extra:
        if set(extra)!={'claims','consistency'}:return 'incomplete_semantic_structure'
        if not isinstance(extra['claims'],list) or not isinstance(extra['consistency'],dict):return 'invalid_semantic_types'
        for claim in extra['claims']:
            if set(claim) not in [{'kind','statement','evidence'},{'kind','statement','evidence','record_owner','owner_expression'}] or claim['kind'] not in ['reported_defect','requirement','source_fact','preservation_inference']:return 'invalid_semantic_claim'
            if not valid_evidence(claim['evidence'],sources):return 'unbound_semantic_claim'
        if set(extra['consistency'])!={'conflicts','unknowns','checked_dimensions'}:return 'invalid_semantic_review'
        # Self-reported tensions are preserved evidence, not a policy verdict.
        # The mandatory source-bound semantic review decides actual core conflicts.
        # Unknowns can be scope limits. The source-bound semantic veto must
        # distinguish unresolved policy from honest non-exhaustiveness.
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
    entry = {**candidate, 'version': 'pilot-v2r4-1', 'primary_class': primary,
             'text_sha256': digest(candidate['text'])}
    entry['sha256'] = digest(canonical(entry))
    return entry


def route(analysis, sources, library, *, task=None, review=None):
    # Only data used below is accepted. No case/cluster/history/oracle arguments.
    def fallback(reason, checks=None):
        return {'condition': 'AUTO', 'reason': reason, 'selected': None,
                'checks': checks or [], 'primary_class': analysis.get('primary_class', 'unknown')}
    invalid = validate_analysis(analysis, sources)
    if invalid:return fallback(invalid)
    if task is None:return fallback('missing_task_semantic_inputs')
    issue=semantic_gate(task,sources,analysis,review)
    if issue:return fallback(issue)
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


from feedback_v2 import feedback


def reflection_prompt(payload):
    return '''只根据以下本批训练反馈反思一次，不能使用工具。生成一个可迁移经验候选，
不得读取或借用旧经验。材料含原始候选、原任务文档标准、两份实际修复/评分及公开交付。
参考实现/参考补丁不在输入。保留已经成功的关系，区分实际差异、退步与未知原因，
不要从断言名称臆造政策或根因。actual_successes才是该补丁已通过项，original_successes只是原始起点曾通过项；regressions是丢失的既有关系。all_checks包含checks/assertions原始实际值与期望值。公开交付中的模型自述未经验证，不能当评分事实。任何修好/保留/退步的叙述必须与实际关系核对；多处改动只能支持原因假设，不能宣称因果已经隔离证明。避免在经验正文复述哪次训练补丁成功，写成一般适用边界和验证动作。标准解释的执行Agent来源已记录。
经验必须包含适用前提、事件关系、验证动作、保留行为、不适用情况。
经验正文不得含案例ID、评分断言名、文件路径、程序专用字段/函数名或可复制补丁。
用一般时序机制和普通中文描述，不引用训练案例名字，不承诺未观察的效果。
适用性requires/excludes只用固定predicate key；至少一个requires；仅当有依据时设置
排除predicate。excludes只有被当前证据明确否定才可路由，未知会回退；不要把相邻
对象政策误用于维护对象。不要要求候选已经修好才适用。
最终直接输出CLI schema规定的顶层JSON对象，不使用report包装，不把JSON放进字符串：
{"text":"完整经验原文", "requires":["predicate key"], "excludes":[]}。
text最多3600字符。只生成一个候选，不另给修订版。requires/excludes必须与正文适用边界一致；无法核查的适用政策不能强行肯定。
固定predicate词典：''' + canonical(PREDICATES) + '\n本批训练材料：\n' + canonical(payload)


def semantic_gate(task, sources, analysis, review):
    """A source-bound veto record; never changes category, Contract or experience."""
    required={'contract_sha256','task_sha256','sources_sha256','reviewer','approved','conflicts','unknowns','evidence','findings'}
    if not isinstance(review,dict) or set(review)!=required:return 'missing_or_invalid_semantic_veto_record'
    if review['contract_sha256']!=digest(analysis['contract']) or review['task_sha256']!=digest(task) or review['sources_sha256']!=digest(canonical(sources)):return 'semantic_review_input_drift'
    if review['reviewer']!='execution_agent_visible_input_only':return 'invalid_semantic_review_provenance'
    if not review['approved'] or review['conflicts'] or review['unknowns']:return 'unresolved_semantic_conflict'
    if not valid_evidence(review['evidence'],sources):return 'unbound_semantic_review'
    return None

