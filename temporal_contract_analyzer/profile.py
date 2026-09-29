"""Researcher-side evidence cards; not a contract classifier or agent report.

Only candidate code enters the syntax scanner. Evaluator artifacts are separately
indexed for later human review. Outcomes, prior profiles and analysis prose are
not inputs. Source hashes prove binding, never semantic correctness.
"""
from pathlib import Path, PurePosixPath

from .core import CODE_EXT, EvidenceError, analyze_sources, canonical, sha


SCHEMA = 'temporal-contract-profile-evidence-1'
DIMENSIONS = [
    dict(id='TR', label='关系恢复', kind='axis', score_policy='confirmed-rubric-only'),
    dict(id='TI', label='时间身份', kind='axis', score_policy='confirmed-rubric-only'),
    dict(id='IB', label='失效边界', kind='axis', score_policy='confirmed-entities-only'),
    dict(id='OC', label='义务耦合', kind='axis', score_policy='evidence-only'),
    dict(id='CS', label='反事实调度', kind='axis', score_policy='evidence-only'),
    dict(id='OD', label='效果可观测距离', kind='axis', score_policy='evidence-only'),
    dict(id='baseline_protection', label='原有保护', kind='maintenance', score_policy='confirmed-category-only'),
    dict(id='maintenance_transfer', label='维护迁移', kind='maintenance', score_policy='confirmed-category-only'),
    dict(id='boundary_delta', label='边界变化', kind='maintenance', score_policy='confirmed-category-only'),
    dict(id='evidence_alignment', label='证据对应', kind='maintenance', score_policy='confirmed-category-only'),
]
# Relevance routes, not inferred values or necessary relationships. In particular
# a scheduling call is only a place to inspect when constructing a schedule pair.
RULE_DIMENSIONS = {
    'listen-before-connect': ['TR', 'TI', 'IB', 'OC', 'CS', 'baseline_protection', 'boundary_delta'],
    'connect-before-listen': ['TR', 'OC', 'CS', 'baseline_protection', 'boundary_delta'],
    'effect-after-await': ['TR', 'TI', 'IB', 'CS', 'OD', 'baseline_protection', 'maintenance_transfer'],
    'commit-after-yield': ['TR', 'OC', 'OD', 'baseline_protection', 'maintenance_transfer'],
    'cleanup-handle-after-call': ['TR', 'TI', 'IB', 'OC', 'CS', 'baseline_protection'],
    'continuation-and-listener-removal': ['TI', 'IB', 'CS', 'OD', 'baseline_protection', 'maintenance_transfer'],
    'early-return-from-async-iteration': ['TI', 'IB', 'baseline_protection', 'maintenance_transfer'],
    'cleanup-in-finally': ['TR', 'TI', 'IB', 'baseline_protection'],
    'asyncio-shield-call': ['TI', 'IB', 'OC', 'baseline_protection', 'maintenance_transfer'],
    'continuation-retry-scheduling': ['TR', 'TI', 'IB', 'CS', 'baseline_protection', 'boundary_delta'],
    'continuation-lifecycle-boundaries': ['TI', 'IB', 'CS', 'baseline_protection', 'maintenance_transfer'],
    'continuation-guard-state-review': ['TI', 'IB', 'OC', 'baseline_protection', 'maintenance_transfer'],
    'state-write-inline-notification': ['TR', 'OC', 'CS', 'boundary_delta', 'maintenance_transfer'],
    'callback-reentrant-transition': ['TR', 'TI', 'IB', 'CS', 'baseline_protection', 'boundary_delta'],
    'snapshot-output-lifetime-split': ['TR', 'TI', 'IB', 'OC', 'OD', 'baseline_protection', 'maintenance_transfer'],
}
LIMITATIONS = [
    '候选位置只表示语法线索，不证明义务、保护充分性、独立边界、因果调度或难度。',
    '规则到维度的映射只建议复核方向；不把命中数量转成等级或总分。',
    '未命中、未解析和未复核均不等于没有保护或低难度；所有初始建议保持 null。',
    '按文件关联来自已有证据路径声明，不是自动推断该观察满足这条义务。',
    'OC、CS、OD 需要人工确认的行为见证；静态源码与 artifact 文件名不能替代见证。',
    '评估者材料只建立独立索引，不能抬高候选显式性，也不能导出为 Agent 输入。',
]


def _digest(value):
    return sha(canonical(value).encode('utf-8'))


