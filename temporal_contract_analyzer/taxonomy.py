"""Canonical obligation labels; carriers, prompt templates and case IDs are separate."""
import json
from pathlib import Path

from .core import EvidenceError, canonical, sha

VERSION = 'temporal-obligation-taxonomy-7-v1'
CODES = ('R', 'O', 'B', 'L', 'I', 'F', 'A')


def definition():
    data = json.loads(Path(__file__).with_name('contract-taxonomy.json').read_text(encoding='utf-8'))
    if data['schema_version'] != VERSION or tuple(row['code'] for row in data['codebook']) != CODES:
        raise EvidenceError('Invalid canonical obligation taxonomy')
    return data


def fingerprint():
    return sha(canonical(definition()).encode())


def labels(value, allow_empty=True):
    if not isinstance(value, list) or any(code not in CODES for code in value) or len(value) != len(set(value)):
        raise EvidenceError('Use unique R/O/B/L/I/F/A obligation labels; legacy T1–T4 are not converted automatically')
    if not allow_empty and not value:
        raise EvidenceError('At least one evidence-supported obligation label is required')
    return [code for code in CODES if code in value]


def evidence_schema():
    return dict(type='array', minItems=1, maxItems=8, items=dict(type='object',
                properties=dict(file=dict(type='string', minLength=1),
                                line=dict(type='integer', minimum=1),
                                quote=dict(type='string', minLength=1, maxLength=160)),
                required=['file', 'line', 'quote'], additionalProperties=False))


def analysis_schema():
    """Output schema for source-only Auto Contract analysis; never executes it."""
    predicates = list(definition()['mechanism_predicates'])
    return dict(type='object', properties=dict(
        taxonomy_version=dict(type='string', enum=[VERSION]),
        contract=dict(type='string', minLength=1, maxLength=1800),
        obligation_labels=dict(type='array', maxItems=7, items=dict(type='object', properties=dict(
            code=dict(type='string', enum=list(CODES)),
            statement=dict(type='string', minLength=1, maxLength=600), evidence=evidence_schema()),
            required=['code', 'statement', 'evidence'], additionalProperties=False)),
        facts=dict(type='array', maxItems=len(predicates), items=dict(type='object', properties=dict(
            predicate=dict(type='string', enum=predicates),
            state=dict(type='string', enum=['known', 'unknown', 'contradicted']),
            evidence=dict(evidence_schema(), minItems=0)),
            required=['predicate', 'state', 'evidence'], additionalProperties=False)),
        unknowns=dict(type='array', items=dict(type='string'), maxItems=20)),
        required=['taxonomy_version', 'contract', 'obligation_labels', 'facts', 'unknowns'],
        additionalProperties=False)


def markdown():
    data = definition()
    lines = ['# 统一时序义务分类（七类）', '', '| 标签 | 名称 | 定义 |', '|---|---|---|']
    lines += ['| ' + row['code'] + ' | ' + row['name_zh'] + ' | ' + row['inclusion_rule'] + ' |'
              for row in data['codebook']]
    lines += ['', '允许多标签；机制与适用条件另记。未知不等于安全。',
              'T1–T4只保留为历史路由分组；五组提示模板和五条题库问题不是另一个当前分类。']
    return '\n'.join(lines) + '\n'
