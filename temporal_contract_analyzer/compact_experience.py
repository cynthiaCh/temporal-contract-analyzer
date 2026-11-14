"""Single-file experience content and inline acceptance, without audit sidecars."""
from html import escape
import json
from pathlib import Path

from . import experience_memory as memory, taxonomy
from .core import EvidenceError, canonical, sha

VERSION = 'experience-library-single-file-v1'
SECTIONS = [('applicability', '适用条件'), ('event_relation', '建议'),
            ('preservation', '需要保留'), ('exclusion', '不适用情况'),
            ('verification', '检查方法')]


def load(path):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    memory.object_fields(value, {'schema_version', 'review', 'experiences'}, 'experience file')
    if value['schema_version'] != VERSION:
        raise EvidenceError('Unknown single-file experience format')
    memory.object_fields(value['review'], {'reviewer', 'decision', 'at'}, 'inline review')
    if not memory.text(value['review']['reviewer']) or not memory.text(value['review']['at']) \
            or value['review']['decision'] not in ('accept', 'revise', 'reject'):
        raise EvidenceError('Invalid inline review')
    if not isinstance(value['experiences'], list) or not value['experiences']:
        raise EvidenceError('Experience list must not be empty')
    ids = set()
    for item in value['experiences']:
        memory.object_fields(item, {'id', 'title', 'labels', 'requires', 'excludes'} |
                             {key for key, _ in SECTIONS}, 'experience')
        if not memory.text(item['id']) or item['id'] in ids or not memory.text(item['title']) \
                or any(not memory.text(item[key]) for key, _ in SECTIONS):
            raise EvidenceError('Invalid or duplicate experience')
        ids.add(item['id'])
    return value


def materialize(path):
    """Adapt the single source of truth to existing retrieval objects in memory only."""
    value = load(path)
    bundles, decisions, blobs = [], [], {}
    for index, item in enumerate(value['experiences'], 1):
        raw = canonical(item).encode('utf-8')
        code = sha(raw)
        blobs[code] = raw
        bundle = memory.seal(dict(schema_version=memory.BUNDLE_VERSION_V2,
            id=item['id'], version='single-file-v1', parent_sha256=None,
            taxonomy_version=taxonomy.VERSION, labels=item['labels'],
            requires=item['requires'], excludes=item['excludes'],
            rules=[dict(id=f'R{i:02d}', category=key, body=item[key])
                   for i, (key, _) in enumerate(SECTIONS, 1)],
            review=dict(status='candidate', kind='ai_assisted', source_sha256=code,
                        limitations=['Content acceptance does not establish cross-task effectiveness.']),
            audit=dict(sources=[dict(path=str(path), sha256=code)],
                       rule_links=[], notes=[], outcome_refs=[])))
        memory.validate(bundle, blobs.__getitem__)
        row = dict(value['review'], reason='', scope='research', actor='named_operator',
                   schema_version='experience-expert-decision-v1',
                   candidate_sha256=bundle['sha256'], report_sha256=None, sequence=index,
                   rules=[dict(rule_id=r['id'], supported=value['review']['decision']=='accept', reason='')
                          for r in bundle['rules']])
        row['sha256'] = memory.digest(canonical(row))
        bundles.append(bundle)
        decisions.append(row)
    return bundles, decisions, blobs


def page(path):
    value = load(path)
    review = value['review']
    status = {'accept': '已接受', 'revise': '需修改', 'reject': '已拒绝'}[review['decision']]
    cards = []
    for item in value['experiences']:
        sections = ''.join(f'<dt>{label}</dt><dd>{escape(item[key])}</dd>'
                           for key, label in SECTIONS)
        cards.append(f'<article><h2>{escape(item["title"])}</h2><dl>{sections}</dl></article>')
    html = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>经验库</title><style>body{max-width:900px;margin:32px auto;padding:0 20px;'
            'font:16px/1.7 system-ui;color:#243047}article{border-top:1px solid #ccd4df;'
            'padding:16px 0}dt{font-weight:bold}dd{margin:0 0 12px}code{overflow-wrap:anywhere}</style>'
            f'<h1>经验库 · {len(cards)} 条</h1><p>{escape(review["reviewer"])} · {status}</p>'
            f'<p>经验均保存在这个文件中，可直接编辑：<code>{escape(str(path))}</code></p>'
            + ''.join(cards) + '</html>')
    return html.encode('utf-8')