def _files(packet):
    if not isinstance(packet, dict) or not isinstance(packet.get('files'), list):
        raise EvidenceError('profile 输入必须是包含 files 列表的复核材料对象')
    result = []
    seen = set()
    for f in packet.get('files', []):
        if not isinstance(f, dict):
            raise EvidenceError('材料文件必须是对象')
        if f.get('role') not in {'candidate', 'evaluator'}:
            continue
        path = f.get('path')
        if not isinstance(path, str):
            raise EvidenceError('材料缺少源码路径')
        p = PurePosixPath(path)
        if p.name == 'REVIEW-GUIDE.md':
            continue  # Post-consensus interpretation is not primary evidence.
        if p.is_absolute() or '..' in p.parts or str(p) != path or not path:
            raise EvidenceError('不安全的材料路径: ' + path)
        if path in seen:
            raise EvidenceError('重复材料路径: ' + path)
        seen.add(path)
        if not isinstance(f.get('text'), str) or sha(f['text'].encode('utf-8')) != f.get('sha256'):
            raise EvidenceError('材料字节与摘要不一致: ' + path)
        result.append(f)
    return sorted(result, key=lambda f: f['path'])


def packet_binding(packet):
    """Small portable binding recipe shared with the offline reviewer."""
    files = _files(packet)
    if not isinstance(packet.get('obligations'), list):
        raise EvidenceError('复核材料必须包含 obligations 列表')
    obligations = []
    seen = set()
    for o in packet.get('obligations', []):
        if not isinstance(o, dict):
            raise EvidenceError('义务必须是对象')
        oid = o.get('id')
        if not isinstance(oid, str) or not oid or oid in seen:
            raise EvidenceError('义务 ID 缺失或重复')
        seen.add(oid)
        paths = o.get('acceptable_evidence_paths', [])
        if not isinstance(paths, list) or any(not isinstance(p, str) for p in paths):
            raise EvidenceError('acceptable_evidence_paths 必须是路径列表')
        if not isinstance(o.get('statement', ''), str):
            raise EvidenceError('义务说明必须是文本')
        obligations.append(dict(id=oid, statement=o.get('statement', ''),
                                acceptable_evidence_paths=sorted(set(paths))))
    return dict(id=packet.get('id'), condition=packet.get('condition'),
                manifest_sha256=packet.get('manifest_sha256'), base_sha256=packet.get('base_sha256'),
                files=[dict(path=f['path'], role=f['role'], sha256=f['sha256']) for f in files],
                obligations=sorted(obligations, key=lambda o: o['id']))


def packet_sha256(packet):
    return _digest(packet_binding(packet))


def _ref(file, event=None):
    lines = file['text'].splitlines()
    return dict(path=file['path'], sha256=file['sha256'],
                start=dict(line=event['line'] if event else 1, column=event['column'] if event else 0),
                end=dict(line=event['end_line'] if event else max(1, len(lines)),
                         column=event['end_column'] if event else (len(lines[-1]) if lines else 0)))


def _index(file, prefix):
    return dict(id=prefix + '-' + _digest([file['path'], file['sha256']])[:20],
                path=file['path'], sha256=file['sha256'], role=file['role'],
                refs=[_ref(file)], interpretation='unreviewed')


def build_profile_evidence(packet, report=None):
    """Build immutable review assistance without reading results or profiles."""
    binding = packet_binding(packet)
    files = _files(packet)
    by_path = {f['path']: f for f in files}
    sources = {f['path']: f['text'] for f in files
               if f['role'] == 'candidate' and PurePosixPath(f['path']).suffix.lower() in CODE_EXT}
    expected_inputs = [dict(path=p, sha256=sha(t.encode('utf-8'))) for p, t in sorted(sources.items())]
    report = analyze_sources(sources) if report is None else report
    if (not isinstance(report, dict) or report.get('schema_version') != 'temporal-contract-analysis-1' or report.get('inputs') != expected_inputs
            or report.get('input_sha256') != _digest(expected_inputs)):
        raise EvidenceError('扫描报告与候选源码不一致；禁止混入评估者或其他版本材料')
    events = {e['id']: e for f in report['files'] for e in f['events']}
    observations = []
    for finding in report['findings']:
        refs = []
        for eid in finding['evidence']:
            event = events.get(eid)
            if event is None or event.get('path') not in sources:
                raise EvidenceError('扫描证据引用不属于候选源码')
            refs.append(_ref(by_path[event['path']], event))
        refs = sorted(refs, key=lambda r: (r['path'], r['start']['line'], r['start']['column'],
                                          r['end']['line'], r['end']['column']))
        dimensions = RULE_DIMENSIONS.get(finding['rule'], [])
        observation = dict(rule=finding['rule'], refs=refs,
                           axes=[x for x in dimensions if len(x) == 2],
                           maintenance_fields=[x for x in dimensions if len(x) != 2],
                           message=finding['message'], qualification=finding.get('condition', ''),
                           review_question=finding.get('review_question', ''),
                           classification='potential_evidence_not_dimension_value')
        observation['id'] = 'observation-' + _digest(observation)[:20]
        observations.append(observation)
    observations = sorted({o['id']: o for o in observations}.values(), key=lambda o: o['id'])
    cards = []
    candidate_paths = set(sources)
    for obligation in binding['obligations']:
        nominated = obligation['acceptable_evidence_paths']
        matched = []
        for path in nominated:
            matches = [p for p in candidate_paths if p == path or p.endswith('/' + path)]
            if len(matches) == 1:
                matched.append(matches[0])
        matched = sorted(set(matched))
        selected = [o for o in observations if not nominated or any(r['path'] in matched for r in o['refs'])]
        association = 'explicit_source_paths' if matched else 'unresolved_source_paths' if nominated else 'workspace_unassigned'
        dimensions = {}
        for dimension in DIMENSIONS:
            ids = [o['id'] for o in selected if dimension['id'] in o['axes'] + o['maintenance_fields']]
            dimensions[dimension['id']] = dict(suggestion=None, status='unreviewed',
                                               observation_ids=ids, coverage='candidate_clues' if ids else 'unknown')
        cards.append(dict(obligation_id=obligation['id'], statement=obligation['statement'],
                          association=association, association_paths=matched,
                          unresolved_paths=[p for p in nominated if not any(x == p or x.endswith('/' + p) for x in matched)],
                          candidate_observation_ids=[o['id'] for o in selected], dimensions=dimensions))
    evidence = dict(schema_version=SCHEMA, case_id=packet.get('id'),
                    context=dict(condition=packet.get('condition'), unit='frozen-review-prompt',
                                 condition_status='declared' if packet.get('condition') else 'not_declared'),
                    visibility='after-both-recovery-locks', agent_input_eligible=False,
                    bindings=dict(packet_sha256=_digest(binding), manifest_sha256=packet.get('manifest_sha256'),
                                  base_sha256=packet.get('base_sha256'), input_sha256=report['input_sha256'],
                                  tool_sha256=report['tool_sha256'], tool_version=report['tool_version'],
                                  generator_sha256=sha(Path(__file__).read_bytes()), report_sha256=_digest(report)),
                    dimensions=[dict(d) for d in DIMENSIONS], observations=observations, cards=cards,
                    candidate_text_index=[_index(f, 'candidate-text') for f in files
                                          if f['role'] == 'candidate' and f['path'] not in sources],
                    evaluator_artifact_index=[_index(f, 'evaluator-artifact') for f in files if f['role'] == 'evaluator'],
                    coverage=dict(status=report['status'], files=report['summary']['files'],
                                  parsed_files=report['summary']['parsed_files'], observations=len(observations),
                                  unparsed_files=[dict(path=f['path'], status=f['status']) for f in report['files'] if f['status'] != 'parsed'],
                                  zero_hits=not observations, semantic_coverage='unknown'),
                    limitations=list(LIMITATIONS))
    evidence['evidence_hash'] = _digest(evidence)
    return evidence


def verify_profile_evidence(packet, evidence):
    """Check frozen binding/integrity, without relabeling or rerunning analysis."""
    if not isinstance(evidence, dict) or evidence.get('schema_version') != SCHEMA:
        raise EvidenceError('未知 profile 证据 schema')
    if evidence.get('evidence_hash') != _digest({k: v for k, v in evidence.items() if k != 'evidence_hash'}):
        raise EvidenceError('profile 证据摘要不一致')
    if evidence.get('bindings', {}).get('packet_sha256') != packet_sha256(packet):
        raise EvidenceError('源码、义务或条件已变化，旧 profile 证据需要重新复核')
    return dict(verified=True, evidence_hash=evidence['evidence_hash'], semantic_validity='not_checked')
